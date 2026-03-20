"""配置管理模块

提供字段策略配置和构建器配置类。
"""

import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


def _safe_eval(expression: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """
    安全地评估字符串表达式（仅用于从本地文件加载的配置）。

    ⚠️ 安全警告：此函数仅用于从本地文件加载的可信配置。
    - 不建议在配置文件中使用字符串形式的 predicate
    - 建议在代码中直接定义 predicate 函数
    - 如果必须在配置文件中使用，请确保配置文件来源可信

    :param expression: 要评估的表达式字符串
    :param context: 评估时使用的上下文变量
    :return: 评估结果
    :raises: SyntaxError, ValueError, TypeError 等
    """
    if context is None:
        context = {}

    warnings.warn(
        "使用字符串形式的 predicate 存在安全风险，建议在代码中直接定义函数。"
        "此功能仅适用于从本地文件加载的可信配置。",
        stacklevel=3
    )

    try:
        # 使用受限的全局变量和提供的上下文
        result = eval(expression, {"__builtins__": {}}, context)
        if not callable(result):
            raise ValueError(f"表达式必须返回可调用对象，得到: {type(result)}")
        return result
    except Exception as e:
        raise ValueError(f"表达式评估失败: {e}") from e


@dataclass
class FieldPolicy:
    """字段策略配置"""
    path: str  # 支持通配符：user.*, orders[*].id
    strategy: Any  # Strategy 类型，避免循环导入使用 Any


@dataclass
class BuilderConfig:
    """构建器配置"""
    policies: List[FieldPolicy] = field(default_factory=list)
    strict_mode: bool = False  # 严格模式：无策略时抛异常
    null_probability: float = 0.0  # null值概率（0-1）
    count: Optional[int] = None  # 默认生成数量
    combinations: List[Any] = field(default_factory=list)  # CombinationSpec 类型
    post_filters: List[Callable] = field(default_factory=list)
    max_depth: Optional[int] = None  # 递归结构最大深度（None 时检测到循环引用会抛异常）
    union_type_priority: Optional[List[str]] = None  # 联合类型优先级（如 ["string", "integer"]）

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BuilderConfig":
        """
        从配置字典创建 BuilderConfig。

        配置格式：
          {
            "policies": [
              {"path": "id", "strategy": {"type": "sequence", "params": {"start": 1001}}},
              {"path": "name", "strategy": {"type": "faker", "method": "name"}}
            ],
            "combinations": [
              {"mode": "cartesian", "fields": ["status", "type"]}
            ],
            "post_filters": [
              {"type": "limit", "max_count": 10},
              {"type": "deduplicate", "key_fields": ["id"]}
            ],
            "count": 10,
            "strict_mode": false
          }

        :param config_dict: 配置字典
        :return: BuilderConfig 实例
        """
        from .strategies.value.registry import StrategyRegistry, _resolve_env_vars_recursive
        from .combinations import CombinationSpec, Constraint, CombinationMode

        # 解析环境变量
        config_dict = _resolve_env_vars_recursive(config_dict)

        # 处理 policies
        policies = []
        for policy_config in config_dict.get("policies", []):
            policy = StrategyRegistry.create_from_policy_config(policy_config)
            policies.append(policy)

        # 处理 combinations 配置
        combinations = []
        for combo_config in config_dict.get("combinations", []):
            combo = cls._parse_combination_spec(combo_config)
            if combo:
                combinations.append(combo)

        # 处理 post_filters
        post_filters = cls._parse_post_filters(config_dict.get("post_filters", []))

        return cls(
            policies=policies,
            strict_mode=config_dict.get("strict_mode", False),
            null_probability=config_dict.get("null_probability", 0.0),
            count=config_dict.get("count"),
            combinations=combinations,
            post_filters=post_filters,
            max_depth=config_dict.get("max_depth"),
            union_type_priority=config_dict.get("union_type_priority"),
        )

    @classmethod
    def _parse_combination_spec(cls, config: Dict[str, Any]) -> Optional[Any]:
        """从字典解析 CombinationSpec"""
        from .combinations import CombinationMode, CombinationSpec, Constraint

        mode_str = config.get("mode", "random").upper()
        try:
            mode = CombinationMode[mode_str]
        except KeyError:
            mode = CombinationMode.RANDOM

        # 解析 constraints
        constraints = []
        for constraint_config in config.get("constraints", []):
            # constraints 支持两种格式：
            # 1. {"description": "xxx"} - 只有描述，需要在运行时提供 predicate
            # 2. {"predicate": "lambda row: row['status'] == 'active'"} - 字符串形式的 predicate
            #    ⚠️ 安全警告：字符串形式的 predicate 仅适用于本地可信配置
            desc = constraint_config.get("description", "")
            predicate_str = constraint_config.get("predicate")
            predicate = None
            if predicate_str and isinstance(predicate_str, str):
                try:
                    # 为 predicate 提供 row 变量作为上下文
                    predicate = _safe_eval(predicate_str)
                except ValueError as e:
                    warnings.warn(f"无法解析 constraint predicate: {e}")
                    continue
            if predicate:
                constraints.append(Constraint(predicate=predicate, description=desc))

        return CombinationSpec(
            mode=mode,
            fields=config.get("fields"),
            scope=config.get("scope"),
            constraints=constraints,
            strength=config.get("strength", 2),
            normal_values=config.get("normal_values"),
        )

    @classmethod
    def _parse_post_filters(cls, filters_config: List[Any]) -> List[Callable]:
        """从字典解析 post_filters"""
        from .filters import deduplicate, constraint_filter, limit, tag_rows

        filters = []
        for filter_config in filters_config:
            if isinstance(filter_config, str):
                # 简单字符串形式：只支持预定义的简单过滤器
                if filter_config == "deduplicate":
                    # 需要指定 key_fields，否则无法工作
                    continue
                elif filter_config == "limit":
                    filters.append(limit(100))  # 默认值
                continue

            if not isinstance(filter_config, dict):
                continue

            filter_type = filter_config.get("type", "").lower()

            if filter_type == "limit":
                max_count = filter_config.get("max_count", 100)
                filters.append(limit(max_count))

            elif filter_type == "deduplicate":
                key_fields = filter_config.get("key_fields", [])
                if key_fields:
                    filters.append(deduplicate(key_fields))

            elif filter_type == "constraint_filter":
                predicate_str = filter_config.get("predicate")
                predicate = None
                if predicate_str and isinstance(predicate_str, str):
                    try:
                        # ⚠️ 安全警告：字符串形式的 predicate 仅适用于本地可信配置
                        predicate = _safe_eval(predicate_str)
                    except ValueError as e:
                        warnings.warn(f"无法解析 filter predicate: {e}")
                        continue
                if predicate:
                    filters.append(constraint_filter(predicate))

            elif filter_type == "tag_rows":
                tag_field = filter_config.get("tag_field", "_tag")
                tag_value = filter_config.get("tag_value", "")
                filters.append(tag_rows(tag_field, tag_value))

        return filters

    @classmethod
    def from_file(cls, file_path: str) -> "BuilderConfig":
        """
        从文件加载配置（支持 JSON 和 YAML 格式）。

        :param file_path: 配置文件路径
        :return: BuilderConfig 实例
        """
        import json

        # 根据文件扩展名判断格式
        ext = file_path.lower().split(".")[-1]

        with open(file_path, "r", encoding="utf-8") as f:
            if ext in ("yaml", "yml"):
                # 尝试导入 yaml
                try:
                    import yaml
                    config_dict = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("YAML 支持需要安装 pyyaml: pip install pyyaml")
            else:
                # 默认为 JSON
                config_dict = json.load(f)

        return cls.from_dict(config_dict)
