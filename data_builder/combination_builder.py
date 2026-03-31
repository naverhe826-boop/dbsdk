"""组合模式构建器模块

封装组合测试数据生成逻辑。
"""

import itertools
import random
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import DataBuilder

from .combinations import CombinationEngine, CombinationMode, CombinationSpec
from .strategies.structure import SchemaAwareStrategy


class CombinationBuilder:
    """组合模式构建器
    
    封装组合测试数据生成逻辑：分组、值域收集、笛卡尔积合并。
    """
    
    def __init__(self, builder: 'DataBuilder'):
        self.builder = builder
    
    def build(self, specs: List[CombinationSpec], count: Optional[int]) -> List[dict]:
        """组合模式构建（支持分层 scope）"""
        # 按 scope 分组字段
        groups = self._group_fields_by_scope(specs)

        if not groups:
            # 无可枚举字段，退化为普通生成
            effective_count = count if count is not None else self.builder.config.count or 1
            return [self.builder._build_single(i) for i in range(effective_count)]

        # 每组独立生成组合
        group_combos = {}
        for scope, (fields, spec) in groups.items():
            domains = self._collect_domains(fields, spec.mode)
            if domains:
                engine = CombinationEngine()
                if spec.mode == CombinationMode.INVALID:
                    normal = spec.normal_values or self._collect_normal_values(fields)
                    group_combos[scope] = engine.generate(domains, spec, normal_values=normal)
                else:
                    group_combos[scope] = engine.generate(domains, spec)

        if not group_combos:
            effective_count = count if count is not None else self.builder.config.count or 1
            return [self.builder._build_single(i) for i in range(effective_count)]

        # 跨组笛卡尔积合并
        merged_combos = self._cartesian_merge_groups(group_combos)

        if not merged_combos:
            effective_count = count if count is not None else self.builder.config.count or 1
            return [self.builder._build_single(i) for i in range(effective_count)]

        # count 处理
        if count is not None:
            if count < len(merged_combos):
                merged_combos = random.sample(merged_combos, count)
            elif count > len(merged_combos):
                extra = [
                    merged_combos[random.randrange(len(merged_combos))]
                    for _ in range(count - len(merged_combos))
                ]
                merged_combos = merged_combos + extra

        # 填充完整对象
        results = []
        for i, overrides in enumerate(merged_combos):
            self.builder._current_overrides = overrides
            try:
                results.append(self.builder._build_single(i))
            finally:
                self.builder._current_overrides = None
        return results

    def _group_fields_by_scope(
        self, specs: List[CombinationSpec]
    ) -> Dict[Optional[str], tuple]:
        """按 scope 分组字段，返回 {scope: (fields, spec)}"""
        groups = {}
        for spec in specs:
            scope = spec.scope
            if spec.fields:
                fields = spec.fields
            else:
                # 自动选取 scope 范围内的所有可枚举字段
                fields = [
                    p for p in self.builder._policy_map.keys()
                    if self._match_scope(p, scope)
                ]
                # BOUNDARY/EQUIVALENCE/INVALID 模式下，也自动发现 schema 中的基本类型字段
                if spec.mode in (CombinationMode.BOUNDARY, CombinationMode.EQUIVALENCE, CombinationMode.INVALID):
                    schema_fields = self._discover_schema_fields(scope)
                    for sf in schema_fields:
                        if sf not in fields:
                            fields.append(sf)
            if fields:
                groups[scope] = (fields, spec)
        return groups

    def _match_scope(self, path: str, scope: Optional[str]) -> bool:
        """判断 path 是否属于 scope"""
        if scope is None:
            # 顶层字段：不包含 '.'
            return "." not in path
        # 嵌套字段：以 scope. 开头
        return path.startswith(scope + ".")

    def _collect_domains(
        self, fields: List[str], mode: CombinationMode
    ) -> Dict[str, List[Any]]:
        """收集字段值域"""
        domains = {}
        for path in fields:
            # 使用 _find_strategy 支持通配符匹配
            strategy = self.builder._find_strategy(path)
            if strategy is None:
                # 无策略时，尝试从 schema 构建 SchemaAwareStrategy
                if mode in (CombinationMode.BOUNDARY, CombinationMode.EQUIVALENCE, CombinationMode.INVALID):
                    field_schema = self._resolve_field_schema(path)
                    if field_schema:
                        strategy = SchemaAwareStrategy(field_schema)
                    else:
                        continue
                else:
                    continue

            if mode == CombinationMode.BOUNDARY:
                vals = strategy.boundary_values()
            elif mode == CombinationMode.EQUIVALENCE:
                classes = strategy.equivalence_classes()
                vals = [c[0] for c in classes] if classes else None
            elif mode == CombinationMode.INVALID:
                vals = strategy.invalid_values()
            else:
                vals = strategy.values()

            if vals is not None:
                domains[path] = vals
        return domains

    def _collect_normal_values(self, fields: List[str]) -> Dict[str, Any]:
        """为 INVALID 模式收集各字段的正常值"""
        normal = {}
        for path in fields:
            strategy = self.builder._find_strategy(path)
            if strategy is None:
                field_schema = self._resolve_field_schema(path)
                if field_schema:
                    strategy = SchemaAwareStrategy(field_schema)
            if strategy is None:
                continue
            # 优先取等价类中间值
            classes = strategy.equivalence_classes()
            if classes:
                mid_idx = len(classes) // 2
                cls = classes[mid_idx]
                if cls:
                    normal[path] = cls[0]
                    continue
            # 其次取边界值第一个
            bv = strategy.boundary_values()
            if bv:
                normal[path] = bv[0]
                continue
        return normal

    def _resolve_field_schema(self, path: str) -> Optional[dict]:
        """根据路径从 schema 提取子 schema"""
        schema = self.builder._value_generator.schema_resolver.resolve(self.builder.schema)
        if not path:
            return schema
        parts = path.split(".")
        node = schema
        for part in parts:
            # 处理数组索引 field[0] -> field
            base = part.split("[")[0] if "[" in part else part
            props = node.get("properties", {})
            if base in props:
                node = self.builder._value_generator.schema_resolver.resolve(props[base])
                if "[" in part:
                    # 数组元素
                    node = self.builder._value_generator.schema_resolver.resolve(node.get("items", {}))
            else:
                return None
        return node

    def _discover_schema_fields(self, scope: Optional[str]) -> List[str]:
        """扫描 schema properties 提取基本类型字段路径"""
        basic_types = {"string", "integer", "number", "boolean"}
        if scope is None:
            schema = self.builder._value_generator.schema_resolver.resolve(self.builder.schema)
            prefix = ""
        else:
            schema = self._resolve_field_schema(scope)
            if not schema:
                return []
            prefix = scope + "."
        properties = schema.get("properties", {})
        result = []
        for name, prop_schema in properties.items():
            resolved = self.builder._value_generator.schema_resolver.resolve(prop_schema)
            if resolved.get("type") in basic_types:
                result.append(prefix + name)
        return result

    def _cartesian_merge_groups(
        self, group_combos: Dict[Optional[str], List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """跨组笛卡尔积合并"""
        if not group_combos:
            return []

        scopes = list(group_combos.keys())
        combo_lists = [group_combos[s] for s in scopes]

        merged = []
        for combo_tuple in itertools.product(*combo_lists):
            # 合并所有组的字段
            merged_row = {}
            for combo in combo_tuple:
                merged_row.update(combo)
            merged.append(merged_row)
        return merged
