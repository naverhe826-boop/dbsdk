from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext


MAX_ENUM_COUNT = 10000


class RegexStrategy(Strategy):
    """正则表达式生成策略"""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self._exrex = None

    def _get_exrex(self):
        if self._exrex is None:
            import exrex
            self._exrex = exrex
        return self._exrex

    def generate(self, ctx: StrategyContext) -> str:
        exrex = self._get_exrex()
        return exrex.getone(self.pattern)

    def values(self) -> Optional[List[str]]:
        exrex = self._get_exrex()
        values = []
        for v in exrex.generate(self.pattern):
            values.append(v)
            if len(values) > MAX_ENUM_COUNT:
                return None
        return values

    def boundary_values(self) -> Optional[List[str]]:
        vals = self.values()
        if vals is None:
            return None
        if not vals:
            return []
        vals_sorted = sorted(vals)
        result = [vals_sorted[0]]
        if len(vals_sorted) > 1:
            result.append(vals_sorted[-1])
        return result

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        vals = self.values()
        if vals is None:
            return None
        return [[v] for v in vals]

    def invalid_values(self) -> List[Any]:
        result = []
        result.append("__INVALID__")
        result.append("")
        result.append(None)
        if not self.pattern.startswith("\\d"):
            result.append("12345")
        if not self.pattern.startswith("\\w"):
            result.append("abcde")
        return result
