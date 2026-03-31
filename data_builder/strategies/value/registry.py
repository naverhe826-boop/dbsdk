import os
import re
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

from ..basic import Strategy
from ..basic import FixedStrategy

# Forward reference for type hints
if TYPE_CHECKING:
    from data_builder.builder import FieldPolicy
from .string import RandomStringStrategy
from .numeric import RangeStrategy
from .enum import EnumStrategy  # noqa: F401
from .string import RegexStrategy
from .numeric import SequenceStrategy
from .external import FakerStrategy
from .string import EmailFakerStrategy
from .advanced import CallableStrategy
from .advanced import RefStrategy
from .datetime import DateTimeStrategy
from .advanced import ConcatStrategy
from .string import PasswordStrategy
from .string import TokenStrategy
from .system import MetricStrategy
from ...exceptions import StrategyNotFoundError


def _resolve_env_vars(value: Any) -> Any:
    """
    解析环境变量插值。
    支持格式：
      - ${VAR_NAME}           # 从环境变量读取
      - ${VAR_NAME:-default}  # 带默认值
      - ${VAR_NAME:-}         # 默认值为空字符串
    """
    if not isinstance(value, str):
        return value

    # 匹配 ${VAR_NAME} 或 ${VAR_NAME:-default}
    pattern = r'\$\{([^}:]+)(?::-(.*?))?\}'

    def replace(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default_value)

    return re.sub(pattern, replace, value)


