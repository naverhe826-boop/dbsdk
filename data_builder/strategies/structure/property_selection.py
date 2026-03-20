from typing import List, Union
from ..basic import Strategy, StructureStrategy, StrategyContext
from ..basic import FixedStrategy


class PropertySelectionStrategy(StructureStrategy):
    """控制对象生成哪些属性的策略"""

    def __init__(self, properties: Union[List[str], Strategy]):
        self.source = FixedStrategy(properties) if isinstance(properties, list) else properties

    def generate(self, ctx: StrategyContext) -> List[str]:
        return self.source.generate(ctx)
