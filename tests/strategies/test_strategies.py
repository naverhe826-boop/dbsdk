import pytest
from datetime import datetime
from data_builder import (
    DataBuilder, BuilderConfig, FieldPolicy,
    FixedStrategy, RandomStringStrategy, RangeStrategy, EnumStrategy,
    RegexStrategy, SequenceStrategy, FakerStrategy, CallableStrategy,
    RefStrategy, DateTimeStrategy,
    StrategyContext,
    StrategyError, StrategyNotFoundError, FieldPathError,
)


def _ctx(**kwargs):
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestFixedStrategy:
    def test_int(self):
        assert FixedStrategy(42).generate(_ctx()) == 42

    def test_str(self):
        assert FixedStrategy("hello").generate(_ctx()) == "hello"

    def test_dict(self):
        v = {"a": 1}
        assert FixedStrategy(v).generate(_ctx()) == v

    def test_list(self):
        v = [1, 2, 3]
        assert FixedStrategy(v).generate(_ctx()) == v

    def test_none(self):
        assert FixedStrategy(None).generate(_ctx()) is None


class TestRandomStringStrategy:
    def test_default_length(self):
        val = RandomStringStrategy().generate(_ctx())
        assert isinstance(val, str)
        assert len(val) == 10

    def test_custom_length(self):
        val = RandomStringStrategy(length=5).generate(_ctx())
        assert len(val) == 5

    def test_custom_charset(self):
        val = RandomStringStrategy(length=20, charset="abc").generate(_ctx())
        assert all(c in "abc" for c in val)

    def test_values_enumerable(self):
        """values: 可枚举情况 (length=2, charset='ab' -> 2^2=4)"""
        s = RandomStringStrategy(length=2, charset="ab")
        vals = s.values()
        assert vals is not None
        assert len(vals) == 4
        assert "aa" in vals
        assert "ab" in vals
        assert "ba" in vals
        assert "bb" in vals

    def test_values_not_enumerable(self):
        """values: 不可枚举情况 (默认参数，组合数远大于1000)"""
        s = RandomStringStrategy()
        vals = s.values()
        assert vals is None


class TestRangeStrategy:
    def test_integer_range(self):
        s = RangeStrategy(min_val=1, max_val=5, is_float=False)
        for _ in range(30):
            v = s.generate(_ctx())
            assert isinstance(v, int)
            assert 1 <= v <= 5

    def test_float_range(self):
        s = RangeStrategy(min_val=0.0, max_val=1.0, is_float=True, precision=2)
        for _ in range(20):
            v = s.generate(_ctx())
            assert isinstance(v, float)
            assert 0.0 <= v <= 1.0

    def test_precision(self):
        s = RangeStrategy(min_val=0.0, max_val=100.0, is_float=True, precision=3)
        v = s.generate(_ctx())
        assert len(str(v).split(".")[-1]) <= 3

    def test_min_equals_max(self):
        s = RangeStrategy(min_val=7, max_val=7, is_float=False)
        assert s.generate(_ctx()) == 7


class TestEnumStrategy:
    def test_no_weights(self):
        choices = ["a", "b", "c"]
        s = EnumStrategy(choices=choices)
        for _ in range(30):
            assert s.generate(_ctx()) in choices

    def test_weighted_bias(self):
        # weight 极端偏向，验证结果有偏差
        s = EnumStrategy(choices=["x", "y"], weights=[100, 1])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert results.count("x") > results.count("y")


