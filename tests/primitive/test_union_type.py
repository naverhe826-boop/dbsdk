"""
联合类型（union type）和 nullable 关键字的测试用例

测试场景：
1. union_type_priority 配置 - 类型优先级选择
2. nullable 关键字处理 - 布尔值和数组形式
3. 联合类型与 null 概率的协同工作
"""

import pytest
from data_builder import DataBuilder, BuilderConfig


class TestUnionTypePriority:
    """测试联合类型优先级配置"""
    
    def test_union_type_priority_string_first(self):
        """测试优先选择 string 类型"""
        schema = {
            "type": ["string", "integer", "number"],
            "minLength": 5
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(union_type_priority=["string", "integer", "number"])
        )
        
        # 生成 10 条数据，应该全部是 string 类型
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)
            assert len(result) >= 5
    
    def test_union_type_priority_integer_first(self):
        """测试优先选择 integer 类型"""
        schema = {
            "type": ["string", "integer", "number"],
            "minimum": 10,
            "maximum": 20
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(union_type_priority=["integer", "string"])
        )
        
        # 生成 10 条数据，应该全部是 integer 类型
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, int)
            assert 10 <= result <= 20
    
    def test_union_type_priority_with_null_probability(self):
        """测试联合类型优先级与 null 概率的协同"""
        schema = {
            "type": ["string", "null"]
        }
        
        # null_probability 为 0 时，不应生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string"],
                null_probability=0.0
            )
        )
        
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)
        
        # null_probability 为 1 时，应该总是生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string"],
                null_probability=1.0
            )
        )
        
        for _ in range(10):
            result = builder.build()
            assert result is None
    
    def test_union_type_priority_fallback_to_random(self):
        """测试优先级不匹配时回退到随机选择"""
        schema = {
            "type": ["boolean", "number"]
        }
        
        # 优先级中包含的类型都不在 schema 的 type 列表中
        builder = DataBuilder(
            schema,
            config=BuilderConfig(union_type_priority=["string", "integer"])
        )
        
        # 生成多条数据，应该回退到随机选择 boolean 或 number
        types_seen = set()
        for _ in range(20):
            result = builder.build()
            assert isinstance(result, (bool, float))
            types_seen.add(type(result))
        
        # 应该至少看到两种类型之一
        assert len(types_seen) > 0
    
    def test_union_type_with_null_in_priority(self):
        """测试优先级列表中不包含 null 时的处理"""
        schema = {
            "type": ["string", "null"]
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string"],
                null_probability=0.0
            )
        )
        
        # 即使 union_type_priority 中没有 null，也不应生成 null（因为 null_probability=0）
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)


class TestNullableKeyword:
    """测试 nullable 关键字处理"""
    
    def test_nullable_boolean_true(self):
        """测试 nullable: true（布尔值形式）"""
        schema = {
            "type": "string",
            "nullable": True,
            "minLength": 3
        }
        
        # null_probability 为 1 时，应该总是生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        for _ in range(10):
            result = builder.build()
            assert result is None
        
        # null_probability 为 0 时，应该不生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=0.0)
        )
        
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)
            assert len(result) >= 3
    
    def test_nullable_boolean_false(self):
        """测试 nullable: false"""
        schema = {
            "type": "string",
            "nullable": False,
            "minLength": 3
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        # 即使 null_probability 为 1，nullable: false 也不应生成 null
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)
            assert len(result) >= 3
    
    def test_nullable_array_form(self):
        """测试 nullable: ["null", "string"]（数组形式，Draft 4-6）"""
        schema = {
            "type": "string",
            "nullable": ["null", "string"]
        }
        
        # null_probability 为 1 时，应该生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        for _ in range(10):
            result = builder.build()
            assert result is None
    
    def test_nullable_array_without_null(self):
        """测试 nullable: ["string", "integer"]（数组形式，不包含 null）"""
        schema = {
            "type": "string"
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        # 没有 nullable 关键字，即使 null_probability 为 1 也不应生成 null
        # 因为单一 type: "string" 不包含 null
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)
    
    def test_nullable_not_present(self):
        """测试 schema 中没有 nullable 字段"""
        schema = {
            "type": "string",
            "minLength": 3
        }
        
        # null_probability 为 1 时，仍应检查 type 是否包含 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        # 单一 type: "string"，不应生成 null
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, str)


