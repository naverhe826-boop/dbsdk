import random
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class RangeStrategy(Strategy):
    """数值范围策略"""

    def __init__(
        self,
        min_val: Union[int, float] = 0,
        max_val: Union[int, float] = 100,
        is_float: bool = False,
        precision: int = 2
    ):
        self.min_val = min_val
        self.max_val = max_val
        self.is_float = is_float
        self.precision = precision
        if min_val > max_val:
            raise StrategyError(f"RangeStrategy: min_val({min_val}) > max_val({max_val})")

    def generate(self, ctx: StrategyContext) -> Union[int, float]:
        if self.is_float:
            val = random.uniform(self.min_val, self.max_val)
            return round(val, self.precision)
        return random.randint(int(self.min_val), int(self.max_val))

    def values(self) -> Optional[List[Union[int, float]]]:
        if self.is_float:
            return None
        int_min, int_max = int(self.min_val), int(self.max_val)
        if int_max - int_min + 1 > 1000:
            return None
        return list(range(int_min, int_max + 1))

    def boundary_values(self) -> Optional[List[Union[int, float]]]:
        if self.is_float:
            epsilon = 10 ** (-self.precision)
            seen = set()
            result = []
            for v in [self.min_val, self.min_val + epsilon, self.max_val - epsilon, self.max_val]:
                rv = round(v, self.precision)
                if rv not in seen and self.min_val <= rv <= self.max_val:
                    seen.add(rv)
                    result.append(rv)
            return result
        int_min, int_max = int(self.min_val), int(self.max_val)
        # 去重保序
        seen = set()
        result = []
        for v in [int_min, int_min + 1, int_max - 1, int_max]:
            if v not in seen and int_min <= v <= int_max:
                seen.add(v)
                result.append(v)
        return result

    def equivalence_classes(self) -> Optional[List[List[Union[int, float]]]]:
        if self.is_float:
            mid = round((self.min_val + self.max_val) / 2, self.precision)
            return [[self.min_val], [mid], [self.max_val]]
        int_min, int_max = int(self.min_val), int(self.max_val)
        mid = (int_min + int_max) // 2
        return [[int_min], [mid], [int_max]]

    def invalid_values(self) -> Optional[List[Any]]:
        if self.is_float:
            epsilon = 10 ** (-self.precision)
            return [
                round(self.min_val - epsilon, self.precision),
                round(self.max_val + epsilon, self.precision),
                "not_a_number",
                None,
            ]
        int_min, int_max = int(self.min_val), int(self.max_val)
        return [int_min - 1, int_max + 1, "not_a_number", None]
