import pytest
from data_builder import (
    Strategy, StructureStrategy,
    ArrayCountStrategy, StrategyContext,
    array_count, fixed, range_int, callable_strategy,
)


def _ctx(**kwargs):
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestStructureStrategyHierarchy:
    def test_structure_strategy_is_subclass_of_strategy(self):
        assert issubclass(StructureStrategy, Strategy)

    def test_array_count_is_subclass_of_structure_strategy(self):
        assert issubclass(ArrayCountStrategy, StructureStrategy)

    def test_array_count_is_still_subclass_of_strategy(self):
        assert issubclass(ArrayCountStrategy, Strategy)

    def test_custom_structure_strategy_isinstance(self):
        class MyStructure(StructureStrategy):
            def generate(self, ctx):
                return 1

        s = MyStructure()
        assert isinstance(s, StructureStrategy)
        assert isinstance(s, Strategy)


class TestArrayCountStrategy:
    def test_int_source(self):
        s = ArrayCountStrategy(3)
        assert s.generate(_ctx()) == 3

    def test_strategy_source(self):
        s = ArrayCountStrategy(fixed(5))
        assert s.generate(_ctx()) == 5

    def test_zero(self):
        s = ArrayCountStrategy(0)
        assert s.generate(_ctx()) == 0

    def test_negative_clamped_to_zero(self):
        s = ArrayCountStrategy(fixed(-1))
        assert s.generate(_ctx()) == 0

    def test_float_truncated(self):
        s = ArrayCountStrategy(fixed(3.9))
        assert s.generate(_ctx()) == 3

    def test_range_strategy_source(self):
        s = ArrayCountStrategy(range_int(2, 5))
        for _ in range(30):
            v = s.generate(_ctx())
            assert 2 <= v <= 5

    def test_callable_source(self):
        s = ArrayCountStrategy(callable_strategy(lambda ctx: ctx.index + 1))
        assert s.generate(_ctx(index=0)) == 1
        assert s.generate(_ctx(index=4)) == 5


class TestArrayCountFactory:
    def test_int_arg(self):
        s = array_count(3)
        assert isinstance(s, ArrayCountStrategy)
        assert s.generate(_ctx()) == 3

    def test_strategy_arg(self):
        s = array_count(fixed(7))
        assert isinstance(s, ArrayCountStrategy)
        assert s.generate(_ctx()) == 7