class TestUnionTypeWithNull:
    """测试联合类型中包含 null 的场景"""
    
    def test_union_type_with_null_in_type_list(self):
        """测试 type: ["string", "integer", "null"]"""
        schema = {
            "type": ["string", "integer", "null"],
            "minLength": 3,
            "minimum": 10,
            "maximum": 20
        }
        
        # null_probability 为 0 时，不应生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=0.0)
        )
        
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, (str, int))
            assert result is not None
        
        # null_probability 为 1 时，应该生成 null
        builder = DataBuilder(
            schema,
            config=BuilderConfig(null_probability=1.0)
        )
        
        for _ in range(10):
            result = builder.build()
            assert result is None
    
    def test_union_type_only_null(self):
        """测试 type: ["null"]"""
        schema = {
            "type": ["null"]
        }
        
        builder = DataBuilder(schema)
        
        for _ in range(10):
            result = builder.build()
            assert result is None
    
    def test_union_type_null_and_priority(self):
        """测试联合类型 null 与优先级的协同"""
        schema = {
            "type": ["string", "integer", "null"]
        }
        
        # 设置优先级，null_probability 为 0
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string", "integer"],
                null_probability=0.0
            )
        )
        
        # 应该只生成 string 或 integer，不生成 null
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, (str, int))
            assert result is not None


class TestUnionTypePriorityWithNestedObjects:
    """测试嵌套对象中的联合类型优先级"""
    
    def test_nested_union_type_priority(self):
        """测试嵌套对象中的联合类型优先级"""
        schema = {
            "type": "object",
            "properties": {
                "field1": {
                    "type": ["string", "integer"]
                },
                "field2": {
                    "type": ["number", "boolean"]
                }
            }
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string", "number"],
                null_probability=0.0
            )
        )
        
        for _ in range(10):
            result = builder.build()
            # field1 应该是 string（优先级匹配）
            assert isinstance(result["field1"], str)
            # field2 应该是 number（优先级匹配）
            assert isinstance(result["field2"], float)
    
    def test_array_of_union_type(self):
        """测试数组中的联合类型"""
        schema = {
            "type": "array",
            "items": {
                "type": ["string", "integer"]
            }
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["string"],
                null_probability=0.0
            )
        )
        
        for _ in range(5):
            result = builder.build()
            # 所有元素都应该是 string 类型
            assert all(isinstance(item, str) for item in result)


class TestUnionTypeEdgeCases:
    """测试联合类型的边界情况"""
    
    def test_union_type_empty_schema(self):
        """测试空 schema 的联合类型处理"""
        schema = {
            "type": ["string", "integer"]
        }
        
        builder = DataBuilder(schema)
        
        # 应该能正常生成数据
        result = builder.build()
        assert isinstance(result, (str, int))
    
    def test_union_type_with_constraints(self):
        """测试带约束的联合类型"""
        schema = {
            "type": ["string", "integer"],
            "string": {"minLength": 5, "maxLength": 10},
            "integer": {"minimum": 10, "maximum": 20}
        }
        
        # 注意：JSON Schema 不支持这种约束语法，但测试可以覆盖
        # 实际实现中，约束应该在对象内部定义
        builder = DataBuilder(schema)
        
        for _ in range(10):
            result = builder.build()
            assert isinstance(result, (str, int))
    
    def test_union_type_priority_mixed(self):
        """测试混合类型的优先级"""
        schema = {
            "type": ["string", "number", "boolean", "integer"]
        }
        
        builder = DataBuilder(
            schema,
            config=BuilderConfig(
                union_type_priority=["boolean", "string"]
            )
        )
        
        # 应该优先选择 boolean 或 string
        results = [builder.build() for _ in range(20)]
        
        # 验证所有结果都是 boolean 或 string
        for result in results:
            assert isinstance(result, (bool, str))
