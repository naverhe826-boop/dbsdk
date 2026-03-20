import re
from typing import Any, Callable, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import FieldPathError


class RefStrategy(Strategy):
    """引用其他字段策略"""

    def __init__(self, ref_path: str, transform: Optional[Callable] = None):
        self.ref_path = ref_path
        self.transform = transform

    def generate(self, ctx: StrategyContext) -> Any:
        value = self._get_value_by_path(ctx.root_data, self.ref_path)
        if self.transform:
            value = self.transform(value)
        return value

    def values(self) -> Optional[List[Any]]:
        """引用路径指向运行时数据，无法预知值域"""
        return None

    def boundary_values(self) -> Optional[List[Any]]:
        """引用无边界概念"""
        return None

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        """引用无法预分类"""
        return None

    def invalid_values(self) -> Optional[List[Any]]:
        """返回无效的引用场景"""
        return [
            None,  # 空引用
            "",  # 空路径
            "nonexistent.path",  # 不存在的路径
            "..",  # 路径解析会失败的格式
            ".",  # 路径解析会失败的格式
            "a[b",  # 格式错误的数组索引
            "a]b",  # 格式错误的数组索引
        ]

    def _get_value_by_path(self, data: dict, path: str) -> Any:
        parts = path.split('.')
        current = data
        traversed = []
        for part in parts:
            match = re.match(r'(\w+)\[(\d+)\]', part)
            try:
                if match:
                    key, idx = match.groups()
                    current = current[key][int(idx)]
                else:
                    current = current[part]
            except (KeyError, IndexError, TypeError):
                traversed_str = ".".join(traversed) or "(root)"
                raise FieldPathError(
                    f"RefStrategy: 路径 '{path}' 在 '{traversed_str}' 处找不到节点 '{part}'"
                )
            traversed.append(part)
        return current
