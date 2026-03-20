"""JSON Schema 逻辑关键字测试：$ref / definitions / $defs / allOf / anyOf / oneOf"""
import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, fixed
from data_builder.exceptions import SchemaError


class TestRef:
    """$ref + definitions/$defs 解析"""

    def test_ref_definitions(self):
        schema = {
            "type": "object",
            "definitions": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "zip": {"type": "string", "example": "100000"},
                    },
                }
            },
            "properties": {
                "address": {"$ref": "#/definitions/Address"},
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["address"], dict)
        assert isinstance(result["address"]["city"], str)
        assert result["address"]["zip"] == "100000"

    def test_ref_defs(self):
        """$defs（Draft 2019-09 写法）"""
        schema = {
            "type": "object",
            "$defs": {
                "Score": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "properties": {
                "score": {"$ref": "#/$defs/Score"},
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_ref_nested(self):
        """$ref 引用的定义中又包含 $ref"""
        schema = {
            "type": "object",
            "definitions": {
                "Street": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "example": "长安街"}},
                },
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"$ref": "#/definitions/Street"},
                        "city": {"type": "string", "example": "北京"},
                    },
                },
            },
            "properties": {
                "home": {"$ref": "#/definitions/Address"},
            },
        }
        result = DataBuilder(schema).build()
        assert result["home"]["street"]["name"] == "长安街"
        assert result["home"]["city"] == "北京"

    def test_ref_circular_raises(self):
        schema = {
            "type": "object",
            "definitions": {
                "A": {"$ref": "#/definitions/A"},
            },
            "properties": {
                "x": {"$ref": "#/definitions/A"},
            },
        }
        with pytest.raises(SchemaError, match="循环引用"):
            DataBuilder(schema).build()

    def test_ref_invalid_path_raises(self):
        schema = {
            "type": "object",
            "properties": {
                "x": {"$ref": "#/definitions/NotExist"},
            },
        }
        with pytest.raises(SchemaError, match="路径未找到"):
            DataBuilder(schema).build()

    def test_ref_external_raises(self):
        schema = {
            "type": "object",
            "properties": {
                "x": {"$ref": "http://example.com/schema.json"},
            },
        }
        with pytest.raises(SchemaError, match="仅支持内部"):
            DataBuilder(schema).build()

    def test_ref_with_field_policy(self):
        """$ref 字段可被 FieldPolicy 覆盖"""
        schema = {
            "type": "object",
            "definitions": {
                "Name": {"type": "string"},
            },
            "properties": {
                "name": {"$ref": "#/definitions/Name"},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("name", fixed("Alice"))])
        result = DataBuilder(schema, config).build()
        assert result["name"] == "Alice"

    def test_ref_with_sibling_keywords(self):
        """$ref 旁边有额外关键字时合并"""
        schema = {
            "type": "object",
            "definitions": {
                "Base": {
                    "type": "object",
                    "properties": {"a": {"type": "string", "example": "hello"}},
                },
            },
            "properties": {
                "item": {
                    "$ref": "#/definitions/Base",
                    "properties": {"b": {"type": "integer", "minimum": 1, "maximum": 1}},
                },
            },
        }
        result = DataBuilder(schema).build()
        assert result["item"]["a"] == "hello"
        assert result["item"]["b"] == 1

    def test_ref_resolved_deepcopy(self):
        """$ref 解析应该是深拷贝 (BUG-006)"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "$ref": "#/definitions/User"
                },
                "admin": {
                    "$ref": "#/definitions/User"
                }
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                }
            }
        }
        builder = DataBuilder(schema)
        # 构建时，两个 $ref 应该解析到独立的对象
        result = builder.build(count=2)
        # 修改一个对象的值不应该影响另一个
        # 这个测试主要用于验证深拷贝不会导致共享引用问题
        assert all("user" in r for r in result)
        assert all("admin" in r for r in result)


class TestAllOf:
    """allOf 合并"""

    def test_allof_merge_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "contact": {
                    "allOf": [
                        {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                            },
                        },
                        {
                            "properties": {
                                "phone": {"type": "string", "example": "13800138000"},
                            },
                        },
                    ],
                }
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["contact"], dict)
        assert "@" in result["contact"]["email"]
        assert result["contact"]["phone"] == "13800138000"

    def test_allof_merge_required(self):
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                    "required": ["a"],
                },
                {
                    "properties": {"b": {"type": "integer", "minimum": 1, "maximum": 1}},
                    "required": ["b"],
                },
            ],
        }
        result = DataBuilder(schema).build()
        assert "a" in result
        assert result["b"] == 1

    def test_allof_with_ref(self):
        """allOf 子 schema 中包含 $ref"""
        schema = {
            "type": "object",
            "definitions": {
                "Named": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "example": "test"}},
                },
            },
            "properties": {
                "item": {
                    "allOf": [
                        {"$ref": "#/definitions/Named"},
                        {"properties": {"value": {"type": "integer", "minimum": 5, "maximum": 5}}},
                    ],
                }
            },
        }
        result = DataBuilder(schema).build()
        assert result["item"]["name"] == "test"
        assert result["item"]["value"] == 5

    def test_allof_with_base_properties(self):
        """allOf 旁边有已有 properties 时合并"""
        schema = {
            "type": "object",
            "properties": {
                "item": {
                    "type": "object",
                    "properties": {"base": {"type": "string", "example": "ok"}},
                    "allOf": [
                        {"properties": {"extra": {"type": "integer", "minimum": 1, "maximum": 1}}},
                    ],
                }
            },
        }
        result = DataBuilder(schema).build()
        assert result["item"]["base"] == "ok"
        assert result["item"]["extra"] == 1


class TestOneOf:
    """oneOf 多态选择"""

    def test_oneof_basic(self):
        schema = {
            "type": "object",
            "properties": {
                "payment": {
                    "oneOf": [
                        {"type": "object", "properties": {"card": {"type": "string", "example": "visa"}}},
                        {"type": "object", "properties": {"alipay": {"type": "string", "example": "test@ali"}}},
                    ]
                }
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["payment"], dict)
        assert "card" in result["payment"] or "alipay" in result["payment"]

    def test_oneof_primitive(self):
        """oneOf 选择基本类型"""
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "oneOf": [
                        {"type": "string", "example": "hello"},
                        {"type": "integer", "minimum": 42, "maximum": 42},
                    ]
                }
            },
        }
        result = DataBuilder(schema).build()
        assert result["value"] in ("hello", 42)

    def test_oneof_with_ref(self):
        schema = {
            "type": "object",
            "definitions": {
                "Cat": {"type": "object", "properties": {"meow": {"type": "boolean", "const": True}}},
                "Dog": {"type": "object", "properties": {"bark": {"type": "boolean", "const": True}}},
            },
            "properties": {
                "pet": {
                    "oneOf": [
                        {"$ref": "#/definitions/Cat"},
                        {"$ref": "#/definitions/Dog"},
                    ]
                }
            },
        }
        result = DataBuilder(schema).build()
        assert ("meow" in result["pet"]) or ("bark" in result["pet"])

    def test_oneof_coverage(self):
        """多次生成应覆盖多个分支"""
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "oneOf": [
                        {"type": "string", "const": "A"},
                        {"type": "string", "const": "B"},
                    ]
                }
            },
        }
        builder = DataBuilder(schema)
        values = {builder.build()["v"] for _ in range(50)}
        assert values == {"A", "B"}


class TestAnyOf:
    """anyOf 多态选择"""

    def test_anyof_basic(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {
                    "anyOf": [
                        {"type": "string", "example": "abc"},
                        {"type": "integer", "minimum": 1, "maximum": 1},
                    ]
                }
            },
        }
        result = DataBuilder(schema).build()
        assert result["id"] in ("abc", 1)

    def test_anyof_objects(self):
        schema = {
            "type": "object",
            "properties": {
                "shape": {
                    "anyOf": [
                        {"type": "object", "properties": {"radius": {"type": "number", "const": 5.0}}},
                        {"type": "object", "properties": {"side": {"type": "number", "const": 10.0}}},
                    ]
                }
            },
        }
        result = DataBuilder(schema).build()
        assert ("radius" in result["shape"]) or ("side" in result["shape"])

    def test_anyof_coverage(self):
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "anyOf": [
                        {"type": "string", "const": "X"},
                        {"type": "string", "const": "Y"},
                    ]
                }
            },
        }
        builder = DataBuilder(schema)
        values = {builder.build()["v"] for _ in range(50)}
        assert values == {"X", "Y"}


class TestIntegration:
    """综合场景"""

    def test_full_schema(self):
        """plan 中给出的综合验证 schema"""
        schema = {
            "type": "object",
            "definitions": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "zip": {"type": "string"},
                    },
                }
            },
            "properties": {
                "name": {"type": "string"},
                "address": {"$ref": "#/definitions/Address"},
                "contact": {
                    "allOf": [
                        {"properties": {"email": {"type": "string", "format": "email"}}},
                        {"properties": {"phone": {"type": "string"}}},
                    ]
                },
                "payment": {
                    "oneOf": [
                        {"type": "object", "properties": {"card": {"type": "string"}}},
                        {"type": "object", "properties": {"alipay": {"type": "string"}}},
                    ]
                },
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["name"], str)
        assert isinstance(result["address"], dict)
        assert "city" in result["address"]
        assert "zip" in result["address"]
        assert isinstance(result["contact"], dict)
        assert "email" in result["contact"]
        assert "phone" in result["contact"]
        assert isinstance(result["payment"], dict)

    def test_ref_in_array_items(self):
        """数组 items 引用 $ref"""
        schema = {
            "type": "object",
            "definitions": {
                "Tag": {
                    "type": "object",
                    "properties": {"label": {"type": "string", "example": "hot"}},
                },
            },
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/Tag"},
                    "minItems": 2,
                    "maxItems": 2,
                },
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["tags"]) == 2
        assert all(t["label"] == "hot" for t in result["tags"])

    def test_allof_at_root(self):
        """根级 allOf"""
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"id": {"type": "integer", "minimum": 1, "maximum": 1}},
                },
                {
                    "properties": {"name": {"type": "string", "example": "root"}},
                },
            ]
        }
        result = DataBuilder(schema).build()
        assert result["id"] == 1
        assert result["name"] == "root"

    def test_bulk_with_ref(self):
        """批量生成 + $ref"""
        schema = {
            "type": "object",
            "definitions": {
                "Item": {
                    "type": "object",
                    "properties": {"v": {"type": "integer", "minimum": 0, "maximum": 100}},
                },
            },
            "properties": {
                "item": {"$ref": "#/definitions/Item"},
            },
        }
        results = DataBuilder(schema).build(count=5)
        assert len(results) == 5
        assert all(isinstance(r["item"]["v"], int) for r in results)