def _resolve_env_vars_recursive(value: Any) -> Any:
    """
    递归解析环境变量插值。
    支持嵌套的 dict 和 list。
    """
    if isinstance(value, dict):
        return {k: _resolve_env_vars_recursive(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars_recursive(item) for item in value]
    elif isinstance(value, str):
        return _resolve_env_vars(value)
    return value


# 参数别名映射：配置中的参数名 -> 策略类的实际参数名
PARAM_ALIASES = {
    # 值策略
    "enum": {
        "values": "choices",  # enum 策略的 values 参数映射到 choices
    },
    "range": {
        "min": "min_val",
        "max": "max_val",
    },
    "random_string": {
        "len": "length",  # 显式声明
    },
    "regex": {
        "pattern": "pattern",
    },
    "ref": {
        "ref_path": "ref_path",
    },
    "datetime": {
        "start": "start",
        "end": "end",
        "format": "format",
        "timezone": "timezone",
        "anchor": "anchor",
        "offset": "offset",
        "date_r": "date_range",
        "time_r": "time_range",
        "spec_date": "specific_date",
        "spec_time": "specific_time",
    },
    "email": {
        "type": "email_type",
        "domain": "domains",
    },
    "username": {
        "style": "style",
        "gender": "gender",
        "suffix_type": "suffix_type",
        "min_len": "min_length",
        "max_len": "max_length",
    },
    "token": {
        "type": "token_type",  # token 策略的 type 参数映射到 token_type
        "len": "length",
    },
    "metric": {
        "type": "metric_type",    # metric 策略的 type 参数映射到 metric_type
        "mode": "data_mode",      # mode 参数映射到 data_mode
        "interval": "time_interval",  # interval 参数映射到 time_interval
    },
    # 结构策略
    "property_count": {
        "count": "source",  # count 映射到 source
    },
    "array_count": {
        "count": "source",  # count 映射到 source
    },
    "contains_count": {
        "count": "source",  # 常用别名映射到 source
    },
    "schema_selection": {
        "index": "source",  # 分支索引映射到 source
    },
}


def _coerce_type(value: Any, target_type: Optional[str] = None) -> Any:
    """
    自动类型转换。
    如果指定了 target_type，则尝试转换。
    """
    # 空字符串在目标类型为数值类型时返回 None，避免转换错误
    if target_type in ("int", "float") and value == "":
        return None
    
    if target_type == "int":
        return int(value)
    elif target_type == "float":
        return float(value)
    elif target_type == "bool":
        if isinstance(value, bool):
            return value
        return value.lower() in ("true", "1", "yes")
    elif target_type == "list":
        if isinstance(value, list):
            return value
        # 逗号分隔的字符串转列表
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return [value]
    elif target_type == "dict":
        if isinstance(value, dict):
            return value
        return {"value": value}
    elif target_type == "tuple":
        # 支持将列表转换为元组
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return (value,)
    return value


def _apply_param_aliases(strategy_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用参数别名映射。
    """
    aliases = PARAM_ALIASES.get(strategy_type, {})
    result = {}
    for key, value in params.items():
        # 使用别名或原始参数名
        new_key = aliases.get(key, key)
        result[new_key] = value
    return result


class StrategyRegistry:
    """策略注册表"""

    _strategies: Dict[str, Type[Strategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[Strategy]):
        """注册策略"""
        cls._strategies[name] = strategy_class

    @classmethod
    def get(cls, name: str) -> Type[Strategy]:
        """获取策略类"""
        if name not in cls._strategies:
            raise StrategyNotFoundError(f"策略 '{name}' 未注册")
        return cls._strategies[name]

    @classmethod
    def has(cls, name: str) -> bool:
        """检查策略是否存在"""
        return name in cls._strategies

    @classmethod
    def reset(cls):
        """恢复为内置策略（测试清理用）"""
        cls._strategies = dict(cls._builtin_strategies)

    @classmethod
    def create(cls, config: Dict[str, Any]) -> Strategy:
        """
        从配置字典创建策略实例。

        配置格式：
          {"type": "sequence", "params": {"start": 1001, "prefix": "ORD-"}}

        或更简化的格式：
          {"type": "sequence", "start": 1001, "prefix": "ORD-"}

        :param config: 策略配置字典
        :return: 策略实例
        """
        # 递归解析环境变量（包括嵌套的 dict 和 list）
        config = _resolve_env_vars_recursive(config)

        strategy_type = config.get("type")
        if not strategy_type:
            raise ValueError("配置中缺少 'type' 字段")

        strategy_class = cls.get(strategy_type)

        # 获取策略类的构造函数参数
        import inspect
        sig = inspect.signature(strategy_class.__init__)
        param_names = set(sig.parameters.keys()) - {"self"}

        # 优先使用 params 字段，否则将顶层字段作为 params
        params = config.get("params", {})
        if not params:
            # 提取非 type 的字段作为参数
            params = {k: v for k, v in config.items() if k != "type"}

        # 应用参数别名映射
        params = _apply_param_aliases(strategy_type, params)

        # 类型推断和转换
        resolved_params = {}
        for key, value in params.items():
            if key in param_names:
                # 尝试自动类型推断
                param_info = sig.parameters[key]
                anno = param_info.annotation
                target_type = None
                if anno != inspect.Parameter.empty:
                    anno_str = str(anno).lower()  # 转换为小写以便统一匹配
                    # 检查顺序：优先检查最外层容器类型
                    # Optional[Dict[...]] -> dict
                    # Optional[List[...]] -> list
                    # Optional[Tuple[...]] -> tuple
                    # 使用索引位置判断最外层容器类型
                    dict_pos = anno_str.find('dict')
                    list_pos = anno_str.find('list')
                    tuple_pos = anno_str.find('tuple')
                    
                    # 找到第一个出现的容器类型
                    container_types = []
                    if dict_pos >= 0:
                        container_types.append(('dict', dict_pos))
                    if list_pos >= 0:
                        container_types.append(('list', list_pos))
                    if tuple_pos >= 0:
                        container_types.append(('tuple', tuple_pos))
                    
                    # 按位置排序，选择第一个（最外层的）
                    if container_types:
                        container_types.sort(key=lambda x: x[1])
                        target_type = container_types[0][0]
                    # 如果没有容器类型，检查基本类型
                    elif "bool" in anno_str:
                        target_type = "bool"
                    elif "float" in anno_str:
                        target_type = "float"
                    elif "int" in anno_str:
                        target_type = "int"
                resolved_params[key] = _coerce_type(value, target_type)

        return strategy_class(**resolved_params)

    @classmethod
    def create_from_policy_config(cls, policy_config: Dict[str, Any]) -> "FieldPolicy":
        """
        从策略配置字典创建 FieldPolicy。

        配置格式：
          {"path": "id", "strategy": {"type": "sequence", "params": {"start": 1001}}}

        或简化格式：
          {"path": "id", "strategy": "sequence", "start": 1001}

        :param policy_config: 策略配置字典
        :return: FieldPolicy 实例
        """
        from data_builder.builder import FieldPolicy

        path = policy_config.get("path")
        if not path:
            raise ValueError("配置中缺少 'path' 字段")

        strategy_config = policy_config.get("strategy")
        if not strategy_config:
            raise ValueError(f"path '{path}' 缺少 'strategy' 配置")

        # 如果 strategy 是字符串，直接作为 type
        if isinstance(strategy_config, str):
            strategy_config = {"type": strategy_config}
            # 将其他字段合并为 params
            for k, v in policy_config.items():
                if k not in ("path", "strategy"):
                    strategy_config[k] = v

        strategy = cls.create(strategy_config)
        return FieldPolicy(path=path, strategy=strategy)


# 注册内置策略
StrategyRegistry.register("fixed", FixedStrategy)
StrategyRegistry.register("random_string", RandomStringStrategy)
StrategyRegistry.register("range", RangeStrategy)
StrategyRegistry.register("enum", EnumStrategy)
StrategyRegistry.register("regex", RegexStrategy)
StrategyRegistry.register("sequence", SequenceStrategy)
StrategyRegistry.register("faker", FakerStrategy)
StrategyRegistry.register("callable", CallableStrategy)
StrategyRegistry.register("ref", RefStrategy)
StrategyRegistry.register("datetime", DateTimeStrategy)
StrategyRegistry.register("concat", ConcatStrategy)
StrategyRegistry.register("password", PasswordStrategy)
StrategyRegistry.register("email", EmailFakerStrategy)
StrategyRegistry.register("token", TokenStrategy)

# 结构策略
from ..structure import (
    ArrayCountStrategy, PropertyCountStrategy, PropertySelectionStrategy,
    ContainsCountStrategy, SchemaSelectionStrategy, SchemaAwareStrategy,
)

StrategyRegistry.register("array_count", ArrayCountStrategy)
StrategyRegistry.register("property_count", PropertyCountStrategy)
StrategyRegistry.register("property_selection", PropertySelectionStrategy)
StrategyRegistry.register("contains_count", ContainsCountStrategy)
StrategyRegistry.register("schema_selection", SchemaSelectionStrategy)
StrategyRegistry.register("schema_aware", SchemaAwareStrategy)

# LLM 策略（openai 为可选依赖）
try:
    from .external import LLMStrategy
    StrategyRegistry.register("llm", LLMStrategy)
except ImportError:
    pass

# 网络策略
from .network import (
    IPv4Strategy, IPv6Strategy, DomainStrategy, HostnameStrategy,
    URLStrategy, MACStrategy, CIDRStrategy, IPRangeStrategy
)

StrategyRegistry.register("ipv4", IPv4Strategy)
StrategyRegistry.register("ipv6", IPv6Strategy)
StrategyRegistry.register("domain", DomainStrategy)
StrategyRegistry.register("hostname", HostnameStrategy)
StrategyRegistry.register("url", URLStrategy)
StrategyRegistry.register("mac", MACStrategy)
StrategyRegistry.register("cidr", CIDRStrategy)
StrategyRegistry.register("ip_range", IPRangeStrategy)

# 账户类策略
from .string import IdCardStrategy, BankCardStrategy, PhoneStrategy, UsernameStrategy

StrategyRegistry.register("id_card", IdCardStrategy)
StrategyRegistry.register("bank_card", BankCardStrategy)
StrategyRegistry.register("phone", PhoneStrategy)
StrategyRegistry.register("username", UsernameStrategy)

# 系统监控指标策略
StrategyRegistry.register("metric", MetricStrategy)

# 保存内置策略快照（用于测试隔离）
StrategyRegistry._builtin_strategies = dict(StrategyRegistry._strategies)
