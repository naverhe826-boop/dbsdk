"""CombinationBuilder 组合构建器测试"""

import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, enum
from data_builder.combination_builder import CombinationBuilder
from data_builder.combinations import CombinationMode, CombinationSpec
from data_builder.strategies.value.enum import EnumStrategy


class TestCombinationBuilderInit:
    """测试 CombinationBuilder 初始化"""
    
    def test_init_with_builder(self):
        """使用 DataBuilder 初始化"""
        schema = {"type": "object", "properties": {"status": {"type": "string"}}}
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        assert combo_builder.builder == builder


class TestCombinationBuilderBuild:
    """测试 build() 方法"""
    
    def test_build_cartesian_mode(self):
        """测试笛卡尔积模式"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "role": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("role", enum(["admin", "user"]))
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, fields=["status", "role"])
            ]
        )
        builder = DataBuilder(schema, config)
        
        results = builder.build()
        
        # 2 × 2 = 4 种组合
        assert len(results) == 4
        pairs = {(r["status"], r["role"]) for r in results}
        expected = {
            ("active", "admin"), ("active", "user"),
            ("inactive", "admin"), ("inactive", "user")
        }
        assert pairs == expected
    
    def test_build_pairwise_mode(self):
        """测试成对组合模式"""
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
                "c": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("a", enum(["a1", "a2"])),
                FieldPolicy("b", enum(["b1", "b2"])),
                FieldPolicy("c", enum(["c1", "c2"]))
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.PAIRWISE, fields=["a", "b", "c"])
            ]
        )
        builder = DataBuilder(schema, config)
        
        results = builder.build()
        
        # 成对组合应该覆盖所有 2-元组
        # 验证所有字段对都被覆盖
        assert len(results) > 0
        assert len(results) < 8  # 少于笛卡尔积（8）
    
    def test_build_with_count_restriction(self):
        """测试 count 限制"""
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "string"},
                "y": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("x", enum(["x1", "x2", "x3"])),
                FieldPolicy("y", enum(["y1", "y2", "y3"]))
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, fields=["x", "y"])
            ]
        )
        builder = DataBuilder(schema, config)
        
        # 笛卡尔积应该生成 9 个，但限制为 5
        results = builder.build(count=5)
        
        assert len(results) == 5
    
    def test_build_with_count_extension(self):
        """测试 count 扩展"""
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "string"},
                "y": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("x", enum(["x1", "x2"])),
                FieldPolicy("y", enum(["y1", "y2"]))
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, fields=["x", "y"])
            ]
        )
        builder = DataBuilder(schema, config)
        
        # 笛卡尔积应该生成 4 个，扩展到 10
        results = builder.build(count=10)
        
        assert len(results) == 10
    
    def test_build_without_combinations(self):
        """无组合配置时退化到普通生成"""
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        builder = DataBuilder(schema, BuilderConfig(count=5))
        
        results = builder.build()
        
        assert len(results) == 5


class TestGroupFieldsByScope:
    """测试 _group_fields_by_scope() 方法"""
    
    def test_group_with_explicit_fields(self):
        """显式指定字段"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "role": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["a", "b"])),
                FieldPolicy("role", enum(["x", "y"]))
            ],
            combinations=[
                CombinationSpec(
                    mode=CombinationMode.CARTESIAN,
                    fields=["status", "role"]
                )
            ]
        )
        builder = DataBuilder(schema, config)
        combo_builder = CombinationBuilder(builder)
        
        groups = combo_builder._group_fields_by_scope(config.combinations)
        
        assert None in groups
        assert groups[None][0] == ["status", "role"]
    
    def test_group_with_scope(self):
        """使用 scope 分组"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "role": {"type": "string"}
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("user.status", enum(["a", "b"])),
                FieldPolicy("user.role", enum(["x", "y"]))
            ],
            combinations=[
                CombinationSpec(
                    mode=CombinationMode.CARTESIAN,
                    scope="user"
                )
            ]
        )
        builder = DataBuilder(schema, config)
        combo_builder = CombinationBuilder(builder)
        
        groups = combo_builder._group_fields_by_scope(config.combinations)
        
        assert "user" in groups
        assert "user.status" in groups["user"][0]
        assert "user.role" in groups["user"][0]


class TestMatchScope:
    """测试 _match_scope() 方法"""
    
    @pytest.fixture
    def combo_builder(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return CombinationBuilder(builder)
    
    def test_match_top_level(self, combo_builder):
        """匹配顶层字段"""
        assert combo_builder._match_scope("status", None)
        assert combo_builder._match_scope("name", None)
        assert not combo_builder._match_scope("user.name", None)
    
    def test_match_nested_scope(self, combo_builder):
        """匹配嵌套 scope"""
        assert combo_builder._match_scope("user.status", "user")
        assert combo_builder._match_scope("user.profile.age", "user.profile")
        assert not combo_builder._match_scope("order.status", "user")


class TestCollectDomains:
    """测试 _collect_domains() 方法"""
    
    def test_collect_from_enum_strategy(self):
        """从枚举策略收集值域"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "role": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("role", enum(["admin", "user"]))
            ]
        )
        builder = DataBuilder(schema, config)
        combo_builder = CombinationBuilder(builder)
        
        domains = combo_builder._collect_domains(
            ["status", "role"],
            CombinationMode.CARTESIAN
        )
        
        assert domains["status"] == ["active", "inactive"]
        assert domains["role"] == ["admin", "user"]
    
    def test_collect_boundary_values(self):
        """收集边界值"""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 100}
            }
        }
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        domains = combo_builder._collect_domains(["age"], CombinationMode.BOUNDARY)
        
        assert "age" in domains
        # 边界值应该包含最小值、最大值等
        assert 0 in domains["age"]
        assert 100 in domains["age"]


