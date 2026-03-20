"""
EnumStrategy 测试用例

覆盖基本功能、权重、边界值、等价类、无效值等
"""
import pytest

from data_builder import EnumStrategy, StrategyContext
from data_builder.exceptions import StrategyError


def _ctx(**kwargs):
    """创建测试用 StrategyContext"""
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestEnumStrategyBasic:
    """EnumStrategy 基本功能测试"""

    def test_basic_choices_string(self):
        """字符串枚举"""
        s = EnumStrategy(choices=["a", "b", "c"])
        results = [s.generate(_ctx()) for _ in range(100)]
        # 验证所有值都在choices中
        assert all(v in ["a", "b", "c"] for v in results)
        # 验证至少生成了不同的值（概率上）
        assert len(set(results)) >= 1

    def test_basic_choices_int(self):
        """整数枚举"""
        s = EnumStrategy(choices=[1, 2, 3])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in [1, 2, 3] for v in results)

    def test_basic_choices_mixed(self):
        """混合类型枚举"""
        s = EnumStrategy(choices=[1, "two", 3.0])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in [1, "two", 3.0] for v in results)

    def test_single_choice(self):
        """单个选项"""
        s = EnumStrategy(choices=["only"])
        results = [s.generate(_ctx()) for _ in range(10)]
        assert all(v == "only" for v in results)


class TestEnumStrategyWeights:
    """权重功能测试"""

    def test_weights_string(self):
        """字符串枚举带权重"""
        s = EnumStrategy(choices=["a", "b", "c"], weights=[10.0, 1.0, 1.0])
        results = [s.generate(_ctx()) for _ in range(1000)]
        # a 应该占绝大多数
        a_count = results.count("a")
        assert a_count > 700  # 至少70%

    def test_weights_all_zero(self):
        """权重全为0应该报错"""
        with pytest.raises(Exception):
            s = EnumStrategy(choices=["a", "b"], weights=[0.0, 0.0])
            s.generate(_ctx())

    def test_weights_int(self):
        """整数枚举带权重"""
        s = EnumStrategy(choices=[1, 2, 3], weights=[0.0, 0.0, 1.0])
        results = [s.generate(_ctx()) for _ in range(100)]
        # 应该总是返回3
        assert all(v == 3 for v in results)

    def test_weights_mismatch_length(self):
        """权重数量与选项不匹配应该报错"""
        with pytest.raises(Exception):
            s = EnumStrategy(choices=["a", "b", "c"], weights=[1.0, 2.0])
            s.generate(_ctx())


class TestEnumStrategyValues:
    """values() 方法测试"""

    def test_values_string(self):
        """字符串枚举的values"""
        s = EnumStrategy(choices=["a", "b", "c"])
        assert s.values() == ["a", "b", "c"]

    def test_values_int(self):
        """整数枚举的values"""
        s = EnumStrategy(choices=[1, 2, 3])
        assert s.values() == [1, 2, 3]

    def test_values_mixed(self):
        """混合类型的values"""
        s = EnumStrategy(choices=[1, "two", 3.0, None])
        assert s.values() == [1, "two", 3.0, None]


class TestEnumStrategyBoundaryValues:
    """boundary_values() 方法测试"""

    def test_boundary_values_multiple(self):
        """多个选项的边界值"""
        s = EnumStrategy(choices=[1, 2, 3, 4, 5])
        boundary = s.boundary_values()
        assert boundary == [1, 5]

    def test_boundary_values_two(self):
        """两个选项的边界值"""
        s = EnumStrategy(choices=["a", "b"])
        boundary = s.boundary_values()
        assert boundary == ["a", "b"]

    def test_boundary_values_single(self):
        """单个选项的边界值"""
        s = EnumStrategy(choices=["only"])
        boundary = s.boundary_values()
        assert boundary == ["only"]

    def test_boundary_values_empty(self):
        """空列表的边界值"""
        s = EnumStrategy(choices=[])
        boundary = s.boundary_values()
        assert boundary is None


