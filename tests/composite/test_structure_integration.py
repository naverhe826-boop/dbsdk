"""StructureStrategy 集成测试：PropertyCount / PropertySelection / ContainsCount / SchemaSelection / prefixItems"""
import pytest
from data_builder import (
    DataBuilder, BuilderConfig, FieldPolicy,
    property_count, property_selection, contains_count, schema_selection,
    fixed, range_int, callable_strategy, enum,
)


# ── prefixItems 原生支持 ────────────────────────────────────

class TestPrefixItems:
    def test_basic_prefix_items(self):
        schema = {
            "type": "object",
            "properties": {
                "tuple": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "hello"},
                        {"type": "integer", "minimum": 42, "maximum": 42},
                        {"type": "boolean", "const": True},
                    ],
                    "items": {"type": "string"},
                }
            },
        }
        result = DataBuilder(schema).build()
        arr = result["tuple"]
        assert arr[0] == "hello"
        assert arr[1] == 42
        assert arr[2] is True

    def test_prefix_items_with_additional_items(self):
        """prefixItems 之后的位置用 items schema 填充"""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "integer", "minimum": 1, "maximum": 1},
                    ],
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
        }
        result = DataBuilder(schema).build()
        arr = result["data"]
        assert len(arr) == 3
        assert arr[0] == 1
        assert isinstance(arr[1], str)
        assert isinstance(arr[2], str)

    def test_prefix_items_false_limits_length(self):
        """items: false 时数组长度不超过 prefixItems 长度"""
        schema = {
            "type": "object",
            "properties": {
                "pair": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "a"},
                        {"type": "integer", "minimum": 1, "maximum": 1},
                    ],
                    "items": False,
                }
            },
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result["pair"]) <= 2

    def test_prefix_items_min_items_default(self):
        """无 minItems 时默认至少生成 len(prefixItems) 个元素"""
        schema = {
            "type": "object",
            "properties": {
                "t": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "x"},
                        {"type": "string", "const": "y"},
                        {"type": "string", "const": "z"},
                    ],
                    "items": {"type": "string"},
                }
            },
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result["t"]) >= 3

    def test_no_prefix_items_unchanged(self):
        """无 prefixItems 时行为不变"""
        schema = {
            "type": "object",
            "properties": {
                "xs": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}
            },
        }
        result = DataBuilder(schema).build()
        assert len(result["xs"]) == 2
        assert all(isinstance(x, int) for x in result["xs"])


# ── PropertyCountStrategy 集成测试 ──────────────────────────

OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "profile": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "example": "Alice"},
                "age": {"type": "integer", "minimum": 20, "maximum": 20},
                "email": {"type": "string", "example": "a@b.c"},
                "city": {"type": "string", "example": "Beijing"},
            },
            "required": ["name"],
        }
    },
}


