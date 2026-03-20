from typing import Any, Callable

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class CallableStrategy(Strategy):
    """自定义函数策略"""

    def __init__(self, func: Callable[[StrategyContext], Any]):
        if not callable(func):
            raise StrategyError(f"CallableStrategy: func 必须是可调用对象，实际为 {type(func).__name__}")
        self.func = func

    def generate(self, ctx: StrategyContext) -> Any:
        return self.func(ctx)
