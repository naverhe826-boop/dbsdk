from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


@dataclass
class StrategyContext:
    """策略执行上下文"""
    field_path: str  # 当前字段路径，如 "user.name"
    field_schema: dict  # 当前字段的 schema
    root_data: dict = field(default_factory=dict)  # 根数据对象
    parent_data: Union[dict, list] = field(default_factory=dict)  # 父级数据（对象为 dict，数组为 list）
    index: int = 0  # 当前生成索引（批量生成时）


class Strategy(ABC):
    """策略抽象基类"""

    @abstractmethod
    def generate(self, ctx: StrategyContext) -> Any:
        """生成数据"""
        pass

    def values(self) -> Optional[List[Any]]:
        """完整值域。None = 不可枚举"""
        return None

    def boundary_values(self) -> Optional[List[Any]]:
        """边界值。None = 无边界概念"""
        return None

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        """等价类分组。None = 不支持"""
        return None

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值（违反约束的值）。None = 不支持"""
        return None


class StructureStrategy(Strategy):
    """结构控制策略基类

    与 Strategy（值策略）的区别：
    - 值策略：generate() 返回字段最终值
    - 结构策略：generate() 返回结构控制参数（如数组数量），由 builder 解释执行
    """
    pass