class TestPropertyCountIntegration:
    def test_fixed_count(self):
        config = BuilderConfig(policies=[FieldPolicy("profile", property_count(2))])
        for _ in range(20):
            result = DataBuilder(OBJECT_SCHEMA, config).build()
            assert len(result["profile"]) == 2
            # required 字段必在
            assert "name" in result["profile"]

    def test_count_zero_with_required(self):
        """count=0 但有 required 字段时，至少生成 required 数量"""
        config = BuilderConfig(policies=[FieldPolicy("profile", property_count(0))])
        result = DataBuilder(OBJECT_SCHEMA, config).build()
        assert "name" in result["profile"]
        assert len(result["profile"]) == 1

    def test_count_exceeds_properties(self):
        """count 超过 properties 数量时，用 additionalProperties 补充"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string", "example": "x"},
                    },
                    "additionalProperties": {"type": "integer", "minimum": 1, "maximum": 1},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("obj", property_count(3))])
        result = DataBuilder(schema, config).build()
        assert len(result["obj"]) == 3
        assert "a" in result["obj"]

    def test_range_count(self):
        config = BuilderConfig(policies=[FieldPolicy("profile", property_count(range_int(2, 4)))])
        for _ in range(30):
            result = DataBuilder(OBJECT_SCHEMA, config).build()
            assert 2 <= len(result["profile"]) <= 4

    def test_all_properties(self):
        """count 等于总属性数时，全部属性都生成"""
        config = BuilderConfig(policies=[FieldPolicy("profile", property_count(4))])
        result = DataBuilder(OBJECT_SCHEMA, config).build()
        assert len(result["profile"]) == 4

    def test_without_property_count_generates_all(self):
        """无策略时所有属性都生成"""
        result = DataBuilder(OBJECT_SCHEMA).build()
        assert len(result["profile"]) == 4


# ── PropertySelectionStrategy 集成测试 ──────────────────────

class TestPropertySelectionIntegration:
    def test_select_subset(self):
        config = BuilderConfig(policies=[FieldPolicy("profile", property_selection(["name", "age"]))])
        result = DataBuilder(OBJECT_SCHEMA, config).build()
        assert set(result["profile"].keys()) == {"name", "age"}

    def test_select_single(self):
        config = BuilderConfig(policies=[FieldPolicy("profile", property_selection(["email"]))])
        result = DataBuilder(OBJECT_SCHEMA, config).build()
        assert set(result["profile"].keys()) == {"email"}

    def test_select_empty(self):
        config = BuilderConfig(policies=[FieldPolicy("profile", property_selection([]))])
        result = DataBuilder(OBJECT_SCHEMA, config).build()
        assert result["profile"] == {}

    def test_select_with_additional_properties(self):
        """选择不在 properties 中定义的名称，用 additionalProperties 生成"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string", "example": "ok"},
                    },
                    "additionalProperties": {"type": "integer", "minimum": 99, "maximum": 99},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("obj", property_selection(["a", "extra_field"]))])
        result = DataBuilder(schema, config).build()
        assert result["obj"]["a"] == "ok"
        assert result["obj"]["extra_field"] == 99

    def test_select_unknown_no_additional_schema_skipped(self):
        """选择不存在的属性且无 additionalProperties 定义时忽略"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {"a": {"type": "string", "example": "ok"}},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("obj", property_selection(["a", "no_such"]))])
        result = DataBuilder(schema, config).build()
        assert set(result["obj"].keys()) == {"a"}

    def test_dynamic_selection_with_callable(self):
        """用 CallableStrategy 动态决定属性列表"""
        config = BuilderConfig(policies=[
            FieldPolicy("profile", property_selection(
                callable_strategy(lambda ctx: ["name", "city"] if ctx.index == 0 else ["age"])
            )),
        ])
        results = DataBuilder(OBJECT_SCHEMA, config).build(count=2)
        assert set(results[0]["profile"].keys()) == {"name", "city"}
        assert set(results[1]["profile"].keys()) == {"age"}


# ── ContainsCountStrategy 集成测试 ──────────────────────────

CONTAINS_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {"type": "string"},
            "contains": {"type": "integer", "minimum": 100, "maximum": 100},
            "minItems": 4,
            "maxItems": 6,
        }
    },
}


class TestContainsCountIntegration:
    def test_fixed_contains_count(self):
        config = BuilderConfig(policies=[FieldPolicy("items", contains_count(2))])
        for _ in range(20):
            result = DataBuilder(CONTAINS_SCHEMA, config).build()
            arr = result["items"]
            int_count = sum(1 for x in arr if isinstance(x, int) and x == 100)
            assert int_count == 2
            assert 4 <= len(arr) <= 6

    def test_contains_count_zero(self):
        """contains_count(0) 时无 contains 元素，全部为 items"""
        config = BuilderConfig(policies=[FieldPolicy("items", contains_count(0))])
        result = DataBuilder(CONTAINS_SCHEMA, config).build()
        arr = result["items"]
        assert all(isinstance(x, str) for x in arr)

    def test_contains_count_equals_total(self):
        """contains_count 等于总长度时全部为 contains 元素"""
        schema = {
            "type": "object",
            "properties": {
                "arr": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "minimum": 7, "maximum": 7},
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("arr", contains_count(3))])
        result = DataBuilder(schema, config).build()
        assert all(x == 7 for x in result["arr"])
        assert len(result["arr"]) == 3

    def test_no_contains_schema_fallback(self):
        """无 contains schema 时 ContainsCountStrategy 作为普通 StructureStrategy 控制数量"""
        schema = {
            "type": "object",
            "properties": {
                "xs": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1, "maximum": 100},
                    "minItems": 1,
                    "maxItems": 10,
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("xs", contains_count(5))])
        result = DataBuilder(schema, config).build()
        # 无 contains，退化为 StructureStrategy 控制总数量
        assert len(result["xs"]) == 5


# ── SchemaSelectionStrategy 集成测试 ─────────────────────────

class TestSchemaSelectionIntegration:
    def test_select_oneof_first_branch(self):
        schema = {
            "type": "object",
            "properties": {
                "payment": {
                    "oneOf": [
                        {"type": "object", "properties": {"card": {"type": "string", "const": "visa"}}},
                        {"type": "object", "properties": {"alipay": {"type": "string", "const": "ali"}}},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("payment", schema_selection(0))])
        for _ in range(10):
            result = DataBuilder(schema, config).build()
            assert "card" in result["payment"]
            assert result["payment"]["card"] == "visa"

    def test_select_oneof_second_branch(self):
        schema = {
            "type": "object",
            "properties": {
                "payment": {
                    "oneOf": [
                        {"type": "object", "properties": {"card": {"type": "string", "const": "visa"}}},
                        {"type": "object", "properties": {"alipay": {"type": "string", "const": "ali"}}},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("payment", schema_selection(1))])
        for _ in range(10):
            result = DataBuilder(schema, config).build()
            assert "alipay" in result["payment"]

    def test_select_anyof(self):
        schema = {
            "type": "object",
            "properties": {
                "val": {
                    "anyOf": [
                        {"type": "string", "const": "A"},
                        {"type": "string", "const": "B"},
                        {"type": "string", "const": "C"},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("val", schema_selection(2))])
        for _ in range(10):
            result = DataBuilder(schema, config).build()
            assert result["val"] == "C"

    def test_index_clamped_to_max(self):
        """索引超出范围时 clamp 到最后一个分支"""
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "oneOf": [
                        {"type": "string", "const": "first"},
                        {"type": "string", "const": "last"},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("v", schema_selection(99))])
        result = DataBuilder(schema, config).build()
        assert result["v"] == "last"

    def test_negative_index_clamped_to_zero(self):
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "oneOf": [
                        {"type": "string", "const": "first"},
                        {"type": "string", "const": "last"},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("v", schema_selection(-5))])
        result = DataBuilder(schema, config).build()
        assert result["v"] == "first"

    def test_no_oneof_anyof_fallthrough(self):
        """无 oneOf/anyOf 时 fall through 到默认生成"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("name", schema_selection(0))])
        result = DataBuilder(schema, config).build()
        assert isinstance(result["name"], str)

    def test_dynamic_branch_with_callable(self):
        """用 CallableStrategy 动态选择分支"""
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
        config = BuilderConfig(
            count=4,
            policies=[FieldPolicy("v", schema_selection(
                callable_strategy(lambda ctx: ctx.index % 2)
            ))],
        )
        results = DataBuilder(schema, config).build()
        assert results[0]["v"] == "A"
        assert results[1]["v"] == "B"
        assert results[2]["v"] == "A"
        assert results[3]["v"] == "B"


