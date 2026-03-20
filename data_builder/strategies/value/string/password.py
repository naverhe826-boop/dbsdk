import random
import string
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class PasswordStrategy(Strategy):
    """密码生成策略，符合 Linux/Windows 密码策略要求"""

    DEFAULT_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(
        self,
        length: int = 12,
        use_digits: bool = True,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_special: bool = True,
        special_chars: Optional[str] = None,
    ):
        # 参数校验：length 必须在 8-32 范围内
        if length < 8 or length > 32:
            raise StrategyError(f"PasswordStrategy: length({length}) 必须在 8-32 范围内")

        # 参数校验：至少选择一种字符类型
        if not (use_digits or use_uppercase or use_lowercase or use_special):
            raise StrategyError(
                "PasswordStrategy: 至少需要选择一种字符类型 "
                "(use_digits/use_uppercase/use_lowercase/use_special)"
            )

        self.length = length
        self.use_digits = use_digits
        self.use_uppercase = use_uppercase
        self.use_lowercase = use_lowercase
        self.use_special = use_special
        self.special_chars = special_chars if special_chars is not None else self.DEFAULT_SPECIAL_CHARS

        # 构建字符集
        self._charset = ""
        self._required_chars = []

        if use_digits:
            self._charset += string.digits
            self._required_chars.append(string.digits)
        if use_uppercase:
            self._charset += string.ascii_uppercase
            self._required_chars.append(string.ascii_uppercase)
        if use_lowercase:
            self._charset += string.ascii_lowercase
            self._required_chars.append(string.ascii_lowercase)
        if use_special:
            self._charset += self.special_chars
            self._required_chars.append(self.special_chars)

        if not self._charset:
            raise StrategyError("PasswordStrategy: 字符集为空")

    def generate(self, ctx: StrategyContext) -> str:
        """生成随机密码，确保每种要求的字符类型至少出现一次"""
        # 确保每种字符类型至少出现一次
        password_chars = []
        for char_set in self._required_chars:
            password_chars.append(random.choice(char_set))

        # 剩余位置用所有启用的字符类型随机填充
        remaining_length = self.length - len(password_chars)
        if remaining_length > 0:
            password_chars.extend(random.choices(self._charset, k=remaining_length))

        # 随机打乱顺序
        random.shuffle(password_chars)

        return ''.join(password_chars)

    def boundary_values(self) -> Optional[List[str]]:
        """返回最小/最大长度边界"""
        min_pwd = ""
        max_pwd = ""

        # 最小边界：8位，使用所有启用的字符类型各一个
        for char_set in self._required_chars:
            min_pwd += random.choice(char_set)
        # 补齐到最小长度 8
        if len(min_pwd) < 8:
            min_pwd += ''.join(random.choices(self._charset, k=8 - len(min_pwd)))

        # 最大边界：32位
        max_pwd = ''.join(random.choices(self._charset, k=32))

        return [min_pwd, max_pwd]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """按字符类型组合分类"""
        classes = []
        samples_per_class = 3

        # 类别1：仅数字
        if self.use_digits and not self.use_uppercase and not self.use_lowercase and not self.use_special:
            classes.append([''.join(random.choices(string.digits, k=self.length)) for _ in range(samples_per_class)])

        # 类别2：仅小写字母
        if self.use_lowercase and not self.use_digits and not self.use_uppercase and not self.use_special:
            classes.append([''.join(random.choices(string.ascii_lowercase, k=self.length)) for _ in range(samples_per_class)])

        # 类别3：仅大写字母
        if self.use_uppercase and not self.use_digits and not self.use_lowercase and not self.use_special:
            classes.append([''.join(random.choices(string.ascii_uppercase, k=self.length)) for _ in range(samples_per_class)])

        # 类别4：数字 + 小写字母
        if self.use_digits and self.use_lowercase and not self.use_uppercase and not self.use_special:
            charset = string.digits + string.ascii_lowercase
            classes.append([''.join(random.choices(charset, k=self.length)) for _ in range(samples_per_class)])

        # 类别5：数字 + 大写字母 + 小写字母 + 特殊字符（完整策略）
        if self.use_digits and self.use_uppercase and self.use_lowercase and self.use_special:
            classes.append([self.generate(StrategyContext(field_path="", field_schema={})) for _ in range(samples_per_class)])

        # 类别6：默认生成结果
        classes.append([self.generate(StrategyContext(field_path="", field_schema={})) for _ in range(samples_per_class)])

        return classes

    def invalid_values(self) -> Optional[List[Any]]:
        """返回无效输入"""
        return [
            "",  # 空字符串
            "short",  # 小于最小长度
            "a" * 5,  # 小于8位
            12345,  # 数字类型
            None,  # None 值
            ["password"],  # 列表类型
        ]
