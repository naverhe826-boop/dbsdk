from typing import Union
from ..basic import Strategy, StructureStrategy, StrategyContext
from ..basic import FixedStrategy


class SchemaSelectionStrategy(StructureStrategy):
    """控制 oneOf/anyOf 分支选择的策略"""

    def __init__(self, source: Union[int, Strategy]):
        self.source = FixedStrategy(source) if isinstance(source, int) else source

    def generate(self, ctx: StrategyContext) -> int:
        return int(self.source.generate(ctx))
