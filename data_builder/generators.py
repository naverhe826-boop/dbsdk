"""值生成器模块

封装 Schema 解析和值生成逻辑。
"""

import copy
import random
import re
import string
import warnings
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import DataBuilder

from .exceptions import SchemaError
from .strategies.basic import Strategy, StrategyContext, StructureStrategy
from .strategies.structure import (
    SchemaAwareStrategy,
    PropertyCountStrategy,
    PropertySelectionStrategy,
    ContainsCountStrategy,
    SchemaSelectionStrategy,
)


class SchemaResolver:
    """Schema 解析器
    
    封装 schema 预处理逻辑：$ref 解析、allOf 合并、if/then/else、not 等。
    """
    
    def __init__(self, builder: 'DataBuilder'):
        self.builder = builder
    
    def resolve(self, schema: dict, _seen: Optional[Set[str]] = None, depth: int = 0) -> dict:
        """预处理 schema：解析 $ref 引用、合并 allOf
        
        _seen 用于检测同一 schema 解析链中的循环引用
        _generation_ref_stack 用于检测跨值生成调用的循环引用（由 ValueGenerator 管理）
        """
        # 初始化 _seen 集合（用于单次 schema 解析链中的引用检测）
        if _seen is None:
            _seen = set()

        # $ref 解析
        if "$ref" in schema:
            ref_path = schema["$ref"]
            
            # 检测 schema 解析链中的循环引用
            if ref_path in _seen:
                if self.builder.config.max_depth is not None:
                    # 启用 max_depth 时，返回截断值
                    return {"type": "object"}
                else:
                    # 未启用 max_depth 时，抛出错误
                    raise SchemaError(f"循环引用: {ref_path}")
            
            resolved = self._resolve_ref(ref_path)
            if len(schema) > 1:
                extra = {k: v for k, v in schema.items() if k != "$ref"}
                resolved = self._merge_schemas(resolved, extra)
            return self.resolve(resolved, _seen | {ref_path}, depth)

        # allOf 合并
        if "allOf" in schema:
            base = {k: v for k, v in schema.items() if k != "allOf"}
            for sub in schema["allOf"]:
                sub = self.resolve(sub, _seen, depth)
                base = self._merge_schemas(base, sub)
            # 有 properties 但无 type 时推断为 object
            if "properties" in base and "type" not in base:
                base["type"] = "object"
            return base

        # if/then/else 条件 schema
        if "if" in schema:
            base = {k: v for k, v in schema.items() if k not in ("if", "then", "else")}
            use_then = random.random() < 0.5
            if use_then and "then" in schema:
                merged = self._merge_schemas(
                    self._merge_schemas(base, schema["if"]), schema["then"]
                )
            elif not use_then and "else" in schema:
                merged = self._merge_schemas(base, schema["else"])
            else:
                merged = base
            return self.resolve(merged, _seen, depth)

        # not（有限子集）
        if "not" in schema:
            not_schema = schema["not"]
            base = {k: v for k, v in schema.items() if k != "not"}

            # 策略：排除 not 中定义的类型，如果类型已完全排除则使用其他策略
            if "type" in not_schema:
                excluded = not_schema["type"] if isinstance(not_schema["type"], list) else [not_schema["type"]]
                # 获取当前 base 中已定义的类型
                current_types = base.get("type")
                if current_types is None:
                    # base 没有 type，随机选择一个非排除类型
                    alt = [t for t in ["string", "integer", "number", "boolean", "null"] if t not in excluded]
                    if alt:
                        base["type"] = random.choice(alt)
                elif isinstance(current_types, list):
                    # 如果是联合类型，排除 not 中的类型
                    alt = [t for t in current_types if t not in excluded]
                    if alt:
                        base["type"] = alt
                    else:
                        # 所有类型都被排除，随机选择一个其他类型
                        base["type"] = random.choice([t for t in ["string", "integer", "number", "boolean", "null"] if t not in excluded])
                elif current_types:
                    # 如果是单一类型且被排除，随机选择另一个类型
                    if current_types in excluded:
                        alt = [t for t in ["string", "integer", "number", "boolean", "null"] if t not in excluded]
                        if alt:
                            base["type"] = random.choice(alt)
                        else:
                            # 所有类型都被排除（极端情况），移除 type 限制
                            base.pop("type", None)

            # 处理 enum：标记为排除的枚举值
            if "enum" in not_schema:
                base.setdefault("_excluded_enum", []).extend(not_schema["enum"])

            return self.resolve(base, _seen, depth)

        return schema

    def _resolve_ref(self, ref_path: str) -> dict:
        """根据 $ref 路径从根 schema 取定义"""
        if not ref_path.startswith("#/"):
            raise SchemaError(f"仅支持内部 $ref 引用: {ref_path}")
        parts = ref_path[2:].split("/")
        node = self.builder.schema
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                raise SchemaError(f"$ref 路径未找到: {ref_path}")
        # 使用深拷贝避免循环引用导致的 RecursionError 和嵌套对象意外共享
        if isinstance(node, dict):
            return copy.deepcopy(node)
        return copy.deepcopy(node)

    def _merge_schemas(self, base: dict, override: dict) -> dict:
        """合并两个 schema（properties/required 深度合并，其余覆盖）"""
        result = dict(base)
        for key, value in override.items():
            if key == "properties" and "properties" in result:
                merged_props = dict(result["properties"])
                merged_props.update(value)
                result["properties"] = merged_props
            elif key == "required" and "required" in result:
                merged_req = list(result["required"])
                for item in value:
                    if item not in merged_req:
                        merged_req.append(item)
                result["required"] = merged_req
            else:
                result[key] = value
        return result