# ── 策略共存测试 ────────────────────────────────────────────

class TestStrategyCoexistence:
    def test_property_count_and_array_count_coexist(self):
        """PropertyCountStrategy 和 ArrayCountStrategy 绑定不同字段"""
        from data_builder import array_count
        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "example": "test"},
                        "age": {"type": "integer", "minimum": 1, "maximum": 1},
                        "email": {"type": "string", "example": "e@e.e"},
                    },
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 10,
                },
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("profile", property_count(2)),
            FieldPolicy("tags", array_count(3)),
        ])
        result = DataBuilder(schema, config).build()
        assert len(result["profile"]) == 2
        assert len(result["tags"]) == 3

    def test_schema_selection_with_property_selection(self):
        """SchemaSelectionStrategy 和 PropertySelectionStrategy 绑定不同字段"""
        schema = {
            "type": "object",
            "properties": {
                "mode": {
                    "oneOf": [
                        {"type": "string", "const": "fast"},
                        {"type": "string", "const": "slow"},
                    ]
                },
                "config": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "minimum": 1, "maximum": 1},
                        "b": {"type": "integer", "minimum": 2, "maximum": 2},
                        "c": {"type": "integer", "minimum": 3, "maximum": 3},
                    },
                },
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("mode", schema_selection(0)),
            FieldPolicy("config", property_selection(["a", "c"])),
        ])
        result = DataBuilder(schema, config).build()
        assert result["mode"] == "fast"
        assert set(result["config"].keys()) == {"a", "c"}

    def test_contains_count_and_prefix_items_independent(self):
        """ContainsCountStrategy 和 prefixItems 作用于不同字段互不干扰"""
        schema = {
            "type": "object",
            "properties": {
                "tuple_field": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "head"},
                    ],
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "contains_field": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "minimum": 42, "maximum": 42},
                    "minItems": 3,
                    "maxItems": 5,
                },
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("contains_field", contains_count(2)),
        ])
        result = DataBuilder(schema, config).build()
        # tuple_field 正常用 prefixItems
        assert result["tuple_field"][0] == "head"
        assert len(result["tuple_field"]) == 2
        # contains_field 有 2 个 contains 元素
        int_count = sum(1 for x in result["contains_field"] if isinstance(x, int) and x == 42)
        assert int_count == 2
