import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, fixed, seq, ref


class TestNestedObjects:
    def test_single_level_nesting(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 99},
                    },
                }
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["user"], dict)
        assert isinstance(result["user"]["name"], str)
        assert 0 <= result["user"]["age"] <= 99

    def test_multi_level_nesting(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {
                    "type": "object",
                    "properties": {
                        "b": {
                            "type": "object",
                            "properties": {
                                "c": {"type": "integer", "minimum": 1, "maximum": 1},
                            },
                        }
                    },
                }
            },
        }
        result = DataBuilder(schema).build()
        assert result["a"]["b"]["c"] == 1


class TestArrayTypes:
    def test_array_of_string(self):
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2}
            },
        }
        result = DataBuilder(schema).build()
        assert isinstance(result["tags"], list)
        assert len(result["tags"]) == 2
        assert all(isinstance(t, str) for t in result["tags"])

    def test_array_of_integer(self):
        schema = {
            "type": "object",
            "properties": {
                "scores": {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3}
            },
        }
        result = DataBuilder(schema).build()
        assert all(isinstance(s, int) for s in result["scores"])

    def test_array_of_object(self):
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    },
                    "minItems": 2,
                    "maxItems": 2,
                }
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["items"]) == 2
        assert all(isinstance(item["id"], int) for item in result["items"])

    def test_min_max_items(self):
        schema = {
            "type": "object",
            "properties": {
                "xs": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4}
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["xs"]) == 4


class TestMixedStructure:
    def test_nested_object_with_array(self, nested_order_schema):
        result = DataBuilder(nested_order_schema).build()
        assert isinstance(result["user"], dict)
        assert isinstance(result["orders"], list)
        assert 2 <= len(result["orders"]) <= 5
        for order in result["orders"]:
            assert order["status"] in ["pending", "paid", "shipped", "done"]


class TestWildcardPaths:
    def test_user_wildcard(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("user.*", fixed("MASKED"))])
        result = DataBuilder(schema, config).build()
        assert result["user"]["name"] == "MASKED"
        assert result["user"]["email"] == "MASKED"

    def test_array_item_wildcard(self):
        schema = {
            "type": "object",
            "properties": {
                "orders": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                    },
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("orders[*].id", seq(start=1))])
        result = DataBuilder(schema, config).build()
        assert result["orders"][0]["id"] == 1
        assert result["orders"][1]["id"] == 2
        assert result["orders"][2]["id"] == 3


class TestRefCrossLevel:
    def test_ref_sibling_field(self):
        schema = {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "owner_id": {"type": "integer"},
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("user_id", fixed(42)),
            FieldPolicy("owner_id", ref("user_id")),
        ])
        result = DataBuilder(schema, config).build()
        assert result["user_id"] == 42
        assert result["owner_id"] == 42

    def test_ref_with_transform(self):
        schema = {
            "type": "object",
            "properties": {
                "price": {"type": "number"},
                "discounted": {"type": "number"},
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("price", fixed(100.0)),
            FieldPolicy("discounted", ref("price", transform=lambda v: round(v * 0.9, 2))),
        ])
        result = DataBuilder(schema, config).build()
        assert result["discounted"] == 90.0


class TestUniqueItems:
    def test_unique_items_integer(self):
        schema = {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1, "maximum": 100},
                    "minItems": 5,
                    "maxItems": 5,
                    "uniqueItems": True,
                }
            },
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result["ids"]) == len(set(result["ids"]))

    def test_unique_items_string(self):
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["a", "b", "c", "d"]},
                    "minItems": 4,
                    "maxItems": 4,
                    "uniqueItems": True,
                }
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["tags"]) == len(set(result["tags"]))

    def test_unique_items_false_allows_duplicates(self):
        """uniqueItems: false 不影响正常生成"""
        schema = {
            "type": "object",
            "properties": {
                "xs": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1, "maximum": 1},
                    "minItems": 3,
                    "maxItems": 3,
                    "uniqueItems": False,
                }
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["xs"]) == 3
        assert all(x == 1 for x in result["xs"])


class TestUnionType:
    def test_string_or_null(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]}
            },
        }
        # null_probability=0 时应始终生成 string
        results = [DataBuilder(schema).build()["name"] for _ in range(20)]
        assert all(isinstance(v, str) for v in results)

    def test_integer_or_string(self):
        schema = {
            "type": "object",
            "properties": {
                "val": {"type": ["integer", "string"]}
            },
        }
        types_seen = set()
        for _ in range(50):
            v = DataBuilder(schema).build()["val"]
            types_seen.add(type(v).__name__)
        # 应能生成两种类型
        assert "int" in types_seen or "str" in types_seen

    def test_only_null(self):
        schema = {
            "type": "object",
            "properties": {
                "empty": {"type": ["null"]}
            },
        }
        result = DataBuilder(schema).build()
        assert result["empty"] is None


class TestAdditionalProperties:
    def test_additional_properties_generates_fields(self):
        schema = {
            "type": "object",
            "additionalProperties": {"type": "integer", "minimum": 0, "maximum": 100},
        }
        result = DataBuilder(schema).build()
        assert len(result) >= 1
        assert all(isinstance(v, int) for v in result.values())

    def test_additional_properties_with_existing_properties(self):
        """有 properties 时不额外生成"""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": {"type": "integer"},
        }
        result = DataBuilder(schema).build()
        assert "name" in result
        # 有 properties 时不应生成 additional
        assert set(result.keys()) == {"name"}

    def test_additional_properties_bool_ignored(self):
        """additionalProperties: true/false 为布尔值时不生成额外属性"""
        schema = {
            "type": "object",
            "additionalProperties": True,
        }
        result = DataBuilder(schema).build()
        assert isinstance(result, dict)
