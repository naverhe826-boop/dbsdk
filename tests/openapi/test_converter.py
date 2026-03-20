"""
测试 SchemaConverter 的 nullable 转换功能。
"""

import pytest

from data_builder.openapi.converter import SchemaConverter


class TestNullableConversion:
    """测试 nullable 字段转换"""
    
    def test_nullable_with_simple_type(self):
        """测试 nullable + 简单类型转换"""
        openapi_schema = {
            "type": "string",
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：type 转换为数组，包含 "null"
        assert "nullable" not in json_schema
        assert "type" in json_schema
        assert isinstance(json_schema["type"], list)
        assert "string" in json_schema["type"]
        assert "null" in json_schema["type"]
    
    def test_nullable_false(self):
        """测试 nullable: false 不做转换"""
        openapi_schema = {
            "type": "string",
            "nullable": False
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：nullable 被移除，type 保持不变
        assert "nullable" not in json_schema
        assert json_schema["type"] == "string"
    
    def test_nullable_with_oneof(self):
        """测试 nullable + oneOf 转换"""
        openapi_schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"}
            ],
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：在 oneOf 中添加 {"type": "null"}
        assert "nullable" not in json_schema
        assert "oneOf" in json_schema
        assert len(json_schema["oneOf"]) == 3
        assert {"type": "null"} in json_schema["oneOf"]
    
    def test_nullable_with_anyof(self):
        """测试 nullable + anyOf 转换"""
        openapi_schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"}
            ],
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：在 anyOf 中添加 {"type": "null"}
        assert "nullable" not in json_schema
        assert "anyOf" in json_schema
        assert len(json_schema["anyOf"]) == 3
        assert {"type": "null"} in json_schema["anyOf"]
    
    def test_nullable_with_allof(self):
        """测试 nullable + allOf 转换"""
        openapi_schema = {
            "allOf": [
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"type": "object", "properties": {"age": {"type": "integer"}}}
            ],
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：allOf 转换为 oneOf 包装
        assert "nullable" not in json_schema
        assert "allOf" not in json_schema
        assert "oneOf" in json_schema
        assert len(json_schema["oneOf"]) == 2
        
        # oneOf 包含原始 allOf 和 null 类型
        one_of_options = json_schema["oneOf"]
        assert {"type": "null"} in one_of_options
        
        # 找到包含 allOf 的选项
        allof_option = None
        for option in one_of_options:
            if "allOf" in option:
                allof_option = option
                break
        
        assert allof_option is not None
        assert len(allof_option["allOf"]) == 2
    
    def test_nullable_without_type_or_composite(self):
        """测试 nullable 但无 type 也无复合类型"""
        openapi_schema = {
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：添加 type: "null"
        assert "nullable" not in json_schema
        assert json_schema["type"] == "null"
    
    def test_nullable_with_type_array(self):
        """测试 nullable + type 数组"""
        openapi_schema = {
            "type": ["string", "integer"],
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=True
        )
        
        # 验证：type 数组添加 "null"
        assert "nullable" not in json_schema
        assert isinstance(json_schema["type"], list)
        assert "string" in json_schema["type"]
        assert "integer" in json_schema["type"]
        assert "null" in json_schema["type"]
    
    def test_nullable_conversion_disabled(self):
        """测试禁用 nullable 转换"""
        openapi_schema = {
            "type": "string",
            "nullable": True
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            openapi_schema, convert_nullable=False
        )
        
        # 验证：nullable 保留，不做转换
        assert "nullable" in json_schema
        assert json_schema["nullable"] is True
        assert json_schema["type"] == "string"
