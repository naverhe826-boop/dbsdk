"""SchemaResolver 和 ValueGenerator 测试"""

import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, fixed
from data_builder.generators import SchemaResolver, ValueGenerator
from data_builder.exceptions import SchemaError


class TestSchemaResolverInit:
    """测试 SchemaResolver 初始化"""
    
    def test_init_with_builder(self):
        """使用 DataBuilder 初始化"""
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        resolver = SchemaResolver(builder)
        
        assert resolver.builder == builder


class TestSchemaResolverResolve:
    """测试 resolve() 方法"""
    
    @pytest.fixture
    def builder(self):
        schema = {"type": "object"}
        return DataBuilder(schema)
    
    @pytest.fixture
    def resolver(self, builder):
        return SchemaResolver(builder)
    
    def test_resolve_simple_schema(self, resolver):
        """解析简单 schema"""
        schema = {"type": "string"}
        result = resolver.resolve(schema)
        
        assert result == schema
    
    def test_resolve_with_ref(self, builder):
        """解析 $ref 引用"""
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "#/definitions/User"}
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        builder = DataBuilder(schema)
        resolver = SchemaResolver(builder)
        
        user_schema = schema["properties"]["user"]
        result = resolver.resolve(user_schema)
        
        assert "$ref" not in result
        assert result["type"] == "object"
        assert "name" in result["properties"]
    
    def test_resolve_with_allOf(self, resolver):
        """解析 allOf 合并"""
        schema = {
            "allOf": [
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"properties": {"age": {"type": "integer"}}}
            ]
        }
        result = resolver.resolve(schema)
        
        assert result["type"] == "object"
        assert "name" in result["properties"]
        assert "age" in result["properties"]
    
    def test_resolve_with_if_then_else(self, resolver):
        """解析 if/then/else"""
        schema = {
            "if": {"type": "object"},
            "then": {"properties": {"name": {"type": "string"}}},
            "else": {"properties": {"value": {"type": "integer"}}}
        }
        result = resolver.resolve(schema)
        
        # 随机选择 then 或 else
        assert "properties" in result
    
    def test_resolve_with_not_type(self, resolver):
        """解析 not 排除类型"""
        schema = {
            "not": {"type": "string"}
        }
        result = resolver.resolve(schema)
        
        # 排除 string 后，应该选择其他类型
        assert result.get("type") != "string"
    
    def test_resolve_circular_ref(self, builder):
        """解析循环引用"""
        schema = {
            "type": "object",
            "properties": {
                "self": {"$ref": "#"}
            }
        }
        builder = DataBuilder(schema, BuilderConfig(max_depth=5))
        resolver = SchemaResolver(builder)
        
        # 启用 max_depth 时，循环引用应该返回截断值
        result = resolver.resolve(schema)
        
        assert result["type"] == "object"
    
    def test_resolve_circular_ref_without_max_depth(self, builder):
        """未启用 max_depth 时检测循环引用"""
        schema = {
            "type": "object",
            "properties": {
                "self": {"$ref": "#"}
            }
        }
        builder = DataBuilder(schema)  # 不启用 max_depth
        resolver = SchemaResolver(builder)
        
        # 未启用 max_depth 时，应该抛出错误
        with pytest.raises(SchemaError):
            resolver.resolve({"$ref": "#"})


class TestSchemaResolverResolveRef:
    """测试 _resolve_ref() 方法"""
    
    @pytest.fixture
    def builder(self):
        schema = {
            "type": "object",
            "definitions": {
                "User": {"type": "object", "properties": {"name": {"type": "string"}}}
            },
            "components": {
                "schemas": {
                    "Product": {"type": "object", "properties": {"price": {"type": "number"}}}
                }
            }
        }
        return DataBuilder(schema)
    
    @pytest.fixture
    def resolver(self, builder):
        return SchemaResolver(builder)
    
    def test_resolve_definitions_ref(self, resolver):
        """解析 #/definitions/* 引用"""
        result = resolver._resolve_ref("#/definitions/User")
        
        assert result["type"] == "object"
        assert "name" in result["properties"]
    
    def test_resolve_components_schemas_ref(self, resolver):
        """解析 #/components/schemas/* 引用"""
        result = resolver._resolve_ref("#/components/schemas/Product")
        
        assert result["type"] == "object"
        assert "price" in result["properties"]
    
    def test_resolve_invalid_ref_format(self, resolver):
        """解析无效格式的引用"""
        with pytest.raises(SchemaError) as exc_info:
            resolver._resolve_ref("http://example.com/schema")
        
        assert "仅支持内部 $ref 引用" in str(exc_info.value)
    
    def test_resolve_nonexistent_ref(self, resolver):
        """解析不存在的引用路径"""
        with pytest.raises(SchemaError) as exc_info:
            resolver._resolve_ref("#/definitions/Unknown")
        
        assert "$ref 路径未找到" in str(exc_info.value)


