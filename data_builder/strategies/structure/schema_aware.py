import random
import string
from typing import Any, List, Optional

from ..basic import Strategy, StrategyContext


class SchemaAwareStrategy(Strategy):
    """基于 schema 约束自动推导值域的策略（仅提供值域接口，不用于 generate）"""

    def __init__(self, field_schema: dict):
        self.field_schema = field_schema
        self.schema_type = field_schema.get("type", "string")

    def generate(self, ctx: StrategyContext) -> Any:
        raise NotImplementedError("SchemaAwareStrategy 仅提供值域接口，不支持 generate()")

    def boundary_values(self) -> Optional[List[Any]]:
        if self.schema_type == "integer":
            return self._int_boundary()
        elif self.schema_type == "number":
            return self._float_boundary()
        elif self.schema_type == "string":
            return self._string_boundary()
        elif self.schema_type == "boolean":
            return [True, False]
        return None

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        if self.schema_type == "integer":
            return self._int_equiv()
        elif self.schema_type == "number":
            return self._float_equiv()
        elif self.schema_type == "string":
            return self._string_equiv()
        elif self.schema_type == "boolean":
            return [[True], [False]]
        return None

    def invalid_values(self) -> Optional[List[Any]]:
        if self.schema_type == "integer":
            return self._int_invalid()
        elif self.schema_type == "number":
            return self._float_invalid()
        elif self.schema_type == "string":
            return self._string_invalid()
        elif self.schema_type == "boolean":
            return ["not_bool", 0, None]
        return None

    # --- integer ---

    def _int_boundary(self) -> List[Any]:
        mn = int(self.field_schema.get("minimum", 0))
        mx = int(self.field_schema.get("maximum", 100))
        seen = set()
        result = []
        for v in [mn, mn + 1, mx - 1, mx]:
            if v not in seen and mn <= v <= mx:
                seen.add(v)
                result.append(v)
        return result

    def _int_equiv(self) -> List[List[Any]]:
        mn = int(self.field_schema.get("minimum", 0))
        mx = int(self.field_schema.get("maximum", 100))
        mid = (mn + mx) // 2
        return [[mn], [mid], [mx]]

    def _int_invalid(self) -> List[Any]:
        mn = int(self.field_schema.get("minimum", 0))
        mx = int(self.field_schema.get("maximum", 100))
        return [mn - 1, mx + 1, "not_int", 3.14, None]

    # --- number ---

    def _float_boundary(self) -> List[Any]:
        mn = float(self.field_schema.get("minimum", 0.0))
        mx = float(self.field_schema.get("maximum", 100.0))
        epsilon = 0.01
        seen = set()
        result = []
        for v in [mn, round(mn + epsilon, 10), round(mx - epsilon, 10), mx]:
            if v not in seen and mn <= v <= mx:
                seen.add(v)
                result.append(v)
        return result

    def _float_equiv(self) -> List[List[Any]]:
        mn = float(self.field_schema.get("minimum", 0.0))
        mx = float(self.field_schema.get("maximum", 100.0))
        mid = round((mn + mx) / 2, 2)
        return [[mn], [mid], [mx]]

    def _float_invalid(self) -> List[Any]:
        mn = float(self.field_schema.get("minimum", 0.0))
        mx = float(self.field_schema.get("maximum", 100.0))
        return [round(mn - 0.01, 10), round(mx + 0.01, 10), "not_number", None]

    # --- string ---

    def _string_boundary(self) -> List[Any]:
        min_len = self.field_schema.get("minLength", 0)
        max_len = self.field_schema.get("maxLength", 10)
        result = []
        if min_len == 0:
            result.append("")
        if min_len > 0:
            result.append(''.join(random.choices(string.ascii_letters, k=min_len)))
        result.append(''.join(random.choices(string.ascii_letters, k=max_len)))
        return result

    def _string_equiv(self) -> List[List[Any]]:
        min_len = self.field_schema.get("minLength", 0)
        max_len = self.field_schema.get("maxLength", 10)
        mid_len = max(1, (min_len + max_len) // 2)
        classes = []
        if min_len > 0:
            classes.append([''.join(random.choices(string.ascii_letters, k=min_len))])
        else:
            classes.append([""])
        classes.append([''.join(random.choices(string.ascii_letters, k=mid_len))])
        classes.append([''.join(random.choices(string.ascii_letters, k=max_len))])
        return classes

    def _string_invalid(self) -> List[Any]:
        min_len = self.field_schema.get("minLength", 0)
        max_len = self.field_schema.get("maxLength", 10)
        result = []
        if min_len > 0:
            result.append(''.join(random.choices(string.ascii_letters, k=max(0, min_len - 1))))
        else:
            # minLength=0 无法生成更短的字符串，跳过
            pass
        result.append(''.join(random.choices(string.ascii_letters, k=max_len + 10)))
        result.append(12345)
        result.append(None)
        return result
