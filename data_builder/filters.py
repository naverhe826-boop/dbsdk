import warnings
from typing import Callable, Dict, List, Set, Tuple


def deduplicate(key_fields: List[str]) -> Callable[[List[dict]], List[dict]]:
    """按指定字段去重"""
    def _filter(rows: List[dict]) -> List[dict]:
        seen: Set[Tuple] = set()
        result = []
        for row in rows:
            key = tuple(row.get(f) for f in key_fields)
            if key not in seen:
                seen.add(key)
                result.append(row)
        return result
    return _filter


def constraint_filter(predicate: Callable[[dict], bool]) -> Callable[[List[dict]], List[dict]]:
    """条件过滤"""
    def _filter(rows: List[dict]) -> List[dict]:
        result = []
        for r in rows:
            try:
                if bool(predicate(r)):
                    result.append(r)
            except Exception as e:
                warnings.warn(f"constraint_filter: predicate 抛出异常，跳过该行: {e}")
                continue
        return result
    return _filter


def limit(max_count: int) -> Callable[[List[dict]], List[dict]]:
    """截断"""
    max_count = max(0, max_count)  # 确保非负
    def _filter(rows: List[dict]) -> List[dict]:
        return rows[:max_count]
    return _filter


def tag_rows(tag_field: str = "_tag", tag_value: str = "") -> Callable[[List[dict]], List[dict]]:
    """为每行添加标记字段（返回新列表，不修改原始数据）"""
    def _filter(rows: List[dict]) -> List[dict]:
        return [{**row, tag_field: tag_value} for row in rows]
    return _filter
