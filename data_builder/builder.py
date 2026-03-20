"""数据构建器核心模块

提供 JSON Schema 测试数据生成的主入口。
"""

import fnmatch
import random
import re
from typing import Any, Dict, List, Optional, Union

from .config import BuilderConfig, FieldPolicy
from .generators import ValueGenerator
from .combination_builder import CombinationBuilder
from .strategies.basic import Strategy
from .combinations import CombinationMode, CombinationSpec


class DataBuilder:
    """数据构建器核心类
    
    通过组合 ValueGenerator 和 CombinationBuilder 实现数据生成。
    """

    @classmethod
    def config_from_dict(cls, config_dict: Dict[str, Any]) -> BuilderConfig:
        """
        从配置字典创建 BuilderConfig（便捷方法）。

        与 BuilderConfig.from_dict 等价，但只需要导入 DataBuilder。

        :param config_dict: 配置字典
        :return: BuilderConfig 实例
        """
        return BuilderConfig.from_dict(config_dict)

    def __init__(self, schema: dict, config: Optional[BuilderConfig] = None):
        self.schema = schema
        self.config = config or BuilderConfig()
        self._policy_map: Dict[str, Strategy] = {
            p.path: p.strategy for p in self.config.policies
        }
        self._current_overrides: Optional[Dict[str, Any]] = None
        # 当 max_depth 为 None 时，用于检测生成过程中的循环引用
        # 存储当前生成路径上遇到的 $ref 路径栈
        self._generation_ref_stack: List[str] = []
        
        # 组合其他模块
        self._value_generator = ValueGenerator(self)
        self._combination_builder = CombinationBuilder(self)

    def build(self, count: Optional[int] = None) -> Union[dict, List[dict]]:
        """
        构建数据
        count: 显式传入优先，其次 config.count，均为 None 时返回单个对象
        """
        specs = self.config.combinations

        if specs and any(s.mode != CombinationMode.RANDOM for s in specs):
            results = self._combination_builder.build(specs, count)
        else:
            effective_count = count if count is not None else self.config.count
            if effective_count is None:
                result = self._build_single(0)
                # 单对象也支持后置过滤
                if self.config.post_filters:
                    results = [result]
                    for f in self.config.post_filters:
                        results = f(results)
                    if not results:
                        return None
                    return results[0] if len(results) == 1 else results
                return result
            results = [self._build_single(i) for i in range(effective_count)]

        # 后置过滤
        if isinstance(results, list) and self.config.post_filters:
            for f in self.config.post_filters:
                results = f(results)
        return results

    def _build_single(self, index: int) -> Any:
        """构建单个数据对象或值"""
        root_data = {}
        result = self._value_generator.generate_value(
            schema=self.schema,
            path="",
            root_data=root_data,
            parent_data=root_data,
            index=index,
            depth=0
        )
        
        # 如果 result 是字典（可能是 example），优先返回 result
        if isinstance(result, dict):
            return result
        
        # 如果 root_data 非空，使用 root_data（用于对象类型 schema）
        if root_data:
            return root_data
        
        # 否则返回 result（用于联合类型等非对象类型 schema）
        return result

    def _find_strategy(self, path: str) -> Optional[Strategy]:
        """查找匹配的策略（支持通配符）"""
        # 精确匹配优先
        if path in self._policy_map:
            return self._policy_map[path]

        # 通配符匹配
        for pattern, strategy in self._policy_map.items():
            if self._match_path(path, pattern):
                return strategy

        return None

    def _match_path(self, path: str, pattern: str) -> bool:
        """路径通配符匹配"""

        # 处理 user.* 匹配 user.name, user.age 等
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if path.startswith(prefix + "."):
                remaining = path[len(prefix) + 1:]
                # 只匹配直接子级
                if "." not in remaining and "[" not in remaining:
                    return True

        # 处理 [*] 数组通配符
        if "[*]" in pattern:
            # 先转义全部特殊字符，再还原通配符部分
            regex_pattern = re.escape(pattern).replace(r"\[\*\]", r"\[\d+\]")
            return bool(re.match(f"^{regex_pattern}$", path))

        return fnmatch.fnmatch(path, pattern)