class TestSchemaResolverMergeSchemas:
    """测试 _merge_schemas() 方法"""
    
    @pytest.fixture
    def resolver(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return SchemaResolver(builder)
    
    def test_merge_properties(self, resolver):
        """合并 properties"""
        base = {"type": "object", "properties": {"name": {"type": "string"}}}
        override = {"properties": {"age": {"type": "integer"}}}
        
        result = resolver._merge_schemas(base, override)
        
        assert "name" in result["properties"]
        assert "age" in result["properties"]
    
    def test_merge_required(self, resolver):
        """合并 required"""
        base = {"required": ["name"]}
        override = {"required": ["age", "name"]}
        
        result = resolver._merge_schemas(base, override)
        
        assert "name" in result["required"]
        assert "age" in result["required"]
        # 去重
        assert len(result["required"]) == 2
    
    def test_override_other_fields(self, resolver):
        """覆盖其他字段"""
        base = {"type": "string", "minLength": 5}
        override = {"minLength": 10}
        
        result = resolver._merge_schemas(base, override)
        
        assert result["minLength"] == 10


class TestValueGeneratorInit:
    """测试 ValueGenerator 初始化"""
    
    def test_init_with_builder(self):
        """使用 DataBuilder 初始化"""
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        generator = ValueGenerator(builder)
        
        assert generator.builder == builder
        assert generator.schema_resolver is not None


class TestValueGeneratorGenerateValue:
    """测试 generate_value() 方法"""
    
    @pytest.fixture
    def builder(self):
        schema = {"type": "object"}
        return DataBuilder(schema)
    
    @pytest.fixture
    def generator(self, builder):
        return ValueGenerator(builder)
    
    def test_generate_simple_object(self, generator):
        """生成简单对象"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        result = generator.generate_value(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert isinstance(result, dict)
        assert "name" in result
    
    def test_generate_with_depth_limit(self, builder):
        """测试深度限制"""
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"}
                    }
                }
            }
        }
        builder = DataBuilder(schema, BuilderConfig(max_depth=1))
        generator = ValueGenerator(builder)
        
        result = generator.generate_value(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=1  # 已达到 max_depth
        )
        
        # 达到 max_depth 时返回空对象
        assert result == {}
    



class TestValueGeneratorGenerateObject:
    """测试 _generate_object() 方法"""
    
    @pytest.fixture
    def generator(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return ValueGenerator(builder)
    
    def test_generate_with_required_fields(self, generator):
        """生成包含必需字段的对象"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        result = generator._generate_object(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert "name" in result
        # 可选字段也可能生成
        assert isinstance(result, dict)
    
    def test_generate_with_example(self, generator):
        """使用 example 生成对象"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "example": {"name": "John", "age": 30}
        }
        
        result = generator._generate_object(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert result["name"] == "John"
        assert result["age"] == 30
    
    def test_generate_with_min_max_properties(self, generator):
        """测试 minProperties/maxProperties"""
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
                "c": {"type": "string"},
                "d": {"type": "string"}
            },
            "minProperties": 2,
            "maxProperties": 3
        }
        
        result = generator._generate_object(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert 2 <= len(result) <= 3
    
    def test_generate_with_additional_properties(self, generator):
        """测试 additionalProperties"""
        schema = {
            "type": "object",
            "additionalProperties": {"type": "string"}
        }
        
        result = generator._generate_object(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        # 应该生成一些额外属性
        assert len(result) > 0
    
    def test_generate_with_pattern_properties(self, generator):
        """测试 patternProperties"""
        schema = {
            "type": "object",
            "patternProperties": {
                "^x-": {"type": "string"}
            }
        }
        
        result = generator._generate_object(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        # 应该生成匹配模式的属性
        assert any(k.startswith("x-") for k in result.keys())


class TestValueGeneratorGenerateArray:
    """测试 _generate_array() 方法"""
    
    @pytest.fixture
    def generator(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return ValueGenerator(builder)
    
    def test_generate_simple_array(self, generator):
        """生成简单数组"""
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        
        result = generator._generate_array(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, str) for item in result)
    
    def test_generate_with_min_max_items(self, generator):
        """测试 minItems/maxItems"""
        schema = {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 5,
            "maxItems": 10
        }
        
        result = generator._generate_array(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        assert 5 <= len(result) <= 10
    
    def test_generate_with_unique_items(self, generator):
        """测试 uniqueItems"""
        schema = {
            "type": "array",
            "items": {"type": "integer", "minimum": 0, "maximum": 100},
            "uniqueItems": True,
            "minItems": 3,
            "maxItems": 5
        }
        
        result = generator._generate_array(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        # 所有元素应该唯一
        assert len(result) == len(set(result))
    
    def test_generate_with_prefix_items(self, generator):
        """测试 prefixItems"""
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "string"},
                {"type": "integer"}
            ],
            "items": {"type": "boolean"}
        }
        
        result = generator._generate_array(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        # 前两个元素类型固定
        assert isinstance(result[0], str)
        assert isinstance(result[1], int)
        # 后续元素为 boolean
        if len(result) > 2:
            assert isinstance(result[2], bool)
    
    def test_generate_with_contains(self, generator):
        """测试 contains"""
        schema = {
            "type": "array",
            "items": {"type": "integer"},
            "contains": {"type": "string"}
        }
        
        result = generator._generate_array(
            schema=schema,
            path="",
            root_data={},
            parent_data={},
            index=0,
            depth=0
        )
        
        # 应该包含至少一个 string 元素
        assert any(isinstance(item, str) for item in result)


class TestValueGeneratorGeneratePrimitive:
    """测试 _generate_primitive() 方法"""
    
    @pytest.fixture
    def generator(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return ValueGenerator(builder)
    
    def test_generate_enum(self, generator):
        """生成枚举值"""
        schema = {"type": "string", "enum": ["active", "inactive", "pending"]}
        
        result = generator._generate_primitive(schema, "string", "status")
        
        assert result in ["active", "inactive", "pending"]
    
    def test_generate_const(self, generator):
        """生成常量值"""
        schema = {"type": "string", "const": "fixed_value"}
        
        result = generator._generate_primitive(schema, "string", "field")
        
        assert result == "fixed_value"
    
    def test_generate_default(self, generator):
        """生成默认值"""
        schema = {"type": "string", "default": "default_value"}
        
        result = generator._generate_primitive(schema, "string", "field")
        
        assert result == "default_value"
    
    def test_generate_examples(self, generator):
        """从 examples 中生成"""
        schema = {"type": "string", "examples": ["example1", "example2"]}
        
        result = generator._generate_primitive(schema, "string", "field")
        
        assert result in ["example1", "example2"]
    
    def test_generate_example(self, generator):
        """从 example 中生成"""
        schema = {"type": "string", "example": "example_value"}
        
        result = generator._generate_primitive(schema, "string", "field")
        
        assert result == "example_value"
    
    def test_generate_string_with_pattern(self, generator):
        """生成匹配正则的字符串"""
        schema = {"type": "string", "pattern": r"^[A-Z]{3}\d{3}$"}
        
        result = generator._generate_primitive(schema, "string", "field")
        
        import re
        assert re.match(r"^[A-Z]{3}\d{3}$", result)
    
    def test_generate_integer_with_range(self, generator):
        """生成范围内的整数"""
        schema = {"type": "integer", "minimum": 10, "maximum": 20}
        
        result = generator._generate_primitive(schema, "integer", "field")
        
        assert 10 <= result <= 20
    
    def test_generate_integer_with_multiple_of(self, generator):
        """生成倍数整数"""
        schema = {"type": "integer", "minimum": 0, "maximum": 20, "multipleOf": 5}
        
        result = generator._generate_primitive(schema, "integer", "field")
        
        assert result % 5 == 0
    
    def test_generate_number_with_range(self, generator):
        """生成范围内的浮点数"""
        schema = {"type": "number", "minimum": 0.0, "maximum": 1.0}
        
        result = generator._generate_primitive(schema, "number", "field")
        
        assert 0.0 <= result <= 1.0
    
    def test_generate_boolean(self, generator):
        """生成布尔值"""
        schema = {"type": "boolean"}
        
        result = generator._generate_primitive(schema, "boolean", "field")
        
        assert isinstance(result, bool)
    
    def test_generate_null(self, generator):
        """生成 null"""
        schema = {"type": "null"}
        
        result = generator._generate_primitive(schema, "null", "field")
        
        assert result is None


class TestValueGeneratorValidateExample:
    """测试 _validate_example() 方法"""
    
    @pytest.fixture
    def generator(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return ValueGenerator(builder)
    
    def test_validate_correct_type(self, generator):
        """验证类型正确"""
        schema = {"type": "string"}
        example = "valid_string"
        
        assert generator._validate_example(schema, example)
    
    def test_validate_incorrect_type(self, generator):
        """验证类型错误"""
        schema = {"type": "string"}
        example = 123
        
        assert not generator._validate_example(schema, example)
    
    def test_validate_enum(self, generator):
        """验证枚举值"""
        schema = {"type": "string", "enum": ["a", "b", "c"]}
        
        assert generator._validate_example(schema, "a")
        assert not generator._validate_example(schema, "d")
    
    def test_validate_const(self, generator):
        """验证常量值"""
        schema = {"type": "string", "const": "fixed"}
        
        assert generator._validate_example(schema, "fixed")
        assert not generator._validate_example(schema, "other")
    
    def test_validate_range(self, generator):
        """验证数值范围"""
        schema = {"type": "integer", "minimum": 10, "maximum": 20}
        
        assert generator._validate_example(schema, 15)
        assert not generator._validate_example(schema, 5)
        assert not generator._validate_example(schema, 25)
    
    def test_validate_string_length(self, generator):
        """验证字符串长度"""
        schema = {"type": "string", "minLength": 2, "maxLength": 5}
        
        assert generator._validate_example(schema, "abc")
        assert not generator._validate_example(schema, "a")
        assert not generator._validate_example(schema, "abcdef")


class TestValueGeneratorCheckType:
    """测试 _check_type() 方法"""
    
    @pytest.fixture
    def generator(self):
        schema = {"type": "object"}
        builder = DataBuilder(schema)
        return ValueGenerator(builder)
    
    def test_check_null(self, generator):
        assert generator._check_type(None, "null")
        assert not generator._check_type(0, "null")
    
    def test_check_boolean(self, generator):
        assert generator._check_type(True, "boolean")
        assert generator._check_type(False, "boolean")
        assert not generator._check_type(1, "boolean")
    
    def test_check_integer(self, generator):
        assert generator._check_type(42, "integer")
        assert not generator._check_type(True, "integer")  # bool 不是 int
        assert not generator._check_type(3.14, "integer")
    
    def test_check_number(self, generator):
        assert generator._check_type(42, "number")
        assert generator._check_type(3.14, "number")
        assert not generator._check_type(True, "number")
    
    def test_check_string(self, generator):
        assert generator._check_type("hello", "string")
        assert not generator._check_type(42, "string")
    
    def test_check_array(self, generator):
        assert generator._check_type([1, 2, 3], "array")
        assert not generator._check_type("string", "array")
    
    def test_check_object(self, generator):
        assert generator._check_type({"a": 1}, "object")
        assert not generator._check_type([1, 2], "object")


class TestValueGeneratorMakeHashable:
    """测试 _make_hashable() 方法"""
    
    def test_make_hashable_primitive(self):
        """基本类型已经是可哈希的"""
        assert ValueGenerator._make_hashable(42) == 42
        assert ValueGenerator._make_hashable("string") == "string"
    
    def test_make_hashable_dict(self):
        """字典转为元组"""
        result = ValueGenerator._make_hashable({"a": 1, "b": 2})
        
        # 应该是排序后的元组
        assert isinstance(result, tuple)
        assert result == (("a", 1), ("b", 2))
    
    def test_make_hashable_list(self):
        """列表转为元组"""
        result = ValueGenerator._make_hashable([1, 2, 3])
        
        assert result == (1, 2, 3)
    
    def test_make_hashable_nested(self):
        """嵌套结构"""
        result = ValueGenerator._make_hashable({"a": [1, 2], "b": {"c": 3}})
        
        assert isinstance(result, tuple)
