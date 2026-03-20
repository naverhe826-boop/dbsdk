from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class FakerStrategy(Strategy):
    """Faker 库集成策略"""

    def __init__(
        self,
        method: str,
        locale: str = "zh_CN",
        **kwargs
    ):
        self.method = method
        self.locale = locale
        self.kwargs = kwargs
        # 立即创建实例并验证 method 存在
        from faker import Faker
        self._faker = Faker(self.locale)
        if not hasattr(self._faker, method):
            raise StrategyError(f"FakerStrategy: Faker({locale!r}) 无方法 {method!r}")

    def generate(self, ctx: StrategyContext) -> Any:
        method = getattr(self._faker, self.method)
        return method(**self.kwargs)

    def values(self) -> Optional[List[Any]]:
        return None

    def boundary_values(self) -> Optional[List[Any]]:
        return None

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        return None

    def invalid_values(self) -> Optional[List[Any]]:
        return [12345, 3.14, {"invalid": "value"}, [1, 2, 3], None]
