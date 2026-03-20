import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, seq, enum


class TestBulkCount:
    def test_build_returns_correct_count(self, nested_order_schema):
        results = DataBuilder(nested_order_schema).build(count=1000)
        assert len(results) == 1000

    def test_all_items_are_dicts(self, nested_order_schema):
        results = DataBuilder(nested_order_schema).build(count=1000)
        assert all(isinstance(r, dict) for r in results)


class TestBulkSeqStrategy:
    def test_seq_continuous_no_duplicates(self):
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        config = BuilderConfig(policies=[FieldPolicy("id", seq(start=1))])
        results = DataBuilder(schema, config).build(count=1000)
        ids = [r["id"] for r in results]
        assert ids == list(range(1, 1001))
        assert len(set(ids)) == 1000


class TestBulkEnumCoverage:
    def test_enum_covers_all_options(self):
        choices = ["a", "b", "c", "d"]
        schema = {"type": "object", "properties": {"v": {"type": "string"}}}
        config = BuilderConfig(policies=[FieldPolicy("v", enum(choices))])
        results = DataBuilder(schema, config).build(count=1000)
        found = {r["v"] for r in results}
        assert found == set(choices)


class TestBulkNested:
    def test_nested_schema_no_exception(self, nested_order_schema):
        results = DataBuilder(nested_order_schema).build(count=1000)
        assert len(results) == 1000

    def test_complex_schema_completes(self):
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "active": {"type": "boolean"},
                                        },
                                    },
                                    "minItems": 3,
                                    "maxItems": 5,
                                }
                            },
                        }
                    },
                }
            },
        }
        results = DataBuilder(schema).build(count=1000)
        assert len(results) == 1000
        assert all(isinstance(r["level1"]["level2"]["items"], list) for r in results)


class TestStrictMode:
    def test_strict_mode_raises_on_missing_strategy(self):
        from data_builder.exceptions import StrategyNotFoundError
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        config = BuilderConfig(strict_mode=True)
        with pytest.raises(StrategyNotFoundError):
            DataBuilder(schema, config).build()

    def test_strict_mode_false_no_raise(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        config = BuilderConfig(strict_mode=False)
        result = DataBuilder(schema, config).build()
        assert "name" in result


class TestPostFilterExhausted:
    def test_single_build_all_filtered_returns_none(self):
        from data_builder.filters import constraint_filter
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(post_filters=[constraint_filter(lambda r: False)])
        result = DataBuilder(schema, config).build()
        assert result is None
