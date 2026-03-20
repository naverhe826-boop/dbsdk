"""极端场景测试：安全性、边界、并发、性能、配置异常"""
import os
import threading
import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_builder import DataBuilder, BuilderConfig, CombinationSpec, CombinationMode, Constraint
from data_builder.strategies import SequenceStrategy


class TestSecurityEvalInjection:
    """eval() 注入攻击安全性测试"""

    def test_predicate_injection_attempt_code_execution(self):
        """测试恶意代码注入尝试应被安全处理"""
        # 尝试注入恶意的 lambda 代码 - 通过 BuilderConfig 解析
        malicious_config = {
            "combinations": [
                {
                    "mode": "pairwise",
                    "fields": ["status", "type"],
                    "constraints": [
                        {
                            "description": "malicious",
                            "predicate": "__import__('os').system('echo pwned')"
                        }
                    ]
                }
            ]
        }

        # 使用 BuilderConfig 解析
        config = BuilderConfig.from_dict(malicious_config)
        # 恶意代码应该被过滤掉（predicate 为 None）
        assert len(config.combinations) == 1
        assert len(config.combinations[0].constraints) == 0

    def test_predicate_injection_attempt_file_read(self):
        """测试 eval() 安全漏洞：文件读取代码应被阻止

        这是一个 P0 安全漏洞测试！
        修复后：恶意代码执行被阻止，约束应为 0 个。
        """
        malicious_config = {
            "combinations": [
                {
                    "mode": "pairwise",
                    "fields": ["status"],
                    "constraints": [
                        {
                            "description": "read file",
                            "predicate": "open('/etc/passwd').read()"
                        }
                    ]
                }
            ]
        }

        config = BuilderConfig.from_dict(malicious_config)
        assert len(config.combinations) == 1
        # 修复后：恶意代码被阻止，约束应该为 0 个
        assert len(config.combinations[0].constraints) == 0

    def test_predicate_injection_attempt_import(self):
        """测试尝试导入模块应被安全处理"""
        malicious_config = {
            "combinations": [
                {
                    "mode": "pairwise",
                    "fields": ["status"],
                    "constraints": [
                        {
                            "description": "import",
                            "predicate": "import sys"
                        }
                    ]
                }
            ]
        }

        config = BuilderConfig.from_dict(malicious_config)
        assert len(config.combinations) == 1
        assert len(config.combinations[0].constraints) == 0

    def test_predicate_valid_lambda_accepted(self):
        """测试合法的 lambda 应该正常工作"""
        config = {
            "combinations": [
                {
                    "mode": "pairwise",
                    "fields": ["status", "type"],
                    "constraints": [
                        {
                            "description": "valid constraint",
                            "predicate": "lambda row: row.get('status') == 'active'"
                        }
                    ]
                }
            ]
        }

        result = BuilderConfig.from_dict(config)
        assert len(result.combinations) == 1
        assert len(result.combinations[0].constraints) == 1


class TestCycleReference:
    """循环引用测试"""

    def test_self_reference_field(self):
        """测试自引用字段 (schema 中引用自身)"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "parent": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }

        # 测试自引用不应该导致无限循环
        builder = DataBuilder(schema, config=BuilderConfig(count=3))
        result = builder.build()
        assert len(result) == 3
        # 验证 parent 字段也被生成
        assert all("parent" in row for row in result)

    def test_mutual_reference_between_fields(self):
        """测试字段间相互引用 (通过 ref 策略)"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "created_by": {"type": "integer"},
                "updated_by": {"type": "integer"}
            }
        }

        from data_builder import FieldPolicy, seq, ref

        builder = DataBuilder(schema, config=BuilderConfig(
            policies=[
                FieldPolicy("id", seq(start=1)),
                FieldPolicy("created_by", ref("id")),
                FieldPolicy("updated_by", ref("id"))
            ]
        ))

        result = builder.build(count=3)
        assert len(result) == 3

    def test_deep_nested_cycle_reference(self):
        """测试深度嵌套的循环引用"""
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=2))
        result = builder.build()
        assert len(result) == 2


