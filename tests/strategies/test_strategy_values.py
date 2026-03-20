"""策略值域方法测试：values / boundary_values / equivalence_classes"""

from data_builder import (
    FixedStrategy,
    EnumStrategy,
    RangeStrategy,
    RandomStringStrategy,
    FakerStrategy,
    StrategyContext,
)


def _ctx(**kwargs):
    defaults = dict(field_path="x", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


# ── FixedStrategy ──────────────────────────────────────────────


class TestFixedValues:
    def test_values(self):
        assert FixedStrategy(42).values() == [42]

    def test_values_none(self):
        assert FixedStrategy(None).values() == [None]

    def test_boundary_values(self):
        assert FixedStrategy("x").boundary_values() == ["x"]

    def test_equivalence_classes(self):
        assert FixedStrategy(1).equivalence_classes() == [[1]]


# ── EnumStrategy ───────────────────────────────────────────────


class TestEnumValues:
    def test_values_returns_all_choices(self):
        s = EnumStrategy(["a", "b", "c"])
        assert s.values() == ["a", "b", "c"]

    def test_values_is_copy(self):
        """返回的列表不应是内部引用"""
        choices = ["a", "b"]
        s = EnumStrategy(choices)
        result = s.values()
        result.append("z")
        assert s.values() == ["a", "b"]

    def test_boundary_values_single(self):
        s = EnumStrategy(["only"])
        assert s.boundary_values() == ["only"]

    def test_boundary_values_multiple(self):
        s = EnumStrategy(["first", "mid", "last"])
        assert s.boundary_values() == ["first", "last"]

    def test_boundary_values_empty(self):
        s = EnumStrategy([])
        assert s.boundary_values() is None

    def test_equivalence_classes(self):
        s = EnumStrategy([1, 2, 3])
        assert s.equivalence_classes() == [[1], [2], [3]]


# ── RangeStrategy 整数 ─────────────────────────────────────────


class TestRangeIntValues:
    def test_values_small_range(self):
        s = RangeStrategy(1, 5, is_float=False)
        assert s.values() == [1, 2, 3, 4, 5]

    def test_values_single(self):
        s = RangeStrategy(3, 3, is_float=False)
        assert s.values() == [3]

    def test_values_large_range_returns_none(self):
        s = RangeStrategy(0, 2000, is_float=False)
        assert s.values() is None

    def test_values_exactly_1000(self):
        """范围恰好 1000 个值时应返回列表"""
        s = RangeStrategy(1, 1000, is_float=False)
        result = s.values()
        assert result is not None
        assert len(result) == 1000

    def test_values_1001_returns_none(self):
        s = RangeStrategy(0, 1000, is_float=False)
        assert s.values() is None

    def test_boundary_values_normal(self):
        s = RangeStrategy(1, 10, is_float=False)
        assert s.boundary_values() == [1, 2, 9, 10]

    def test_boundary_values_small_range(self):
        """min=1, max=2 时 [1,2,1,2] 去重为 [1,2]"""
        s = RangeStrategy(1, 2, is_float=False)
        assert s.boundary_values() == [1, 2]

    def test_boundary_values_single(self):
        s = RangeStrategy(5, 5, is_float=False)
        assert s.boundary_values() == [5]

    def test_equivalence_classes(self):
        s = RangeStrategy(0, 100, is_float=False)
        classes = s.equivalence_classes()
        assert classes == [[0], [50], [100]]

    def test_equivalence_classes_odd_range(self):
        s = RangeStrategy(1, 10, is_float=False)
        classes = s.equivalence_classes()
        assert classes == [[1], [5], [10]]


# ── RangeStrategy 浮点 ─────────────────────────────────────────


class TestRangeFloatValues:
    def test_values_returns_none(self):
        s = RangeStrategy(0.0, 1.0, is_float=True)
        assert s.values() is None

    def test_boundary_values(self):
        s = RangeStrategy(0.5, 9.5, is_float=True)
        assert s.boundary_values() == [0.5, 0.51, 9.49, 9.5]

    def test_equivalence_classes(self):
        s = RangeStrategy(0.0, 10.0, is_float=True)
        classes = s.equivalence_classes()
        assert classes == [[0.0], [5.0], [10.0]]


# ── 不支持值域的策略 ───────────────────────────────────────────


class TestUnsupportedValues:
    def test_random_string_values_none(self):
        s = RandomStringStrategy(length=5)
        assert s.values() is None
        assert s.boundary_values() is not None
        assert s.equivalence_classes() is not None

    def test_faker_values_none(self):
        s = FakerStrategy(method="name")
        assert s.values() is None
        assert s.boundary_values() is None
        assert s.equivalence_classes() is None
