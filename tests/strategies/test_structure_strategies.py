import pytest
from data_builder import (
    Strategy, StructureStrategy, StrategyContext,
    PropertyCountStrategy, PropertySelectionStrategy,
    ContainsCountStrategy, SchemaSelectionStrategy,
    property_count, property_selection, contains_count, schema_selection,
    fixed, range_int, callable_strategy,
)


def _ctx(**kwargs):
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


# ── PropertyCountStrategy 单元测试 ──────────────────────────

class TestPropertyCountStrategyHierarchy:
    def test_is_subclass_of_structure_strategy(self):
        assert issubclass(PropertyCountStrategy, StructureStrategy)

    def test_is_subclass_of_strategy(self):
        assert issubclass(PropertyCountStrategy, Strategy)


class TestPropertyCountStrategy:
    def test_int_source(self):
        s = PropertyCountStrategy(3)
        assert s.generate(_ctx()) == 3

    def test_strategy_source(self):
        s = PropertyCountStrategy(fixed(5))
        assert s.generate(_ctx()) == 5

    def test_zero(self):
        s = PropertyCountStrategy(0)
        assert s.generate(_ctx()) == 0

    def test_negative_clamped_to_zero(self):
        s = PropertyCountStrategy(fixed(-3))
        assert s.generate(_ctx()) == 0

    def test_float_truncated(self):
        s = PropertyCountStrategy(fixed(2.9))
        assert s.generate(_ctx()) == 2

    def test_range_strategy_source(self):
        s = PropertyCountStrategy(range_int(1, 4))
        for _ in range(30):
            v = s.generate(_ctx())
            assert 1 <= v <= 4

    def test_callable_source(self):
        s = PropertyCountStrategy(callable_strategy(lambda ctx: ctx.index + 2))
        assert s.generate(_ctx(index=0)) == 2
        assert s.generate(_ctx(index=3)) == 5


class TestPropertyCountFactory:
    def test_int_arg(self):
        s = property_count(3)
        assert isinstance(s, PropertyCountStrategy)
        assert s.generate(_ctx()) == 3

    def test_strategy_arg(self):
        s = property_count(fixed(7))
        assert isinstance(s, PropertyCountStrategy)
        assert s.generate(_ctx()) == 7


# ── PropertySelectionStrategy 单元测试 ──────────────────────

class TestPropertySelectionStrategyHierarchy:
    def test_is_subclass_of_structure_strategy(self):
        assert issubclass(PropertySelectionStrategy, StructureStrategy)


class TestPropertySelectionStrategy:
    def test_list_source(self):
        s = PropertySelectionStrategy(["a", "b"])
        assert s.generate(_ctx()) == ["a", "b"]

    def test_strategy_source(self):
        s = PropertySelectionStrategy(fixed(["x", "y", "z"]))
        assert s.generate(_ctx()) == ["x", "y", "z"]

    def test_empty_list(self):
        s = PropertySelectionStrategy([])
        assert s.generate(_ctx()) == []


class TestPropertySelectionFactory:
    def test_list_arg(self):
        s = property_selection(["a"])
        assert isinstance(s, PropertySelectionStrategy)
        assert s.generate(_ctx()) == ["a"]

    def test_strategy_arg(self):
        s = property_selection(fixed(["x"]))
        assert isinstance(s, PropertySelectionStrategy)


# ── ContainsCountStrategy 单元测试 ──────────────────────────

class TestContainsCountStrategyHierarchy:
    def test_is_subclass_of_structure_strategy(self):
        assert issubclass(ContainsCountStrategy, StructureStrategy)


class TestContainsCountStrategy:
    def test_int_source(self):
        s = ContainsCountStrategy(2)
        assert s.generate(_ctx()) == 2

    def test_strategy_source(self):
        s = ContainsCountStrategy(fixed(4))
        assert s.generate(_ctx()) == 4

    def test_zero(self):
        s = ContainsCountStrategy(0)
        assert s.generate(_ctx()) == 0

    def test_negative_clamped_to_zero(self):
        s = ContainsCountStrategy(fixed(-5))
        assert s.generate(_ctx()) == 0

    def test_float_truncated(self):
        s = ContainsCountStrategy(fixed(3.7))
        assert s.generate(_ctx()) == 3


class TestContainsCountFactory:
    def test_int_arg(self):
        s = contains_count(2)
        assert isinstance(s, ContainsCountStrategy)
        assert s.generate(_ctx()) == 2

    def test_strategy_arg(self):
        s = contains_count(fixed(5))
        assert isinstance(s, ContainsCountStrategy)


# ── SchemaSelectionStrategy 单元测试 ────────────────────────

class TestSchemaSelectionStrategyHierarchy:
    def test_is_subclass_of_structure_strategy(self):
        assert issubclass(SchemaSelectionStrategy, StructureStrategy)


class TestSchemaSelectionStrategy:
    def test_int_source(self):
        s = SchemaSelectionStrategy(0)
        assert s.generate(_ctx()) == 0

    def test_strategy_source(self):
        s = SchemaSelectionStrategy(fixed(1))
        assert s.generate(_ctx()) == 1

    def test_negative_index(self):
        s = SchemaSelectionStrategy(fixed(-1))
        assert s.generate(_ctx()) == -1  # clamp 由 builder 负责


class TestSchemaSelectionFactory:
    def test_int_arg(self):
        s = schema_selection(0)
        assert isinstance(s, SchemaSelectionStrategy)
        assert s.generate(_ctx()) == 0

    def test_strategy_arg(self):
        s = schema_selection(fixed(2))
        assert isinstance(s, SchemaSelectionStrategy)
