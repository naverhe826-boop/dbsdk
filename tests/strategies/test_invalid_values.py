"""策略 invalid_values() 接口测试"""

import pytest
from datetime import datetime, timedelta

from data_builder import (
    FixedStrategy,
    EnumStrategy,
    RangeStrategy,
    RandomStringStrategy,
    DateTimeStrategy,
    FakerStrategy,
    SchemaAwareStrategy,
    StrategyContext,
)


def _ctx(**kwargs):
    defaults = dict(field_path="x", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


# ── RangeStrategy invalid_values ──────────────────────────────


class TestRangeInvalidValues:
    def test_int_invalid(self):
        s = RangeStrategy(1, 100, is_float=False)
        inv = s.invalid_values()
        assert inv == [0, 101, "not_a_number", None]

    def test_int_invalid_zero_based(self):
        s = RangeStrategy(0, 10, is_float=False)
        inv = s.invalid_values()
        assert inv[0] == -1
        assert inv[1] == 11

    def test_float_invalid(self):
        s = RangeStrategy(0.0, 1.0, is_float=True, precision=2)
        inv = s.invalid_values()
        assert inv[0] == -0.01
        assert inv[1] == 1.01
        assert inv[2] == "not_a_number"
        assert inv[3] is None

    def test_float_invalid_precision_3(self):
        s = RangeStrategy(0.0, 1.0, is_float=True, precision=3)
        inv = s.invalid_values()
        assert inv[0] == -0.001
        assert inv[1] == 1.001

    def test_int_single_value(self):
        """min==max 时非法值仍正确"""
        s = RangeStrategy(5, 5, is_float=False)
        inv = s.invalid_values()
        assert 4 in inv
        assert 6 in inv


# ── RangeStrategy 浮点 boundary_values 增强 ───────────────────


class TestRangeFloatBoundaryEnhanced:
    def test_precision_1(self):
        s = RangeStrategy(1.0, 10.0, is_float=True, precision=1)
        bv = s.boundary_values()
        assert bv == [1.0, 1.1, 9.9, 10.0]

    def test_precision_3(self):
        s = RangeStrategy(0.0, 1.0, is_float=True, precision=3)
        bv = s.boundary_values()
        assert bv == [0.0, 0.001, 0.999, 1.0]

    def test_float_single_value(self):
        """min==max 时去重"""
        s = RangeStrategy(5.0, 5.0, is_float=True, precision=2)
        bv = s.boundary_values()
        assert bv == [5.0]

    def test_float_tiny_range(self):
        """范围极小时边界值去重"""
        s = RangeStrategy(1.0, 1.01, is_float=True, precision=2)
        bv = s.boundary_values()
        assert 1.0 in bv
        assert 1.01 in bv


# ── RandomStringStrategy 值域接口 ─────────────────────────────


class TestRandomStringBoundary:
    def test_normal_length(self):
        s = RandomStringStrategy(length=10)
        bv = s.boundary_values()
        assert len(bv) == 2
        assert len(bv[0]) == 1
        assert len(bv[1]) == 10

    def test_length_zero(self):
        s = RandomStringStrategy(length=0)
        bv = s.boundary_values()
        assert bv == [""]

    def test_length_one(self):
        s = RandomStringStrategy(length=1)
        bv = s.boundary_values()
        assert len(bv) == 2
        assert len(bv[0]) == 1
        assert len(bv[1]) == 1


class TestRandomStringEquivalence:
    def test_alpha_digits_charset(self):
        """默认 charset 有字母和数字，应产生 3 个等价类"""
        s = RandomStringStrategy(length=5)
        classes = s.equivalence_classes()
        assert len(classes) == 3  # 纯字母、纯数字、混合

    def test_digits_only_charset(self):
        s = RandomStringStrategy(length=5, charset="0123456789")
        classes = s.equivalence_classes()
        # 只有数字，1 个等价类
        assert len(classes) == 1
        assert classes[0][0].isdigit()

    def test_alpha_only_charset(self):
        s = RandomStringStrategy(length=5, charset="abcdef")
        classes = s.equivalence_classes()
        assert len(classes) == 1
        assert classes[0][0].isalpha()

    def test_special_charset(self):
        """无字母无数字的 charset"""
        s = RandomStringStrategy(length=3, charset="!@#$%")
        classes = s.equivalence_classes()
        assert len(classes) == 1


class TestRandomStringInvalid:
    def test_returns_four_items(self):
        s = RandomStringStrategy(length=5)
        inv = s.invalid_values()
        assert len(inv) == 4
        assert inv[0] == ""
        assert len(inv[1]) == 105  # length + 100
        assert inv[2] == 12345
        assert inv[3] is None


# ── DateTimeStrategy 值域接口 ──────────────────────────────────


class TestDateTimeBoundary:
    def test_normal_range(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        s = DateTimeStrategy(start=start, end=end)
        bv = s.boundary_values()
        assert bv[0] == "2024-01-01 00:00:00"
        assert bv[-1] == "2024-12-31 00:00:00"
        assert len(bv) == 4

    def test_same_start_end(self):
        """start==end 时边界值去重"""
        t = datetime(2024, 6, 15, 12, 0, 0)
        s = DateTimeStrategy(start=t, end=t)
        bv = s.boundary_values()
        assert len(bv) == 1
        assert bv[0] == "2024-06-15 12:00:00"

    def test_one_second_range(self):
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 0, 0, 1)
        s = DateTimeStrategy(start=start, end=end)
        bv = s.boundary_values()
        assert len(bv) == 2


class TestDateTimeEquivalence:
    def test_three_classes(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        s = DateTimeStrategy(start=start, end=end)
        classes = s.equivalence_classes()
        assert len(classes) == 3
        assert classes[0] == ["2024-01-01 00:00:00"]
        assert classes[2] == ["2024-12-31 00:00:00"]


class TestDateTimeInvalid:
    def test_returns_five_items(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        s = DateTimeStrategy(start=start, end=end)
        inv = s.invalid_values()
        assert len(inv) == 5
        assert inv[0] == "2023-12-31 00:00:00"
        assert inv[1] == "2025-01-01 00:00:00"
        assert inv[2] == "not-a-date"
        assert inv[3] == 12345
        assert inv[4] is None


# ── EnumStrategy invalid_values ───────────────────────────────


class TestEnumInvalidValues:
    def test_string_choices(self):
        s = EnumStrategy(["a", "b", "c"])
        inv = s.invalid_values()
        assert len(inv) == 2
        assert inv[0] not in ["a", "b", "c"]
        assert inv[1] is None

    def test_numeric_choices(self):
        s = EnumStrategy([1, 2, 3])
        inv = s.invalid_values()
        assert inv[0] not in [1, 2, 3]
        assert isinstance(inv[0], (int, float))
        assert inv[1] is None

    def test_mixed_choices(self):
        s = EnumStrategy([1, "a", True])
        inv = s.invalid_values()
        assert len(inv) == 2


# ── FixedStrategy invalid_values ──────────────────────────────


class TestFixedInvalidValues:
    def test_string_value(self):
        inv = FixedStrategy("hello").invalid_values()
        assert inv[0] == 12345  # 类型不匹配
        assert inv[1] is None

    def test_int_value(self):
        inv = FixedStrategy(42).invalid_values()
        assert inv[0] == "not_a_number"
        assert inv[1] is None

    def test_bool_value(self):
        inv = FixedStrategy(True).invalid_values()
        assert inv[0] == "not_bool"
        assert inv[1] is None

    def test_none_value(self):
        inv = FixedStrategy(None).invalid_values()
        assert len(inv) == 2


# ── 不支持 invalid_values 的策略 ──────────────────────────────


class TestUnsupportedInvalid:
    def test_faker_invalid_values(self):
        s = FakerStrategy(method="name")
        # FakerStrategy 依赖外部库，无法预知值域，但可以提供非法值测试用例
        invalid = s.invalid_values()
        assert invalid is not None
        assert isinstance(invalid, list)
        assert 12345 in invalid  # 类型错误：数字
        assert None in invalid   # 空值
