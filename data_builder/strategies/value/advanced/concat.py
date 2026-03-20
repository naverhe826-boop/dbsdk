from itertools import product
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class ConcatStrategy(Strategy):
    """级联合并策略：将多个子策略生成的值按顺序连接起来"""

    def __init__(
        self,
        strategies: List[Union[Strategy, dict]],
        separators: Optional[List[str]] = None
    ):
        """
        初始化 ConcatStrategy

        Args:
            strategies: 子策略列表，支持：
                - 已实例化的 Strategy 对象
                - 配置字典列表（需用 StrategyRegistry.create() 实例化）
            separators: 分隔符列表，默认空字符串
                - 只有一个 separator 时，复用于所有连接位置
                - 多个时需与 strategies 长度匹配（n-1 个分隔符）
        """
        if not strategies:
            raise StrategyError("ConcatStrategy: strategies 不能为空")

        # 处理 strategies：支持 Strategy 对象或配置字典
        self.strategies: List[Strategy] = []
        for s in strategies:
            if isinstance(s, dict):
                # 延迟导入，避免循环依赖
                from ..registry import StrategyRegistry
                self.strategies.append(StrategyRegistry.create(s))
            elif isinstance(s, Strategy):
                self.strategies.append(s)
            else:
                raise StrategyError(
                    f"ConcatStrategy: strategies 元素必须是 Strategy 实例或配置字典，"
                    f"得到: {type(s)}"
                )

        # 处理 separators
        if separators is None:
            separators = []
        
        self._separators = separators

    @property
    def separators(self) -> List[str]:
        """获取处理后的 separators 列表"""
        if len(self._separators) == 1:
            # 只有一个 separator 时，复用于所有连接位置
            return self._separators * (len(self.strategies) - 1)
        elif len(self._separators) == len(self.strategies) - 1:
            # 数量匹配
            return self._separators
        elif len(self._separators) == 0:
            # 默认空字符串
            return [''] * (len(self.strategies) - 1)
        else:
            raise StrategyError(
                f"ConcatStrategy: separators 数量({len(self._separators)}) "
                f"必须与连接位置数量({len(self.strategies) - 1}) 匹配，或为 1 个"
            )

    def generate(self, ctx: StrategyContext) -> str:
        """遍历子策略调用 generate(ctx)，根据 separators 拼接结果"""
        # 校验字段类型：concat 策略仅支持 string 类型
        field_type = ctx.field_schema.get("type") if ctx.field_schema else None
        if field_type and field_type != "string":
            raise StrategyError(
                f"ConcatStrategy: 字段类型必须是 string，当前类型为 {field_type!r}"
            )
        
        parts = []
        for i, strategy in enumerate(self.strategies):
            value = strategy.generate(ctx)
            parts.append(str(value))
            if i < len(self.strategies) - 1:
                parts.append(self.separators[i])
        return ''.join(parts)

    def values(self) -> Optional[List[str]]:
        """若所有子策略都可枚举，返回笛卡尔积；否则返回 None"""
        # 获取每个子策略的值列表
        values_lists = []
        for strategy in self.strategies:
            vals = strategy.values()
            if vals is None:
                # 任何子策略不可枚举，则整体不可枚举
                return None
            values_lists.append(vals)

        # 计算笛卡尔积
        result = []
        for combination in product(*values_lists):
            # 拼接每个部分的字符串
            parts = []
            for i, val in enumerate(combination):
                parts.append(str(val))
                if i < len(combination) - 1:
                    parts.append(self.separators[i])
            result.append(''.join(parts))
        return result

    def boundary_values(self) -> Optional[List[str]]:
        """边界值：使用各子策略的边界值进行组合"""
        # 获取每个子策略的边界值
        boundary_lists = []
        for strategy in self.strategies:
            bv = strategy.boundary_values()
            if bv is None:
                return None
            boundary_lists.append(bv)

        # 取每个子策略的第一个和最后一个边界值进行组合
        result = []
        # 首尾组合
        for i in range(len(boundary_lists)):
            boundary = boundary_lists[i]
            # 简化处理：取最小和最大值
            for b in [boundary[0], boundary[-1] if len(boundary) > 1 else boundary[0]]:
                result.append(str(b))
        
        # 如果只有一个子策略，直接返回其边界值
        if len(boundary_lists) == 1:
            return [str(b) for b in boundary_lists[0]]

        # 构造一些典型组合
        parts = []
        for i, boundary in enumerate(boundary_lists):
            parts.append(str(boundary[0] if boundary else ''))
            if i < len(boundary_lists) - 1:
                parts.append(self.separators[i])
        result.append(''.join(parts))
        
        return result[:10]  # 限制数量

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组：基于子策略的等价类进行组合"""
        # 获取每个子策略的等价类
        classes_lists = []
        for strategy in self.strategies:
            ec = strategy.equivalence_classes()
            if ec is None:
                return None
            classes_lists.append(ec)

        # 简化处理：每个子策略取第一个等价类进行组合
        result = []
        parts = []
        for i, classes in enumerate(classes_lists):
            if classes and len(classes) > 0:
                parts.append(str(classes[0][0] if classes[0] else ''))
            else:
                parts.append('')
            if i < len(classes_lists) - 1:
                parts.append(self.separators[i])
        result.append(''.join(parts))
        
        return result

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值：收集各子策略的非法值进行组合"""
        invalid_lists = []
        for strategy in self.strategies:
            iv = strategy.invalid_values()
            if iv is None:
                return None
            invalid_lists.append(iv)

        # 取各子策略的第一个非法值进行组合
        if not invalid_lists:
            return None
            
        result = []
        parts = []
        for i, invalid in enumerate(invalid_lists):
            if invalid:
                parts.append(str(invalid[0]))
            else:
                parts.append('')
            if i < len(invalid_lists) - 1:
                parts.append(self.separators[i])
        result.append(''.join(parts))
        
        return result
