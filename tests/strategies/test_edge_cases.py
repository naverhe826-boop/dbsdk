"""异常路径测试：RefStrategy / EnumStrategy / DateTimeStrategy"""
import pytest
from datetime import datetime

from data_builder import (
    RefStrategy, EnumStrategy, DateTimeStrategy,
    StrategyContext, StrategyError, FieldPathError,
)


def _ctx(**kwargs):
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


# ------------------------------------------------------------------
# RefStrategy 引用不存在路径
# ------------------------------------------------------------------
class TestRefStrategyPathErrors:
    def test_top_level_missing_key(self):
        s = RefStrategy("missing")
        with pytest.raises(FieldPathError, match="missing"):
            s.generate(_ctx(root_data={"other": 1}))

    def test_nested_missing_key(self):
        s = RefStrategy("a.b.c")
        with pytest.raises(FieldPathError, match="c"):
            s.generate(_ctx(root_data={"a": {"b": {"x": 1}}}))

    def test_array_index_out_of_range(self):
        s = RefStrategy("items[10]")
        with pytest.raises(FieldPathError):
            s.generate(_ctx(root_data={"items": [1, 2]}))

    def test_traverse_into_non_dict(self):
        s = RefStrategy("a.b")
        with pytest.raises(FieldPathError):
            s.generate(_ctx(root_data={"a": 42}))

    def test_empty_root_data(self):
        s = RefStrategy("x")
        with pytest.raises(FieldPathError):
            s.generate(_ctx(root_data={}))


# ------------------------------------------------------------------
# EnumStrategy 空列表
# ------------------------------------------------------------------
class TestEnumStrategyEmpty:
    def test_generate_empty_raises(self):
        s = EnumStrategy([])
        with pytest.raises(StrategyError, match="choices"):
            s.generate(_ctx())

    def test_construct_empty_ok(self):
        """构造时不报错，generate 时才报错"""
        s = EnumStrategy([])
        assert s.choices == []

    def test_boundary_values_empty(self):
        s = EnumStrategy([])
        assert s.boundary_values() is None


# ------------------------------------------------------------------
# DateTimeStrategy start > end
# ------------------------------------------------------------------
class TestDateTimeStrategyInvalid:
    def test_start_after_end_raises(self):
        s = DateTimeStrategy(start=datetime(2025, 6, 1), end=datetime(2020, 1, 1))
        with pytest.raises(StrategyError, match="start"):
            s.generate(_ctx())

    def test_start_equals_end_ok(self):
        dt = datetime(2025, 1, 1, 12, 0, 0)
        s = DateTimeStrategy(start=dt, end=dt, format="%Y-%m-%d")
        result = s.generate(_ctx())
        assert result == "2025-01-01"
