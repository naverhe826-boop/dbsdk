from typing import Union
from ..basic import Strategy, StructureStrategy, StrategyContext
from ..basic import FixedStrategy


class ContainsCountStrategy(StructureStrategy):
    """控制数组中 contains 元素数量的策略"""

    def __init__(self, source: Union[int, Strategy]):
        self.source = FixedStrategy(source) if isinstance(source, int) else source

    def generate(self, ctx: StrategyContext) -> int:
        val = self.source.generate(ctx)
        return max(0, int(val))