class TestPerformanceLargeScale:
    """大规模数据生成性能测试"""

    def test_large_count_generation(self):
        """测试大规模数据生成 (1000 条)"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "value": {"type": "number"}
            }
        }

        from data_builder import FieldPolicy, seq, faker, range_float

        builder = DataBuilder(schema, config=BuilderConfig(
            policies=[
                FieldPolicy("id", seq(start=1)),
                FieldPolicy("name", faker("name")),
                FieldPolicy("value", range_float(0, 100))
            ]
        ))

        start = time.time()
        result = builder.build(count=1000)
        elapsed = time.time() - start

        assert len(result) == 1000
        assert elapsed < 5.0  # 应该在 5 秒内完成

    def test_deep_nested_structure_performance(self):
        """测试深度嵌套结构的性能"""
        # 创建 5 层嵌套结构
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "level3": {
                                    "type": "object",
                                    "properties": {
                                        "level4": {
                                            "type": "object",
                                            "properties": {
                                                "value": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=100))
        start = time.time()
        result = builder.build()
        elapsed = time.time() - start

        assert len(result) == 100
        assert elapsed < 3.0


class TestBoundaryConditions:
    """边界条件测试"""

    def test_multipleof_boundary_minimum_not_multiple(self):
        """测试 multipleOf 边界: minimum 不是 multipleOf 的倍数"""
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "multipleOf": 10, "minimum": 3, "maximum": 50}
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=10))
        result = builder.build()

        # 所有值应该是 10 的倍数
        for row in result:
            assert row["value"] % 10 == 0
            assert 3 <= row["value"] <= 50

    def test_multipleof_boundary_float_precision(self):
        """测试浮点数 multipleOf 精度问题"""
        schema = {
            "type": "object",
            "properties": {
                "price": {"type": "number", "multipleOf": 0.01, "minimum": 0, "maximum": 1}
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=50))
        result = builder.build()

        # 浮点数精度问题可能导致 0.01 * 100 = 1.0000000001
        for row in result:
            # 检查是否是 0.01 的倍数
            val = row["price"]
            assert abs(val - round(val / 0.01) * 0.01) < 0.0001

    def test_allof_type_conflict(self):
        """测试 allOf 类型冲突场景"""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "allOf": [
                        {"type": "object", "properties": {"a": {"type": "string"}}},
                        {"type": "object", "properties": {"b": {"type": "integer"}}}
                    ]
                }
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=5))
        result = builder.build()

        # 应该能正确合并 allOf 中的类型
        assert len(result) == 5

    def test_minimum_maximum_equal(self):
        """测试 minimum == maximum 边界"""
        schema = {
            "type": "object",
            "properties": {
                "fixed": {"type": "integer", "minimum": 100, "maximum": 100}
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=5))
        result = builder.build()

        # 所有值应该都是 100
        assert all(row["fixed"] == 100 for row in result)

    def test_minimum_maximum_single_value_range(self):
        """测试只有单个可能值的范围"""
        schema = {
            "type": "object",
            "properties": {
                "narrow": {"type": "integer", "minimum": 5, "maximum": 6}
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=20))
        result = builder.build()

        # 值应该是 5 或 6
        assert all(5 <= row["narrow"] <= 6 for row in result)


class TestConcurrency:
    """并发安全测试"""

    def test_sequence_strategy_thread_safety(self):
        """测试 SequenceStrategy 在多线程环境下的线程安全性"""
        results = []
        errors = []

        def generate_sequence(start, count):
            try:
                from data_builder.strategies import SequenceStrategy
                from data_builder import StrategyContext

                s = SequenceStrategy(start=start, step=1)
                ctx = StrategyContext(field_path="id", field_schema={}, root_data={})
                values = [s.generate(ctx) for _ in range(count)]
                results.extend(values)
            except Exception as e:
                errors.append(e)

        # 多线程并发生成
        threads = []
        for i in range(10):
            t = threading.Thread(target=generate_sequence, args=(i * 100, 100))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 不应该有错误
        assert len(errors) == 0
        # 应该生成 1000 个值
        assert len(results) == 1000

    def test_concurrent_data_builder_builds(self):
        """测试 DataBuilder 在多线程环境下并发构建"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        }

        all_results = []
        errors = []

        def build_data(count):
            try:
                builder = DataBuilder(schema, config=BuilderConfig(count=count))
                result = builder.build()
                all_results.extend(result)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(build_data, 50) for _ in range(10)]
            for f in as_completed(futures):
                pass

        assert len(errors) == 0
        assert len(all_results) == 500

    def test_concurrent_different_schemas(self):
        """测试不同 schema 的并发构建"""
        schema1 = {"type": "object", "properties": {"id": {"type": "integer"}}}
        schema2 = {"type": "object", "properties": {"name": {"type": "string"}}}

        results = []

        def build(schema, count):
            builder = DataBuilder(schema, config=BuilderConfig(count=count))
            return builder.build()

        with ThreadPoolExecutor(max_workers=4) as executor:
            f1 = executor.submit(build, schema1, 100)
            f2 = executor.submit(build, schema2, 100)
            results.extend(f1.result())
            results.extend(f2.result())

        assert len(results) == 200