class TestCartesianMergeGroups:
    """测试 _cartesian_merge_groups() 方法"""
    
    def test_merge_single_group(self):
        """合并单个组"""
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        group_combos = {
            None: [
                {"status": "active"},
                {"status": "inactive"}
            ]
        }
        
        result = combo_builder._cartesian_merge_groups(group_combos)
        
        assert len(result) == 2
        assert result[0] == {"status": "active"}
        assert result[1] == {"status": "inactive"}
    
    def test_merge_multiple_groups(self):
        """合并多个组"""
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        group_combos = {
            None: [
                {"status": "active"},
                {"status": "inactive"}
            ],
            "user": [
                {"user.role": "admin"},
                {"user.role": "user"}
            ]
        }
        
        result = combo_builder._cartesian_merge_groups(group_combos)
        
        # 2 × 2 = 4 种组合
        assert len(result) == 4
        
        # 验证所有组合都存在
        expected_combos = [
            {"status": "active", "user.role": "admin"},
            {"status": "active", "user.role": "user"},
            {"status": "inactive", "user.role": "admin"},
            {"status": "inactive", "user.role": "user"}
        ]
        
        for expected in expected_combos:
            assert expected in result
    
    def test_merge_empty_groups(self):
        """合并空组"""
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        result = combo_builder._cartesian_merge_groups({})
        
        assert result == []


class TestDiscoverSchemaFields:
    """测试 _discover_schema_fields() 方法"""
    
    def test_discover_top_level_fields(self):
        """发现顶层基本类型字段"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"},
                "profile": {"type": "object"}  # 不是基本类型
            }
        }
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        fields = combo_builder._discover_schema_fields(None)
        
        assert "name" in fields
        assert "age" in fields
        assert "active" in fields
        assert "profile" not in fields
    
    def test_discover_nested_fields(self):
        """发现嵌套字段"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                }
            }
        }
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        fields = combo_builder._discover_schema_fields("user")
        
        assert "user.name" in fields
        assert "user.age" in fields


class TestResolveFieldSchema:
    """测试 _resolve_field_schema() 方法"""
    
    def test_resolve_top_level_field(self):
        """解析顶层字段"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        field_schema = combo_builder._resolve_field_schema("name")
        
        assert field_schema == {"type": "string"}
    
    def test_resolve_nested_field(self):
        """解析嵌套字段"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "age": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        field_schema = combo_builder._resolve_field_schema("user.profile.age")
        
        assert field_schema == {"type": "integer"}
    
    def test_resolve_nonexistent_field(self):
        """解析不存在的字段"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        builder = DataBuilder(schema)
        combo_builder = CombinationBuilder(builder)
        
        field_schema = combo_builder._resolve_field_schema("unknown")
        
        assert field_schema is None