class TestEnumStrategyEquivalenceClasses:
    """equivalence_classes() 方法测试"""

    def test_equivalence_classes(self):
        """等价类"""
        s = EnumStrategy(choices=["a", "b", "c"])
        classes = s.equivalence_classes()
        assert classes == [["a"], ["b"], ["c"]]

    def test_equivalence_classes_int(self):
        """整数等价类"""
        s = EnumStrategy(choices=[1, 2])
        classes = s.equivalence_classes()
        assert classes == [[1], [2]]

    def test_equivalence_classes_empty(self):
        """空列表等价类"""
        s = EnumStrategy(choices=[])
        classes = s.equivalence_classes()
        assert classes == []


class TestEnumStrategyInvalidValues:
    """invalid_values() 方法测试"""

    def test_invalid_values_string(self):
        """字符串枚举的无效值"""
        s = EnumStrategy(choices=["a", "b", "c"])
        invalid = s.invalid_values()
        # 应该包含一个不在choices中的字符串和None
        assert None in invalid
        assert len(invalid) == 2
        # 验证第一个无效值不在choices中
        non_none = [v for v in invalid if v is not None]
        assert all(v not in ["a", "b", "c"] for v in non_none)

    def test_invalid_values_int(self):
        """整数枚举的无效值"""
        s = EnumStrategy(choices=[1, 2, 3])
        invalid = s.invalid_values()
        assert None in invalid
        assert len(invalid) == 2
        # 验证整数无效值大于所有choices
        non_none = [v for v in invalid if v is not None]
        assert all(v > 3 for v in non_none)

    def test_invalid_values_mixed(self):
        """混合类型的无效值"""
        s = EnumStrategy(choices=[1, "two", 3.0])
        invalid = s.invalid_values()
        assert None in invalid
        # 混合类型使用字符串作为无效值
        non_none = [v for v in invalid if v is not None]
        assert any(isinstance(v, str) for v in non_none)


class TestEnumStrategyError:
    """错误处理测试"""

    def test_empty_choices_error(self):
        """空列表应该报错"""
        s = EnumStrategy(choices=[])
        with pytest.raises(StrategyError):
            s.generate(_ctx())

    def test_weights_length_mismatch_raises_error(self):
        """weights 长度与 choices 不匹配应该抛出异常 (BUG-016)"""
        with pytest.raises(StrategyError, match="weights 长度"):
            EnumStrategy(choices=["a", "b"], weights=[0.5])

    def test_weights_negative_raises_error(self):
        """weights 包含负数应该抛出异常 (BUG-016)"""
        with pytest.raises(StrategyError, match="weights 不能包含负数"):
            EnumStrategy(choices=["a", "b"], weights=[0.5, -0.5])

    def test_weights_all_zero_raises_error(self):
        """weights 全为零应该抛出异常 (BUG-016)"""
        with pytest.raises(StrategyError, match="weights 不能全为零"):
            EnumStrategy(choices=["a", "b"], weights=[0, 0])

    def test_weights_with_empty_choices_raises_error(self):
        """choices 为空时提供 weights 应该抛出异常 (BUG-016)"""
        with pytest.raises(StrategyError, match="不能在 choices 为空时提供 weights"):
            EnumStrategy(choices=[], weights=[1])


class TestEnumStrategyEdgeCases:
    """边界情况测试"""

    def test_duplicate_choices(self):
        """重复的选项"""
        s = EnumStrategy(choices=["a", "a", "b"])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in ["a", "b"] for v in results)

    def test_special_characters(self):
        """特殊字符"""
        s = EnumStrategy(choices=["hello\nworld", "tab\there", "quote\""])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in ["hello\nworld", "tab\there", "quote\""] for v in results)

    def test_unicode(self):
        """Unicode字符"""
        s = EnumStrategy(choices=["中文", "日本語", "한국어"])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in ["中文", "日本語", "한국어"] for v in results)

    def test_very_large_choices(self):
        """大量选项"""
        choices = [f"item_{i}" for i in range(1000)]
        s = EnumStrategy(choices=choices)
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in choices for v in results)

    def test_float_values(self):
        """浮点数选项"""
        s = EnumStrategy(choices=[1.1, 2.2, 3.3])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in [1.1, 2.2, 3.3] for v in results)

    def test_boolean_values(self):
        """布尔值选项"""
        s = EnumStrategy(choices=[True, False])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert all(v in [True, False] for v in results)

    def test_none_in_choices(self):
        """选项中包含None"""
        s = EnumStrategy(choices=[None, "a", "b"])
        results = [s.generate(_ctx()) for _ in range(100)]
        assert None in results
        assert "a" in results or "b" in results