class TestConfigurationErrors:
    """配置错误测试"""

    def test_missing_required_config_field(self):
        """测试缺少必需的配置字段"""
        # Policy 缺少 path
        config_dict = {
            "policies": [
                {
                    "strategy": {
                        "type": "sequence",
                        "start": 1
                    }
                }
            ]
        }

        with pytest.raises(Exception):
            BuilderConfig.from_dict(config_dict)

    def test_invalid_strategy_type(self):
        """测试无效的策略类型"""
        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "invalid_strategy_type",
                        "value": 100
                    }
                }
            ]
        }

        with pytest.raises(Exception):
            BuilderConfig.from_dict(config_dict)

    def test_env_var_missing_without_default(self):
        """测试缺少环境变量且没有默认值"""
        # 确保环境变量不存在
        os.environ.pop("NONEXISTENT_VAR_12345", None)

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": "${NONEXISTENT_VAR_12345}"
                    }
                }
            ]
        }

        # 应该使用原始字符串还是报错？
        # 当前实现会保留原始字符串
        config = BuilderConfig.from_dict(config_dict)
        # 验证策略被创建
        assert len(config.policies) > 0

    def test_invalid_combination_mode(self):
        """测试无效的组合模式"""
        config_dict = {
            "combinations": [
                {
                    "mode": "invalid_mode",
                    "fields": ["a", "b"]
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        # 无效模式应该回退到 RANDOM
        assert config.combinations[0].mode == CombinationMode.RANDOM

    def test_empty_schema(self):
        """测试空 schema"""
        schema = {}

        builder = DataBuilder(schema)
        result = builder.build(count=3)
        assert len(result) == 3
        # 空 schema 应该生成空对象
        assert all(isinstance(row, dict) and len(row) == 0 for row in result)

    def test_invalid_json_schema_type(self):
        """测试无效的 JSON Schema type"""
        schema = {
            "type": "object",
            "properties": {
                "invalid": {"type": "not_a_valid_type"}
            }
        }

        builder = DataBuilder(schema, config=BuilderConfig(count=1))
        result = builder.build()
        # 应该仍然能生成数据，使用默认值
        assert len(result) == 1

    def test_policy_path_invalid_format(self):
        """测试无效的 policy path 格式"""
        from data_builder import FieldPolicy
        from data_builder.strategies import FixedStrategy

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }

        # 使用无效的路径（包含非法字符）
        builder = DataBuilder(schema, config=BuilderConfig(
            policies=[
                FieldPolicy("name/invalid", FixedStrategy("test"))
            ]
        ))

        # 应该能构建，但在生成时可能会出问题
        result = builder.build(count=1)
        assert len(result) == 1
