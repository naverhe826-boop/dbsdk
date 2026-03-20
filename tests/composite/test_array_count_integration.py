import pytest
from data_builder import (
    DataBuilder, BuilderConfig, FieldPolicy,
    StructureStrategy, StrategyContext,
    array_count, range_int, callable_strategy, fixed,
)


ARRAY_SCHEMA = {
    "type": "object",
    "properties": {
        "orders": {
            "type": "array",
            "items": {"type": "object", "properties": {"id": {"type": "integer"}}},
            "minItems": 1,
            "maxItems": 10,
        }
    },
}


class TestArrayCountIntegration:
    def test_fixed_count_overrides_min_max(self):
        config = BuilderConfig(policies=[FieldPolicy("orders", array_count(3))])
        for _ in range(20):
            result = DataBuilder(ARRAY_SCHEMA, config).build()
            assert len(result["orders"]) == 3

    def test_fixed_count_zero_produces_empty_array(self):
        config = BuilderConfig(policies=[FieldPolicy("orders", array_count(0))])
        result = DataBuilder(ARRAY_SCHEMA, config).build()
        assert result["orders"] == []

    def test_range_count_stays_in_bounds(self):
        config = BuilderConfig(policies=[FieldPolicy("orders", array_count(range_int(2, 4)))])
        for _ in range(30):
            result = DataBuilder(ARRAY_SCHEMA, config).build()
            assert 2 <= len(result["orders"]) <= 4

    def test_callable_count_uses_index(self):
        config = BuilderConfig(
            count=3,
            policies=[FieldPolicy("orders", array_count(callable_strategy(lambda ctx: ctx.index + 1)))],
        )
        results = DataBuilder(ARRAY_SCHEMA, config).build()
        # index 0 → 1 条，index 1 → 2 条，index 2 → 3 条
        assert len(results[0]["orders"]) == 1
        assert len(results[1]["orders"]) == 2
        assert len(results[2]["orders"]) == 3

    def test_without_array_count_uses_schema_min_max(self):
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                }
            },
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            assert len(result["items"]) == 2

    def test_array_items_are_generated_correctly(self):
        config = BuilderConfig(policies=[FieldPolicy("orders", array_count(2))])
        result = DataBuilder(ARRAY_SCHEMA, config).build()
        assert len(result["orders"]) == 2
        for item in result["orders"]:
            assert "id" in item
            assert isinstance(item["id"], int)


class TestStructureStrategyRouting:
    """验证 builder 对 StructureStrategy 的分发路由"""

    def test_custom_structure_strategy_on_array(self):
        """自定义 StructureStrategy 子类绑定到 array 字段"""
        class FixedCount(StructureStrategy):
            def generate(self, ctx):
                return 4

        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 1}
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("tags", FixedCount())])
        result = DataBuilder(schema, config).build()
        assert len(result["tags"]) == 4

    def test_structure_strategy_on_object_passes_strategy(self):
        """StructureStrategy 绑定到 object 字段时走 _generate_object 路由，
        当前 _generate_object 不消费 strategy 参数，对象按默认逻辑生成"""
        class ObjectMarker(StructureStrategy):
            def generate(self, ctx):
                return {}

        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("profile", ObjectMarker())])
        result = DataBuilder(schema, config).build()
        # object 按默认逻辑生成，properties 正常展开
        assert "name" in result["profile"]
        assert isinstance(result["profile"]["name"], str)

    def test_structure_strategy_on_primitive_falls_through(self):
        """StructureStrategy 绑定到基础类型时，StructureStrategy 分支不处理，
        fall through 到默认值生成"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 5, "maxLength": 5},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("name", array_count(3))])
        result = DataBuilder(schema, config).build()
        # fall through 到默认 string 生成
        assert isinstance(result["name"], str)

    def test_value_strategy_on_array_returns_strategy_value(self):
        """值策略绑定到 array 类型字段时，直接返回策略值（不走 _generate_array）"""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("tags", fixed(["a", "b"]))])
        result = DataBuilder(schema, config).build()
        assert result["tags"] == ["a", "b"]

    def test_array_count_with_wildcard_path(self):
        """通配符路径绑定 StructureStrategy"""
        schema = {
            "type": "object",
            "properties": {
                "group": {
                    "type": "object",
                    "properties": {
                        "items_a": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "maxItems": 10},
                        "items_b": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "maxItems": 10},
                    },
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("group.*", array_count(2))])
        result = DataBuilder(schema, config).build()
        assert len(result["group"]["items_a"]) == 2
        assert len(result["group"]["items_b"]) == 2
