from typing import Any, List, Optional

from .base import Strategy, StrategyContext


class FixedStrategy(Strategy):
    """固定值策略"""

    def __init__(self, value: Any):
        self.value = value

    def generate(self, ctx: StrategyContext) -> Any:
        return self.value

    def values(self) -> Optional[List[Any]]:
        return [self.value]

    def boundary_values(self) -> Optional[List[Any]]:
        return [self.value]

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        return [[self.value]]

    def invalid_values(self) -> Optional[List[Any]]:
        result = []
        if isinstance(self.value, bool):
            result.append("not_bool")
        elif isinstance(self.value, str):
            result.append(12345)
        elif isinstance(self.value, (int, float)):
            result.append("not_a_number")
        else:
            result.append("__INVALID__")
        result.append(None)
        return result
