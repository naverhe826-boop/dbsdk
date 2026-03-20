from typing import Any, List, Optional, Union
from ...basic import Strategy, StrategyContext


class SequenceStrategy(Strategy):
    """自增序列策略"""

    def __init__(
        self,
        start: int = 1,
        step: int = 1,
        prefix: str = "",
        suffix: str = "",
        padding: int = 0
    ):
        if step == 0:
            raise ValueError("SequenceStrategy: step 不能为零")
        if padding < 0:
            raise ValueError("SequenceStrategy: padding 不能为负数")

        self.start = start
        self.step = step
        self.prefix = prefix
        self.suffix = suffix
        self.padding = padding
        self._counter = start

    def generate(self, ctx: StrategyContext) -> Union[int, str]:
        val = self._counter
        self._counter += self.step
        # 无格式修饰时返回 int，保留原始数值类型
        if not self.prefix and not self.suffix and not self.padding:
            return val
        num_str = str(val).zfill(self.padding) if self.padding else str(val)
        return f"{self.prefix}{num_str}{self.suffix}"

    def reset(self):
        """重置计数器"""
        self._counter = self.start

    def _format_value(self, val: int) -> Union[int, str]:
        """格式化单个值，应用 prefix/suffix/padding"""
        if not self.prefix and not self.suffix and not self.padding:
            return val
        num_str = str(val).zfill(self.padding) if self.padding else str(val)
        return f"{self.prefix}{num_str}{self.suffix}"

    def values(self, limit: int = 100) -> Optional[List[Union[int, str]]]:
        """返回序列的前 N 个值

        Args:
            limit: 返回的最大值数量，默认100
        Returns:
            值列表，如果有限制则返回列表，无限制则返回 None
        """
        result = []
        for i in range(limit):
            val = self.start + i * self.step
            result.append(self._format_value(val))
        return result

    def boundary_values(self) -> Optional[List[Union[int, str]]]:
        """返回边界值：起始值和预估的最大边界"""
        # 起始值
        start_val = self._format_value(self.start)
        # 预估一个大边界（start + 99 * step，即 values 默认返回的范围）
        max_val = self.start + 99 * self.step
        max_boundary = self._format_value(max_val)
        return [start_val, max_boundary]

    def equivalence_classes(self) -> Optional[List[List[Union[int, str]]]]:
        """返回等价类分组

        按步长分区，返回 start, start+step, start+2*step 等作为代表值
        """
        # 返回前几个等价类的代表值
        representatives = []
        for i in range(min(5, 100)):  # 最多5个代表值
            val = self.start + i * self.step
            representatives.append([self._format_value(val)])
        return representatives

    def invalid_values(self) -> Optional[List[Any]]:
        """返回非法值示例

        包括：负数（非序列起始值）、超大数、字符串、非数字等
        """
        return [
            -1,
            -100,
            10**15,  # 超大数
            "abc",
            "not-a-number",
            None,
            3.14,
            [],
        ]
