import itertools
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .exceptions import SchemaError


class CombinationMode(Enum):
    RANDOM = "random"
    CARTESIAN = "cartesian"
    PAIRWISE = "pairwise"
    ORTHOGONAL = "orthogonal"
    EQUIVALENCE = "equivalence"
    BOUNDARY = "boundary"
    INVALID = "invalid"


@dataclass
class Constraint:
    predicate: Callable[[Dict[str, Any]], bool]
    description: str = ""


@dataclass
class CombinationSpec:
    mode: CombinationMode = CombinationMode.RANDOM
    fields: Optional[List[str]] = None
    scope: Optional[str] = None  # 路径前缀，None 表示顶层
    constraints: List[Constraint] = field(default_factory=list)
    strength: int = 2
    normal_values: Optional[Dict[str, Any]] = None  # INVALID 模式下其他字段的正常填充值


class CombinationEngine:

    def generate(
        self,
        domains: Dict[str, List[Any]],
        spec: CombinationSpec,
        normal_values: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not domains:
            return []

        mode = spec.mode
        if mode == CombinationMode.CARTESIAN:
            rows = self._cartesian(domains)
        elif mode == CombinationMode.PAIRWISE:
            rows = self._t_way(domains, t=2)
        elif mode == CombinationMode.ORTHOGONAL:
            rows = self._t_way(domains, t=spec.strength)
        elif mode in (CombinationMode.EQUIVALENCE, CombinationMode.BOUNDARY):
            # 值域由调用方已替换为等价类/边界值，引擎内部做笛卡尔积
            rows = self._cartesian(domains)
        elif mode == CombinationMode.INVALID:
            rows = self._one_invalid_at_a_time(domains, normal_values or {})
        else:
            rows = self._cartesian(domains)

        # 应用约束过滤
        if spec.constraints:
            rows = [
                r for r in rows
                if all(c.predicate(r) for c in spec.constraints)
            ]
        return rows

    _CARTESIAN_LIMIT = 10_000   # 笛卡尔积最大生成1万个数据

    def _cartesian(self, domains: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        keys = list(domains.keys())
        value_lists = [domains[k] for k in keys]
        total = 1
        for vl in value_lists:
            total *= len(vl)
            if total > self._CARTESIAN_LIMIT:
                raise SchemaError(
                    f"笛卡尔积结果集过大（>{self._CARTESIAN_LIMIT}），请改用 PAIRWISE 模式"
                )
        return [dict(zip(keys, combo)) for combo in itertools.product(*value_lists)]

    def _t_way(
        self, domains: Dict[str, List[Any]], t: int
    ) -> List[Dict[str, Any]]:
        """贪心覆盖算法：覆盖所有 t-元组"""
        keys = list(domains.keys())
        if t > len(keys):
            t = len(keys)

        # 收集所有需要覆盖的 t-元组
        uncovered = set()
        for combo_keys in itertools.combinations(range(len(keys)), t):
            value_lists = [domains[keys[i]] for i in combo_keys]
            for val_combo in itertools.product(*value_lists):
                uncovered.add((combo_keys, val_combo))

        rows: List[Dict[str, Any]] = []
        value_lists_all = [domains[k] for k in keys]
        all_candidates_size = 1
        for vl in value_lists_all:
            all_candidates_size *= len(vl)

        # 阈值：候选空间小于 10000 时全量枚举
        THRESHOLD = 10000
        if all_candidates_size <= THRESHOLD:
            all_candidates = [
                dict(zip(keys, combo))
                for combo in itertools.product(*value_lists_all)
            ]
        else:
            all_candidates = None

        while uncovered:
            best_row = None
            best_count = 0

            if all_candidates is not None:
                # 全量枚举找最优
                for candidate in all_candidates:
                    count = self._count_coverage(candidate, keys, uncovered, t)
                    if count > best_count:
                        best_count = count
                        best_row = candidate
            else:
                # 随机采样找近似最优
                sample_size = min(1000, all_candidates_size)
                for _ in range(sample_size):
                    candidate = {
                        k: random.choice(domains[k]) for k in keys
                    }
                    count = self._count_coverage(candidate, keys, uncovered, t)
                    if count > best_count:
                        best_count = count
                        best_row = candidate

            if best_row is None:
                break

            # 移除已覆盖的元组
            for combo_keys in itertools.combinations(range(len(keys)), t):
                val_tuple = tuple(best_row[keys[i]] for i in combo_keys)
                uncovered.discard((combo_keys, val_tuple))

            rows.append(best_row)

        return rows

    @staticmethod
    def _count_coverage(
        candidate: Dict[str, Any],
        keys: List[str],
        uncovered: set,
        t: int,
    ) -> int:
        count = 0
        for combo_keys in itertools.combinations(range(len(keys)), t):
            val_tuple = tuple(candidate[keys[i]] for i in combo_keys)
            if (combo_keys, val_tuple) in uncovered:
                count += 1
        return count

    @staticmethod
    def _one_invalid_at_a_time(
        invalid_domains: Dict[str, List[Any]],
        normal_values: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """轮流非法：每次只有一个字段取非法值，其余字段取正常值"""
        all_fields = list(invalid_domains.keys())
        rows = []
        for target_field in all_fields:
            for inv_val in invalid_domains[target_field]:
                row = {f: normal_values.get(f) for f in all_fields}
                row[target_field] = inv_val
                rows.append(row)
        return rows