class ValueGenerator:
    """值生成器
    
    封装值生成逻辑：对象、数组、基本类型的生成。
    """
    
    def __init__(self, builder: 'DataBuilder'):
        self.builder = builder
        self.schema_resolver = SchemaResolver(builder)
    
    def generate_value(
        self,
        schema: dict,
        path: str,
        root_data: dict,
        parent_data: dict,
        index: int,
        depth: int = 0
    ) -> Any:
        """递归生成值"""
        # 当 max_depth 未启用时，在值生成层面管理 $ref 栈以检测循环引用
        ref_path_to_pop = None
        if self.builder.config.max_depth is None and "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path in self.builder._generation_ref_stack:
                # 检测到生成过程中的循环引用
                raise SchemaError(f"循环引用: {ref_path}")
            # 压栈
            self.builder._generation_ref_stack.append(ref_path)
            ref_path_to_pop = ref_path
        
        try:
            # schema 预处理：$ref 解析 + allOf 合并
            schema = self.schema_resolver.resolve(schema, depth=depth)

            # 深度检查：达到 max_depth 时返回默认值
            if self.builder.config.max_depth is not None and depth >= self.builder.config.max_depth:
                schema_type = schema.get("type", "string")
                if isinstance(schema_type, list):
                    non_null = [t for t in schema_type if t != "null"]
                    schema_type = non_null[0] if non_null else "null"
                if schema_type == "object":
                    return {}
                elif schema_type == "array":
                    return []
                else:
                    return None

            # 调用内部生成逻辑
            return self._generate_value_inner(schema, path, root_data, parent_data, index, depth)
        finally:
            # 弹栈：确保在异常情况下也能正确清理
            if ref_path_to_pop is not None:
                if self.builder._generation_ref_stack and self.builder._generation_ref_stack[-1] == ref_path_to_pop:
                    self.builder._generation_ref_stack.pop()

    def _generate_value_inner(
        self,
        schema: dict,
        path: str,
        root_data: dict,
        parent_data: dict,
        index: int,
        depth: int = 0
    ) -> Any:
        """值生成的内部实现（$ref 已解析，栈已管理）"""

        # 组合模式 override 检查
        if self.builder._current_overrides and path in self.builder._current_overrides:
            return self.builder._current_overrides[path]

        # 检查 null 概率
        if self.builder.config.null_probability > 0 and random.random() < self.builder.config.null_probability:
            is_nullable = schema.get("nullable", False)
            # nullable 可以是布尔值或类型数组（Draft 4-6）
            if isinstance(is_nullable, list) and "null" in is_nullable:
                is_nullable = True
            if not is_nullable:
                schema_type = schema.get("type")
                if isinstance(schema_type, list) and "null" in schema_type:
                    is_nullable = True
            if is_nullable:
                return None

        # 查找匹配的策略
        strategy = self.builder._find_strategy(path)
        if strategy:
            # SchemaSelectionStrategy：oneOf/anyOf 分支选择
            if isinstance(strategy, SchemaSelectionStrategy):
                branches = schema.get("oneOf") or schema.get("anyOf")
                if branches:
                    ctx = StrategyContext(
                        field_path=path, field_schema=schema,
                        root_data=root_data, parent_data=parent_data, index=index
                    )
                    idx = strategy.generate(ctx)
                    idx = max(0, min(idx, len(branches) - 1))
                    selected = self.schema_resolver.resolve(branches[idx], depth=depth)
                    return self.generate_value(selected, path, root_data, parent_data, index, depth)
                # 无 oneOf/anyOf 时 fall through 到默认生成

            elif isinstance(strategy, StructureStrategy):
                schema_type = schema.get("type")
                if schema_type == "array":
                    return self._generate_array(schema, path, root_data, parent_data, index, depth, strategy)
                elif schema_type == "object":
                    return self._generate_object(schema, path, root_data, parent_data, index, depth, strategy)
            else:
                ctx = StrategyContext(
                    field_path=path,
                    field_schema=schema,
                    root_data=root_data,
                    parent_data=parent_data,
                    index=index
                )
                return strategy.generate(ctx)

        # oneOf / anyOf：随机选一个子 schema 生成
        if "oneOf" in schema:
            selected = random.choice(schema["oneOf"])
            return self.generate_value(
                self.schema_resolver.resolve(selected, depth=depth), path, root_data, parent_data, index, depth
            )
        if "anyOf" in schema:
            selected = random.choice(schema["anyOf"])
            return self.generate_value(
                self.schema_resolver.resolve(selected, depth=depth), path, root_data, parent_data, index, depth
            )

        # 无策略时根据 schema 类型生成默认值
        if self.builder.config.strict_mode and path:
            from .exceptions import StrategyNotFoundError
            raise StrategyNotFoundError(f"strict_mode: 字段 '{path}' 未配置策略")

        # 从 schema 推导类型
        schema_type = schema.get("type")
        if schema_type is None:
            # 从 enum/const 推导类型
            if "enum" in schema and schema["enum"]:
                first_value = schema["enum"][0]
                schema_type = type(first_value).__name__
            elif "const" in schema:
                schema_type = type(schema["const"]).__name__
            else:
                # 默认为 object
                schema_type = "object"

        # 联合类型：type 为数组时，如 ["string", "null"]
        if isinstance(schema_type, list):
            non_null = [t for t in schema_type if t != "null"]
            if not non_null:
                return None
            
            # 根据配置的优先级选择类型
            if self.builder.config.union_type_priority:
                # 按优先级顺序查找第一个可用的类型
                for priority_type in self.builder.config.union_type_priority:
                    if priority_type in non_null:
                        schema_type = priority_type
                        break
                else:
                    # 无优先级匹配，使用随机选择
                    schema_type = random.choice(non_null)
            else:
                schema_type = random.choice(non_null)

        if schema_type == "object":
            return self._generate_object(schema, path, root_data, parent_data, index, depth)
        elif schema_type == "array":
            return self._generate_array(schema, path, root_data, parent_data, index, depth)
        else:
            return self._generate_primitive(schema, schema_type, path)

    def _generate_object(
        self,
        schema: dict,
        path: str,
        root_data: dict,
        parent_data: dict,
        index: int,
        depth: int = 0,
        strategy: Optional[StructureStrategy] = None,
    ) -> dict:
        """生成对象"""
        result = {}
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        additional_schema = schema.get("additionalProperties")
        
        # 对象级别的 example 作为基础值
        base_example = None
        if "examples" in schema:
            examples = schema["examples"]
            if isinstance(examples, list) and examples:
                example = random.choice(examples)
                if isinstance(example, dict):
                    base_example = example
        elif "example" in schema:
            example = schema["example"]
            if isinstance(example, dict):
                base_example = example
        
        # 如果有 example，先填充 example 值作为基础
        if base_example:
            result.update(base_example)

        if isinstance(strategy, PropertySelectionStrategy):
            # 只生成指定的属性列表
            ctx = StrategyContext(
                field_path=path, field_schema=schema,
                root_data=root_data, parent_data=parent_data, index=index
            )
            selected_names = strategy.generate(ctx)
            for prop_name in selected_names:
                prop_path = f"{path}.{prop_name}" if path else prop_name
                if prop_name in properties:
                    value = self.generate_value(
                        schema=properties[prop_name], path=prop_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                elif isinstance(additional_schema, dict):
                    value = self.generate_value(
                        schema=additional_schema, path=prop_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                else:
                    continue
                result[prop_name] = value
                if not path:
                    root_data[prop_name] = value

        elif isinstance(strategy, PropertyCountStrategy):
            # 控制属性数量
            ctx = StrategyContext(
                field_path=path, field_schema=schema,
                root_data=root_data, parent_data=parent_data, index=index
            )
            count = strategy.generate(ctx)
            count = max(count, len(required))

            # required 必选
            selected = list(required)
            # optional 随机补齐
            optional = [k for k in properties if k not in required]
            need = count - len(selected)
            if need > 0:
                if need >= len(optional):
                    selected.extend(optional)
                else:
                    selected.extend(random.sample(optional, need))

            # 从 properties 中生成
            props_to_gen = [n for n in selected if n in properties]
            additional_count = count - len(props_to_gen)

            for prop_name in props_to_gen:
                prop_path = f"{path}.{prop_name}" if path else prop_name
                value = self.generate_value(
                    schema=properties[prop_name], path=prop_path,
                    root_data=root_data, parent_data=result, index=index, depth=depth + 1
                )
                result[prop_name] = value
                if not path:
                    root_data[prop_name] = value

            # 超出 properties 时用 additionalProperties 补生成
            if additional_count > 0 and isinstance(additional_schema, dict):
                existing_keys = set(result.keys())
                for i in range(additional_count):
                    key = f"extra_{i}"
                    while key in existing_keys:
                        key = f"extra_{i}_{random.randint(0, 999)}"
                    prop_path = f"{path}.{key}" if path else key
                    value = self.generate_value(
                        schema=additional_schema, path=prop_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                    result[key] = value
                    if not path:
                        root_data[key] = value
                    existing_keys.add(key)

        else:
            # minProperties / maxProperties 支持
            min_p = schema.get("minProperties")
            max_p = schema.get("maxProperties")
            required_keys = list(required)
            optional_keys = [k for k in properties if k not in required]

            if min_p is not None or max_p is not None:
                # 确定目标属性数量
                lo = max(min_p or 0, len(required_keys))
                hi = min(max_p, len(properties)) if max_p is not None else len(properties)
                hi = max(lo, hi)
                target = random.randint(lo, hi)

                selected = list(required_keys)
                need = target - len(selected)
                if need > 0:
                    if need >= len(optional_keys):
                        selected.extend(optional_keys)
                    else:
                        selected.extend(random.sample(optional_keys, need))
                selected_set = set(selected)
            else:
                selected_set = set(properties.keys())

            for prop_name in properties:
                if prop_name not in selected_set:
                    continue
                
                prop_path = f"{path}.{prop_name}" if path else prop_name
                
                # 检查是否有 field_policies 覆盖该字段
                has_field_policy = self.builder._find_strategy(prop_path) is not None
                
                if has_field_policy:
                    # 如果有 field_policies，生成并覆盖 example 值
                    value = self.generate_value(
                        schema=properties[prop_name], path=prop_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                    result[prop_name] = value
                    if not path:
                        root_data[prop_name] = value
                elif prop_name in result:
                    # 如果没有 field_policies 且字段已在 example 中，保留 example 值
                    continue
                else:
                    # 如果没有 field_policies 且字段不在 example 中，按 schema 生成
                    value = self.generate_value(
                        schema=properties[prop_name], path=prop_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                    result[prop_name] = value
                    if not path:
                        root_data[prop_name] = value

            # additionalProperties：无 properties 时根据 additionalProperties schema 生成额外属性
            if not properties:
                if isinstance(additional_schema, dict):
                    count = random.randint(1, 3)
                    # propertyNames.pattern 控制键名
                    pn_pattern = (schema.get("propertyNames") or {}).get("pattern")
                    for i in range(count):
                        if pn_pattern:
                            import exrex
                            key = exrex.getone(pn_pattern)
                            # 避免重复键名
                            retry = 0
                            while key in result and retry < 10:
                                key = exrex.getone(pn_pattern)
                                retry += 1
                        else:
                            key = f"prop_{i}"
                        prop_path = f"{path}.{key}" if path else key
                        value = self.generate_value(
                            schema=additional_schema, path=prop_path,
                            root_data=root_data, parent_data=result, index=index, depth=depth + 1
                        )
                        result[key] = value
                        if not path:
                            root_data[key] = value

            # patternProperties：为每个 pattern 生成匹配键名
            for pp_pattern, pp_schema in schema.get("patternProperties", {}).items():
                import exrex
                key = exrex.getone(pp_pattern)
                if key not in result:
                    pp_path = f"{path}.{key}" if path else key
                    value = self.generate_value(
                        schema=pp_schema, path=pp_path,
                        root_data=root_data, parent_data=result, index=index, depth=depth + 1
                    )
                    result[key] = value
                    if not path:
                        root_data[key] = value

        # dependentRequired 后处理
        for trigger, deps in schema.get("dependentRequired", {}).items():
            if trigger in result:
                for dep in deps:
                    if dep not in result:
                        if dep in properties:
                            dep_path = f"{path}.{dep}" if path else dep
                            value = self.generate_value(
                                schema=properties[dep], path=dep_path,
                                root_data=root_data, parent_data=result, index=index, depth=depth + 1
                            )
                            result[dep] = value
                            if not path:
                                root_data[dep] = value

        # dependentSchemas 后处理
        for trigger, dep_schema in schema.get("dependentSchemas", {}).items():
            if trigger in result:
                resolved = self.schema_resolver.resolve(dep_schema, depth=depth)
                dep_props = resolved.get("properties", {})
                for k, v_schema in dep_props.items():
                    if k not in result:
                        k_path = f"{path}.{k}" if path else k
                        value = self.generate_value(
                            schema=v_schema, path=k_path,
                            root_data=root_data, parent_data=result, index=index, depth=depth + 1
                        )
                        result[k] = value
                        if not path:
                            root_data[k] = value

        # additionalProperties: false → 过滤掉非 properties 定义的键
        if additional_schema is False and properties:
            allowed_keys = set(properties.keys())
            # patternProperties 匹配的键也保留
            pattern_props = schema.get("patternProperties", {})
            if pattern_props:
                allowed_keys |= {
                    k for k in result
                    if any(re.search(p, k) for p in pattern_props)
                }
            result = {k: v for k, v in result.items() if k in allowed_keys}
            if not path:
                for k in list(root_data.keys()):
                    if k not in allowed_keys:
                        del root_data[k]

        return result

    def _generate_array(
        self,
        schema: dict,
        path: str,
        root_data: dict,
        parent_data: dict,
        index: int,
        depth: int = 0,
        strategy: Optional[Strategy] = None
    ) -> list:
        """生成数组"""
        from .strategies.structure.contains_count import ContainsCountStrategy
        from .strategies.structure.array_count import ArrayCountStrategy

        items_schema = schema.get("items", {"type": "string"})
        prefix_items = schema.get("prefixItems", [])
        contains_schema = schema.get("contains")

        # ContainsCountStrategy：控制 contains 元素数量
        if isinstance(strategy, ContainsCountStrategy) and contains_schema:
            ctx = StrategyContext(
                field_path=path, field_schema=schema,
                root_data=root_data, parent_data=parent_data, index=index
            )
            contains_n = strategy.generate(ctx)
            # minContains / maxContains clamp（仅 schema 显式声明时）
            if "minContains" in schema:
                contains_n = max(contains_n, schema["minContains"])
            if "maxContains" in schema:
                contains_n = min(contains_n, schema["maxContains"])
            min_items = schema.get("minItems", max(1, contains_n))
            max_items = schema.get("maxItems", max(min_items, contains_n + 2))
            total = max(contains_n, random.randint(min_items, max_items))

            # 生成 contains 元素
            contains_elems = []
            for i in range(contains_n):
                item_path = f"{path}[c{i}]"
                val = self.generate_value(
                    schema=contains_schema, path=item_path,
                    root_data=root_data, parent_data=contains_elems, index=index, depth=depth + 1
                )
                contains_elems.append(val)

            # 生成普通元素
            normal_n = total - contains_n
            normal_elems = []
            for i in range(normal_n):
                item_path = f"{path}[n{i}]"
                val = self.generate_value(
                    schema=items_schema, path=item_path,
                    root_data=root_data, parent_data=normal_elems, index=index, depth=depth + 1
                )
                normal_elems.append(val)

            # 随机穿插位置
            result = contains_elems + normal_elems
            random.shuffle(result)
            return result

        # ArrayCountStrategy 或其他 StructureStrategy：控制数组数量
        if isinstance(strategy, StructureStrategy):
            ctx = StrategyContext(
                field_path=path, field_schema=schema,
                root_data=root_data, parent_data=parent_data, index=index
            )
            count = strategy.generate(ctx)
        else:
            # 无策略但有 contains_schema 时，使用 minContains/maxContains 推导
            if contains_schema and not isinstance(strategy, ContainsCountStrategy):
                min_contains = schema.get("minContains", 1)
                max_contains = schema.get("maxContains", min_contains + 1)
                contains_n = random.randint(min_contains, max_contains)
                min_items = schema.get("minItems", max(1, contains_n))
                max_items = schema.get("maxItems", max(min_items, contains_n + 2))
                total = max(contains_n, random.randint(min_items, max_items))

                contains_elems = []
                for i in range(contains_n):
                    item_path = f"{path}[c{i}]"
                    val = self.generate_value(
                        schema=contains_schema, path=item_path,
                        root_data=root_data, parent_data=contains_elems, index=index, depth=depth + 1
                    )
                    contains_elems.append(val)

                normal_n = total - contains_n
                normal_elems = []
                for i in range(normal_n):
                    item_path = f"{path}[n{i}]"
                    val = self.generate_value(
                        schema=items_schema, path=item_path,
                        root_data=root_data, parent_data=normal_elems, index=index, depth=depth + 1
                    )
                    normal_elems.append(val)

                result = contains_elems + normal_elems
                random.shuffle(result)
                return result

            # prefixItems 存在时调整 minItems 默认值
            if prefix_items:
                default_min = max(1, len(prefix_items))
            else:
                default_min = 1
            min_items = schema.get("minItems", default_min)
            max_items = schema.get("maxItems", max(min_items, 3))
            count = random.randint(min_items, max_items)

        # items 为 false 时限制总数不超过 prefixItems 长度
        if prefix_items and items_schema is False:
            count = min(count, len(prefix_items))

        unique = schema.get("uniqueItems", False)
        result = []
        seen = set()
        # 增加重试次数配置：对于复杂结构使用更大的重试次数
        max_retries = max(count * 10, 100) if unique else 0

        for i in range(count):
            item_path = f"{path}[{i}]"
            if i < len(prefix_items):
                # prefixItems 位置用对应 schema
                current_schema = prefix_items[i]
            else:
                current_schema = items_schema if items_schema is not False else {"type": "string"}

            value = self.generate_value(
                schema=current_schema,
                path=item_path,
                root_data=root_data,
                parent_data=result,
                index=index,
                depth=depth + 1
            )
            if unique:
                retries = 0
                hashable_val = self._make_hashable(value)
                while hashable_val in seen and retries < max_retries:
                    value = self.generate_value(
                        schema=current_schema,
                        path=item_path,
                        root_data=root_data,
                        parent_data=result,
                        index=index,
                        depth=depth + 1
                    )
                    hashable_val = self._make_hashable(value)
                    retries += 1
                if hashable_val in seen:
                    break
                seen.add(hashable_val)
            result.append(value)

        return result

    @staticmethod
    def _make_hashable(value: Any) -> Any:
        """将值转为可哈希类型（用于 uniqueItems 去重）"""
        if isinstance(value, dict):
            return tuple(sorted((k, ValueGenerator._make_hashable(v)) for k, v in value.items()))
        if isinstance(value, list):
            return tuple(ValueGenerator._make_hashable(v) for v in value)
        return value

    def _generate_primitive(self, schema: dict, schema_type: str, path: str) -> Any:
        """根据 schema 约束生成基本类型默认值"""
        # 优先使用 enum（排除 _excluded_enum 中的值）
        if "enum" in schema:
            excluded = schema.get("_excluded_enum", [])
            candidates = [v for v in schema["enum"] if v not in excluded]
            if candidates:
                return random.choice(candidates)
            return random.choice(schema["enum"])

        # 优先使用 const
        if "const" in schema:
            return schema["const"]

        # 优先使用 default
        if "default" in schema:
            return schema["default"]

        # 优先使用 examples（数组，随机选一个）
        if "examples" in schema:
            examples = schema["examples"]
            if isinstance(examples, list) and examples:
                return random.choice(examples)

        # 优先使用 example（单值）
        if "example" in schema:
            example = schema["example"]
            # 检查 example 是否符合 schema 约束（基本验证）
            if self._validate_example(schema, example):
                return example
            # 如果不符合约束，记录警告但仍使用（向后兼容）
            warnings.warn(f"example 值可能不符合 schema 约束: {example}")
            return example

        if schema_type == "string":
            return self._generate_default_string(schema)
        elif schema_type == "integer":
            return self._generate_default_integer(schema)
        elif schema_type == "number":
            return self._generate_default_number(schema)
        elif schema_type == "boolean":
            return random.choice([True, False])
        elif schema_type == "null":
            return None

        return None

    def _validate_example(self, schema: dict, example: Any) -> bool:
        """验证 example 是否符合 schema 基本约束（轻量级验证）"""
        schema_type = schema.get("type")

        # 类型验证
        if schema_type:
            if isinstance(schema_type, list):
                # 联合类型：检查是否匹配任意一种类型
                if not any(self._check_type(example, t) for t in schema_type):
                    return False
            elif not self._check_type(example, schema_type):
                return False

        # enum 验证
        if "enum" in schema and example not in schema["enum"]:
            return False

        # const 验证
        if "const" in schema and example != schema["const"]:
            return False

        # 数值范围验证（轻量级）
        if schema_type in ["integer", "number"] and isinstance(example, (int, float)):
            if "minimum" in schema and example < schema["minimum"]:
                return False
            if "maximum" in schema and example > schema["maximum"]:
                return False

        # 字符串长度验证
        if schema_type == "string" and isinstance(example, str):
            if "minLength" in schema and len(example) < schema["minLength"]:
                return False
            if "maxLength" in schema and len(example) > schema["maxLength"]:
                return False

        # 数组长度验证
        if schema_type == "array" and isinstance(example, list):
            if "minItems" in schema and len(example) < schema["minItems"]:
                return False
            if "maxItems" in schema and len(example) > schema["maxItems"]:
                return False

        # 对象必需字段验证
        if schema_type == "object" and isinstance(example, dict):
            required = set(schema.get("required", []))
            if not required.issubset(example.keys()):
                return False

        return True

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值是否符合预期类型"""
        if expected_type == "null":
            return value is None
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return True

    def _generate_default_string(self, schema: dict) -> str:
        """生成默认字符串"""
        # pattern 优先：直接用 exrex 生成
        pattern = schema.get("pattern")
        if pattern:
            import exrex
            return exrex.getone(pattern)

        min_len = schema.get("minLength", 5)
        max_len = schema.get("maxLength", 10)
        max_len = max(min_len, max_len)
        length = random.randint(min_len, max_len)

        # 检查 format
        fmt = schema.get("format")
        if fmt:
            from faker import Faker
            _faker = Faker()
            FORMAT_GENERATORS = {
                "email": lambda: _faker.email(),
                "uri": lambda: _faker.uri(),
                "uuid": lambda: str(__import__('uuid').uuid4()),
                "date": lambda: _faker.date(),
                "date-time": lambda: _faker.iso8601(),
                "time": lambda: _faker.time(),
                "ipv4": lambda: _faker.ipv4(),
                "ipv6": lambda: _faker.ipv6(),
                "hostname": lambda: _faker.hostname(),
                "idn-hostname": lambda: _faker.hostname(),
                "idn-email": lambda: __import__(
                    'data_builder.strategies.value.string.email',
                    fromlist=['_generate_idn_email', 'DOMAINS_IDN', 'OutputFormat']
                )._generate_idn_email(
                    _faker,
                    __import__(
                        'data_builder.strategies.value.string.email',
                        fromlist=['DOMAINS_IDN']
                    ).DOMAINS_IDN,
                    __import__(
                        'data_builder.strategies.value.string.email',
                        fromlist=['OutputFormat']
                    ).OutputFormat.UNICODE,
                    "zh_CN"
                ),
                "duration": lambda: "P%dY%dM%dDT%dH%dM%dS" % (
                    random.randint(0, 5), random.randint(0, 11),
                    random.randint(0, 30), random.randint(0, 23),
                    random.randint(0, 59), random.randint(0, 59)),
                "uri-reference": lambda: "/path/to/" + _faker.word(),
                "json-pointer": lambda: "/" + "/".join(_faker.words(2)),
                "relative-json-pointer": lambda: str(random.randint(0, 5)) + "/" + _faker.word(),
                "regex": lambda: "^[a-z]{%d}$" % random.randint(1, 10),
            }
            generator = FORMAT_GENERATORS.get(fmt)
            if generator:
                return generator()

        return ''.join(random.choices(string.ascii_letters, k=length))

    def _generate_default_integer(self, schema: dict) -> int:
        """生成默认整数"""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 100)

        if "exclusiveMinimum" in schema:
            minimum = schema["exclusiveMinimum"] + 1
        if "exclusiveMaximum" in schema:
            maximum = schema["exclusiveMaximum"] - 1

        minimum, maximum = int(minimum), int(maximum)

        if "multipleOf" in schema:
            step = schema["multipleOf"]
            # 向上取整到最近的倍数
            low = minimum + (-minimum % step) if minimum % step else minimum
            # 向下取整到最近的倍数
            high = maximum - (maximum % step)
            if low > high:
                # 范围内无合法倍数，回退到无 multipleOf 逻辑
                return random.randint(minimum, maximum)
            count = (high - low) // step
            return low + random.randint(0, count) * step

        return random.randint(minimum, maximum)

    def _generate_default_number(self, schema: dict) -> float:
        """生成默认浮点数"""
        minimum = schema.get("minimum", 0.0)
        maximum = schema.get("maximum", 100.0)

        if "exclusiveMinimum" in schema:
            minimum = schema["exclusiveMinimum"] + 1e-9
        if "exclusiveMaximum" in schema:
            maximum = schema["exclusiveMaximum"] - 1e-9

        if "multipleOf" in schema:
            step = schema["multipleOf"]
            import math
            low = math.ceil(minimum / step) * step
            high = math.floor(maximum / step) * step
            if low > high:
                return round(low, 10)
            count = round((high - low) / step)
            return round(low + random.randint(0, count) * step, 10)

        return round(random.uniform(minimum, maximum), 2)
