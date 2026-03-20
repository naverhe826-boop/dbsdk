import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, fixed


class TestBuilderConfigCount:
    def test_config_count_returns_list(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(count=5)
        result = DataBuilder(schema, config).build()
        assert isinstance(result, list)
        assert len(result) == 5

    def test_config_count_zero_returns_empty_list(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(count=0)
        result = DataBuilder(schema, config).build()
        assert result == []

    def test_explicit_count_overrides_config(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(count=100)
        result = DataBuilder(schema, config).build(count=3)
        assert len(result) == 3

    def test_no_count_returns_single_dict(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        result = DataBuilder(schema).build()
        assert isinstance(result, dict)

    def test_config_count_none_explicit_count_works(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(count=None)
        result = DataBuilder(schema, config).build(count=7)
        assert len(result) == 7

    def test_config_count_with_policies(self):
        schema = {"type": "object", "properties": {"v": {"type": "integer"}}}
        config = BuilderConfig(count=10, policies=[FieldPolicy("v", fixed(42))])
        result = DataBuilder(schema, config).build()
        assert len(result) == 10
        assert all(r["v"] == 42 for r in result)