class TestRegexStrategy:
    """RegexStrategy 测试用例"""

    def test_digits(self):
        """generate: 纯数字正则"""
        import re
        s = RegexStrategy(pattern=r"\d{6}")
        v = s.generate(_ctx())
        assert re.fullmatch(r"\d{6}", v)

    def test_uppercase(self):
        """generate: 大写字母正则"""
        import re
        s = RegexStrategy(pattern=r"[A-Z]{3}")
        v = s.generate(_ctx())
        assert re.fullmatch(r"[A-Z]{3}", v)

    def test_letters(self):
        """generate: 字母组合正则"""
        import re
        s = RegexStrategy(pattern=r"[a-zA-Z]{5}")
        v = s.generate(_ctx())
        assert re.fullmatch(r"[a-zA-Z]{5}", v)

    def test_alphanumeric(self):
        """generate: 字母数字混合正则"""
        import re
        s = RegexStrategy(pattern=r"[A-Za-z0-9]{4}")
        v = s.generate(_ctx())
        assert re.fullmatch(r"[A-Za-z0-9]{4}", v)

    def test_phone_format(self):
        """generate: 手机号格式 (带特殊字符)"""
        import re
        s = RegexStrategy(pattern=r"^\d{3}-\d{4}$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"\d{3}-\d{4}", v)

    def test_limited_chars(self):
        """generate: 有限字符集正则"""
        import re
        s = RegexStrategy(pattern=r"[abc]{2}")
        v = s.generate(_ctx())
        assert re.fullmatch(r"[abc]{2}", v)

    def test_values_enumerable(self):
        """values: 可枚举正则，返回所有值"""
        s = RegexStrategy(pattern=r"[a-c]{2}")
        vals = s.values()
        assert vals is not None
        assert len(vals) == 9  # 3*3=9

    def test_values_too_many(self):
        """values: 不可枚举（超过10000），返回None"""
        s = RegexStrategy(pattern=r"\d{5}")
        vals = s.values()
        assert vals is None

    def test_values_infinite(self):
        """values: 无限匹配，返回None"""
        s = RegexStrategy(pattern=r"\d+")
        vals = s.values()
        assert vals is None

    def test_boundary_values_enumerable(self):
        """boundary_values: 可枚举正则返回边界值"""
        s = RegexStrategy(pattern=r"\d{2}")
        bounds = s.boundary_values()
        assert bounds is not None
        assert "00" in bounds
        assert "99" in bounds

    def test_boundary_values_non_enumerable(self):
        """boundary_values: 不可枚举时返回None"""
        s = RegexStrategy(pattern=r"\d{5}")
        bounds = s.boundary_values()
        assert bounds is None

    def test_equivalence_classes(self):
        """equivalence_classes: 每个值是一个单独的等价类"""
        s = RegexStrategy(pattern=r"[ab]{2}")
        classes = s.equivalence_classes()
        assert classes is not None
        # 验证每个等价类只有一个值
        assert all(len(c) == 1 for c in classes)

    def test_equivalence_classes_non_enumerable(self):
        """equivalence_classes: 不可枚举时返回None"""
        s = RegexStrategy(pattern=r"\d{5}")
        classes = s.equivalence_classes()
        assert classes is None

    def test_invalid_values_numeric(self):
        """invalid_values: 针对数字正则返回非法值"""
        s = RegexStrategy(pattern=r"\d{3}")
        invalid = s.invalid_values()
        assert "abcde" in invalid
        assert None in invalid
        assert "" in invalid

    def test_invalid_values_alpha(self):
        """invalid_values: 针对字母正则返回非法值"""
        s = RegexStrategy(pattern=r"[a-z]+")
        invalid = s.invalid_values()
        assert "12345" in invalid
        assert None in invalid
        assert "" in invalid

    def test_invalid_values_contains_none_and_empty(self):
        """invalid_values: 包含None和空字符串"""
        s = RegexStrategy(pattern=r"\w+")
        invalid = s.invalid_values()
        assert None in invalid
        assert "" in invalid

    def test_invalid_regex_unclosed_paren(self):
        """错误处理: 无效正则表达式（未闭合的括号）"""
        import re
        s = RegexStrategy(pattern=r"[a-z(")
        with pytest.raises(Exception):
            s.generate(_ctx())

    def test_registry_integration(self):
        """Registry集成: 通过StrategyRegistry创建RegexStrategy"""
        import re
        from data_builder.strategies.value.registry import StrategyRegistry
        registry = StrategyRegistry()
        strategy = registry.create({"type": "regex", "pattern": r"\d{4}"})
        v = strategy.generate(_ctx())
        assert re.fullmatch(r"\d{4}", v)

    def test_cron_every_minute(self):
        """generate: Linux cron 每分钟 * * * * *"""
        import re
        s = RegexStrategy(pattern=r"^\* \* \* \* \*$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^\* \* \* \* \*$", v)

    def test_cron_hourly(self):
        """generate: Linux cron 每小时整点 0 * * * *"""
        import re
        s = RegexStrategy(pattern=r"^0 \* \* \* \*$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^0 \* \* \* \*$", v)

    def test_cron_daily(self):
        """generate: Linux cron 每天午夜 0 0 * * *"""
        import re
        s = RegexStrategy(pattern=r"^0 0 \* \* \*$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^0 0 \* \* \*$", v)

    def test_cron_every_5_minutes(self):
        """generate: Linux cron 每 5 分钟 */5 * * * *"""
        import re
        s = RegexStrategy(pattern=r"^\*/5 \* \* \* \*$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^\*/5 \* \* \* \*$", v)

    def test_cron_weekly(self):
        """generate: Linux cron 每周日 0 0 * * 0"""
        import re
        s = RegexStrategy(pattern=r"^0 0 \* \* 0$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^0 0 \* \* 0$", v)

    def test_cron_monthly(self):
        """generate: Linux cron 每月第一天 0 0 1 * *"""
        import re
        s = RegexStrategy(pattern=r"^0 0 1 \* \*$")
        v = s.generate(_ctx())
        assert re.fullmatch(r"^0 0 1 \* \*$", v)


class TestSequenceStrategy:
    def test_increment_step(self):
        s = SequenceStrategy(start=0, step=5)
        assert s.generate(_ctx()) == 0
        assert s.generate(_ctx()) == 5
        assert s.generate(_ctx()) == 10

    def test_prefix(self):
        s = SequenceStrategy(start=1, prefix="ID-")
        assert s.generate(_ctx()) == "ID-1"

    def test_suffix(self):
        s = SequenceStrategy(start=1, suffix="-X")
        assert s.generate(_ctx()) == "1-X"

    def test_padding(self):
        s = SequenceStrategy(start=1, padding=4)
        assert s.generate(_ctx()) == "0001"

    def test_reset(self):
        s = SequenceStrategy(start=10)
        s.generate(_ctx())
        s.generate(_ctx())
        s.reset()
        assert s.generate(_ctx()) == 10

    def test_step_zero_raises_error(self):
        """step 为零应该抛出异常 (BUG-015)"""
        with pytest.raises(ValueError, match="step 不能为零"):
            SequenceStrategy(step=0)

    def test_padding_negative_raises_error(self):
        """padding 为负数应该抛出异常 (BUG-015)"""
        with pytest.raises(ValueError, match="padding 不能为负数"):
            SequenceStrategy(padding=-5)

    def test_negative_step_allowed(self):
        """step 为负数应该允许 (BUG-015)"""
        s = SequenceStrategy(start=100, step=-1)
        assert s.generate(_ctx()) == 100
        assert s.generate(_ctx()) == 99

    def test_negative_start_allowed(self):
        """start 为负数应该允许 (BUG-015)"""
        s = SequenceStrategy(start=-10)
        assert s.generate(_ctx()) == -10


class TestSequenceStrategyBaseMethods:
    """SequenceStrategy 基类方法测试"""

    def test_values_basic(self):
        """values: 基本序列的 values()"""
        s = SequenceStrategy(start=1, step=1)
        vals = s.values(limit=10)
        assert vals is not None
        assert len(vals) == 10
        assert vals == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_values_with_limit(self):
        """values: 带 limit 参数"""
        s = SequenceStrategy(start=0, step=5)
        vals = s.values(limit=5)
        assert vals is not None
        assert len(vals) == 5
        assert vals == [0, 5, 10, 15, 20]

    def test_values_with_format(self):
        """values: 带格式的 values() (prefix/suffix/padding)"""
        s = SequenceStrategy(start=1, prefix="ID-", padding=3)
        vals = s.values(limit=3)
        assert vals is not None
        assert len(vals) == 3
        assert vals == ["ID-001", "ID-002", "ID-003"]

    def test_boundary_values(self):
        """boundary_values: 返回起始值和预估的最大边界"""
        s = SequenceStrategy(start=1, step=2)
        bounds = s.boundary_values()
        assert bounds is not None
        assert len(bounds) == 2
        assert bounds[0] == 1  # 起始值
        assert bounds[1] == 199  # start + 99 * step = 1 + 99 * 2

    def test_equivalence_classes(self):
        """equivalence_classes: 返回等价类分组"""
        s = SequenceStrategy(start=0, step=10)
        classes = s.equivalence_classes()
        assert classes is not None
        # 每个等价类只有一个代表值
        assert all(len(c) == 1 for c in classes)
        # 验证前几个代表值
        assert classes[0][0] == 0
        assert classes[1][0] == 10
        assert classes[2][0] == 20

    def test_invalid_values(self):
        """invalid_values: 返回非法值示例"""
        s = SequenceStrategy(start=1, step=1)
        invalid = s.invalid_values()
        assert invalid is not None
        assert -1 in invalid
        assert -100 in invalid
        assert 10**15 in invalid
        assert "abc" in invalid
        assert "not-a-number" in invalid
        assert None in invalid
        assert 3.14 in invalid
        assert [] in invalid


class TestFakerStrategy:
    def test_name(self):
        v = FakerStrategy(method="name", locale="zh_CN").generate(_ctx())
        assert isinstance(v, str) and len(v) > 0

    def test_phone_number(self):
        v = FakerStrategy(method="phone_number", locale="zh_CN").generate(_ctx())
        assert isinstance(v, str) and len(v) > 0

    def test_email(self):
        v = FakerStrategy(method="email", locale="zh_CN").generate(_ctx())
        assert "@" in v

    def test_values_returns_none(self):
        """values: 返回 None (Faker 值域不可枚举)"""
        s = FakerStrategy(method="name")
        assert s.values() is None

    def test_boundary_values_returns_none(self):
        """boundary_values: 返回 None (Faker 无边界概念)"""
        s = FakerStrategy(method="name")
        assert s.boundary_values() is None

    def test_equivalence_classes_returns_none(self):
        """equivalence_classes: 返回 None (Faker 无法预分类)"""
        s = FakerStrategy(method="name")
        assert s.equivalence_classes() is None

    def test_invalid_values(self):
        """invalid_values: 返回类型错误值"""
        s = FakerStrategy(method="name")
        invalid = s.invalid_values()
        assert 12345 in invalid
        assert 3.14 in invalid
        assert {"invalid": "value"} in invalid
        assert [1, 2, 3] in invalid
        assert None in invalid


class TestCallableStrategy:
    def test_ctx_field_path(self):
        s = CallableStrategy(func=lambda ctx: ctx.field_path)
        assert s.generate(_ctx(field_path="my.path")) == "my.path"

    def test_ctx_index(self):
        s = CallableStrategy(func=lambda ctx: ctx.index * 2)
        assert s.generate(_ctx(index=5)) == 10


class TestRefStrategy:
    def test_sibling_ref(self):
        root = {"source": 99}
        s = RefStrategy(ref_path="source")
        assert s.generate(_ctx(root_data=root)) == 99

    def test_transform(self):
        root = {"val": 10}
        s = RefStrategy(ref_path="val", transform=lambda v: v + 1)
        assert s.generate(_ctx(root_data=root)) == 11


class TestRefStrategyBaseMethods:
    """RefStrategy 基类方法测试"""

    def test_values_returns_none(self):
        """values: 返回 None (引用路径指向运行时数据，无法预知值域)"""
        s = RefStrategy(ref_path="user.name")
        assert s.values() is None

    def test_boundary_values_returns_none(self):
        """boundary_values: 返回 None (引用无边界概念)"""
        s = RefStrategy(ref_path="user.name")
        assert s.boundary_values() is None

    def test_equivalence_classes_returns_none(self):
        """equivalence_classes: 返回 None (引用无法预分类)"""
        s = RefStrategy(ref_path="user.name")
        assert s.equivalence_classes() is None

    def test_invalid_values(self):
        """invalid_values: 返回无效的引用场景"""
        s = RefStrategy(ref_path="user.name")
        invalid = s.invalid_values()
        assert None in invalid
        assert "" in invalid
        assert "nonexistent.path" in invalid
        assert ".." in invalid
        assert "." in invalid
        assert "a[b" in invalid
        assert "a]b" in invalid


class TestDateTimeStrategy:
    def test_default_format_output(self):
        import re
        s = DateTimeStrategy()
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_custom_format(self):
        s = DateTimeStrategy(format="%Y/%m/%d")
        import re
        v = s.generate(_ctx())
        assert re.match(r"\d{4}/\d{2}/\d{2}", v)

    def test_start_end_range(self):
        start = datetime(2020, 1, 1)
        end = datetime(2020, 12, 31)
        s = DateTimeStrategy(start=start, end=end, format="%Y-%m-%d")
        for _ in range(20):
            v = s.generate(_ctx())
            dt = datetime.strptime(v, "%Y-%m-%d")
            assert start <= dt <= end


class TestEnumStrategyEdgeCases:
    def test_empty_choices_raises(self):
        s = EnumStrategy([])
        with pytest.raises(StrategyError):
            s.generate(_ctx())


class TestDateTimeStrategyEdgeCases:
    def test_start_after_end_raises(self):
        start = datetime(2025, 1, 1)
        end = datetime(2020, 1, 1)
        s = DateTimeStrategy(start=start, end=end)
        with pytest.raises(StrategyError):
            s.generate(_ctx())


class TestRefStrategyEdgeCases:
    def test_missing_path_raises(self):
        s = RefStrategy("nonexistent.field")
        ctx = _ctx(root_data={"other": 1})
        with pytest.raises(FieldPathError):
            s.generate(ctx)

    def test_missing_array_index_raises(self):
        s = RefStrategy("items[5]")
        ctx = _ctx(root_data={"items": [1, 2, 3]})
        with pytest.raises(FieldPathError):
            s.generate(ctx)
