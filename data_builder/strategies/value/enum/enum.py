import random
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class EnumStrategy(Strategy):
    """枚举选择策略，支持权重"""

    def __init__(
        self,
        choices: List[Any],
        weights: Optional[List[float]] = None
    ):
        self.choices = choices
        self.weights = weights

        # 验证权重参数（仅当提供 weights 时）
        if weights is not None:
            if not choices:
                raise StrategyError("EnumStrategy: 不能在 choices 为空时提供 weights")
            if len(weights) != len(choices):
                raise StrategyError(
                    f"EnumStrategy: weights 长度({len(weights)}) 与 choices 长度({len(choices)}) 不匹配"
                )
            if any(w < 0 for w in weights):
                raise StrategyError("EnumStrategy: weights 不能包含负数")
            if all(w == 0 for w in weights):
                raise StrategyError("EnumStrategy: weights 不能全为零")

    def generate(self, ctx: StrategyContext) -> Any:
        if not self.choices:
            raise StrategyError("EnumStrategy: choices 不能为空列表")
        if self.weights:
            # random.choices 已经内置了权重验证，但我们已在 __init__ 中预验证
            return random.choices(self.choices, weights=self.weights, k=1)[0]
        return random.choice(self.choices)

    def values(self) -> Optional[List[Any]]:
        return list(self.choices)

    def boundary_values(self) -> Optional[List[Any]]:
        if not self.choices:
            return None
        result = [self.choices[0]]
        if len(self.choices) > 1:
            result.append(self.choices[-1])
        return result

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        return [[c] for c in self.choices]

    def invalid_values(self) -> Optional[List[Any]]:
        result = []
        # 生成一个不在 choices 中的值
        if all(isinstance(c, str) for c in self.choices):
            candidate = "__INVALID__"
            while candidate in self.choices:
                candidate += "_"
            result.append(candidate)
        elif all(isinstance(c, (int, float)) for c in self.choices):
            candidate = max(self.choices) + 9999
            result.append(candidate)
        else:
            result.append("__INVALID__")
        result.append(None)
        return result
