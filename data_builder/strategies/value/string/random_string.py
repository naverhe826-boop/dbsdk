import random
import string
from itertools import product
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class RandomStringStrategy(Strategy):
    """随机字符串策略"""

    def __init__(
        self,
        length: int = 10,
        charset: str = string.ascii_letters + string.digits
    ):
        if length < 0:
            raise StrategyError(f"RandomStringStrategy: length({length}) 不能为负数")
        if not charset:
            raise StrategyError("RandomStringStrategy: charset 不能为空")
        self.length = length
        self.charset = charset

    def generate(self, ctx: StrategyContext) -> str:
        return ''.join(random.choices(self.charset, k=self.length))

    def boundary_values(self) -> Optional[List[str]]:
        if self.length == 0:
            return [""]
        return [
            ''.join(random.choices(self.charset, k=1)),
            ''.join(random.choices(self.charset, k=self.length)),
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        has_alpha = any(c.isalpha() for c in self.charset)
        has_digit = any(c.isdigit() for c in self.charset)
        classes = []
        if has_alpha:
            alpha_chars = [c for c in self.charset if c.isalpha()]
            classes.append([''.join(random.choices(alpha_chars, k=max(1, self.length)))])
        if has_digit:
            digit_chars = [c for c in self.charset if c.isdigit()]
            classes.append([''.join(random.choices(digit_chars, k=max(1, self.length)))])
        if has_alpha and has_digit:
            classes.append([''.join(random.choices(self.charset, k=max(1, self.length)))])
        if not classes:
            classes.append([''.join(random.choices(self.charset, k=max(1, self.length)))])
        return classes

    def invalid_values(self) -> Optional[List[Any]]:
        return [
            "",
            ''.join(random.choices(self.charset, k=self.length + 100)),
            12345,
            None,
        ]

    def values(self) -> Optional[List[str]]:
        """值域：字符串组合可能非常多，当超过阈值时返回 None"""
        total_combinations = len(self.charset) ** self.length
        if total_combinations > 1000:
            return None  # 不可枚举
        # 枚举所有组合
        return [''.join(p) for p in product(self.charset, repeat=self.length)]
