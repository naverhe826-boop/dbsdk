"""
PasswordStrategy 测试用例

覆盖各种参数组合和边界条件：
- 默认参数生成
- 自定义长度和字符类型
- 边界值测试
- 异常情况测试
"""

import string
import pytest

from data_builder.strategies.value.string import PasswordStrategy
from data_builder.strategies.basic import StrategyContext
from data_builder.exceptions import StrategyError


def _ctx(**kwargs):
    """创建测试用 StrategyContext"""
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestDefaultPassword:
    """默认参数测试"""

    def test_default_password_contains_all_types(self):
        """测试默认参数生成的密码包含数字、大写字母、小写字母、特殊字符"""
        strategy = PasswordStrategy()
        password = strategy.generate(_ctx())

        assert len(password) == 12

        # 验证包含数字
        assert any(c in string.digits for c in password), f"密码应包含数字: {password}"
        # 验证包含大写字母
        assert any(c in string.ascii_uppercase for c in password), f"密码应包含大写字母: {password}"
        # 验证包含小写字母
        assert any(c in string.ascii_lowercase for c in password), f"密码应包含小写字母: {password}"
        # 验证包含特殊字符
        assert any(c in strategy.special_chars for c in password), f"密码应包含特殊字符: {password}"


class TestCustomLength:
    """自定义长度测试"""

    def test_custom_length(self):
        """测试自定义长度范围 (8-32)"""
        for length in [10, 16, 20, 32]:
            strategy = PasswordStrategy(length=length)
            password = strategy.generate(_ctx())
            assert len(password) == length, f"长度应为 {length}, 实际为 {len(password)}"

    def test_length_boundary(self):
        """测试边界值 8 和 32"""
        # 最小边界
        strategy_min = PasswordStrategy(length=8)
        password_min = strategy_min.generate(_ctx())
        assert len(password_min) == 8

        # 最大边界
        strategy_max = PasswordStrategy(length=32)
        password_max = strategy_max.generate(_ctx())
        assert len(password_max) == 32


class TestCharacterTypes:
    """字符类型测试"""

    def test_use_digits_only(self):
        """测试仅数字"""
        strategy = PasswordStrategy(
            length=12,
            use_digits=True,
            use_uppercase=False,
            use_lowercase=False,
            use_special=False
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        assert password.isdigit(), f"密码应仅包含数字: {password}"

    def test_use_uppercase_only(self):
        """测试仅大写字母"""
        strategy = PasswordStrategy(
            length=12,
            use_digits=False,
            use_uppercase=True,
            use_lowercase=False,
            use_special=False
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        assert password.isupper(), f"密码应仅包含大写字母: {password}"
        assert password.isalpha(), f"密码应仅包含字母: {password}"

    def test_use_lowercase_only(self):
        """测试仅小写字母"""
        strategy = PasswordStrategy(
            length=12,
            use_digits=False,
            use_uppercase=False,
            use_lowercase=True,
            use_special=False
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        assert password.islower(), f"密码应仅包含小写字母: {password}"
        assert password.isalpha(), f"密码应仅包含字母: {password}"

    def test_use_special_only(self):
        """测试仅特殊字符"""
        strategy = PasswordStrategy(
            length=12,
            use_digits=False,
            use_uppercase=False,
            use_lowercase=False,
            use_special=True
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        # 验证所有字符都在特殊字符集中
        for c in password:
            assert c in strategy.special_chars, f"字符应在特殊字符集中: {c}"

    def test_use_multiple_types(self):
        """测试多种字符类型组合"""
        # 数字 + 小写字母
        strategy = PasswordStrategy(
            length=12,
            use_digits=True,
            use_uppercase=False,
            use_lowercase=True,
            use_special=False
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        has_digit = any(c in string.digits for c in password)
        has_lower = any(c in string.ascii_lowercase for c in password)
        assert has_digit, f"密码应包含数字: {password}"
        assert has_lower, f"密码应包含小写字母: {password}"

        # 数字 + 大写字母 + 小写字母
        strategy2 = PasswordStrategy(
            length=12,
            use_digits=True,
            use_uppercase=True,
            use_lowercase=True,
            use_special=False
        )
        password2 = strategy2.generate(_ctx())

        assert len(password2) == 12
        has_digit2 = any(c in string.digits for c in password2)
        has_upper2 = any(c in string.ascii_uppercase for c in password2)
        has_lower2 = any(c in string.ascii_lowercase for c in password2)
        assert has_digit2 and has_upper2 and has_lower2, f"密码应包含数字、大写和小写: {password2}"

    def test_custom_special_chars(self):
        """测试特殊字符自定义"""
        custom_chars = "!#$%"
        strategy = PasswordStrategy(
            length=12,
            use_digits=False,
            use_uppercase=False,
            use_lowercase=False,
            use_special=True,
            special_chars=custom_chars
        )
        password = strategy.generate(_ctx())

        assert len(password) == 12
        for c in password:
            assert c in custom_chars, f"字符应在自定义特殊字符集中: {c}"


class TestInvalidParameters:
    """无效参数测试"""

    def test_invalid_length_too_short(self):
        """测试长度小于 8 时抛出异常"""
        with pytest.raises(StrategyError) as exc_info:
            PasswordStrategy(length=7)
        assert "8-32" in str(exc_info.value)

    def test_invalid_length_too_long(self):
        """测试长度大于 32 时抛出异常"""
        with pytest.raises(StrategyError) as exc_info:
            PasswordStrategy(length=33)
        assert "8-32" in str(exc_info.value)

    def test_all_char_types_disabled(self):
        """测试全部字符类型关闭时抛出异常"""
        with pytest.raises(StrategyError) as exc_info:
            PasswordStrategy(
                length=12,
                use_digits=False,
                use_uppercase=False,
                use_lowercase=False,
                use_special=False
            )
        assert "至少需要选择一种字符类型" in str(exc_info.value)


class TestBoundaryAndEquivalence:
    """边界值和等价类测试"""

    def test_boundary_values(self):
        """测试 boundary_values 方法"""
        strategy = PasswordStrategy()
        boundaries = strategy.boundary_values()

        assert boundaries is not None
        assert len(boundaries) == 2

        min_pwd, max_pwd = boundaries
        assert len(min_pwd) == 8, f"最小边界长度应为 8, 实际为 {len(min_pwd)}"
        assert len(max_pwd) == 32, f"最大边界长度应为 32, 实际为 {len(max_pwd)}"

    def test_equivalence_classes(self):
        """测试 equivalence_classes 方法"""
        strategy = PasswordStrategy()
        classes = strategy.equivalence_classes()

        assert classes is not None
        assert len(classes) > 0
        for cls in classes:
            assert len(cls) == 3  # 每个类别生成3个样本

    def test_invalid_values(self):
        """测试 invalid_values 方法"""
        strategy = PasswordStrategy()
        invalid_vals = strategy.invalid_values()

        assert invalid_vals is not None
        assert len(invalid_vals) > 0
