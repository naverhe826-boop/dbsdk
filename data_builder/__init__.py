__version__ = "0.3.0"

from typing import List, Optional

from .builder import DataBuilder
from .config import BuilderConfig, FieldPolicy
from .combinations import CombinationMode, CombinationSpec, Constraint
from .filters import deduplicate, constraint_filter, limit, tag_rows
from .utils import InvalidDataGenerator
from .strategies import (
    Strategy,
    StrategyContext,
    StructureStrategy,
    FixedStrategy,
    RandomStringStrategy,
    RangeStrategy,
    EnumStrategy,
    RegexStrategy,
    SequenceStrategy,
    FakerStrategy,
    EmailFakerStrategy,
    CallableStrategy,
    RefStrategy,
    DateTimeStrategy,
    StrategyRegistry,
    LLMStrategy,
    LLMConfig,
    ConcatStrategy,
    ArrayCountStrategy,
    SchemaAwareStrategy,
    PropertyCountStrategy,
    PropertySelectionStrategy,
    ContainsCountStrategy,
    SchemaSelectionStrategy,
    PasswordStrategy,
    IdCardStrategy,
    BankCardStrategy,
    PhoneStrategy,
    UsernameStrategy,
)
from .exceptions import (
    DataBuilderError,
    SchemaError,
    StrategyError,
    StrategyNotFoundError,
    FieldPathError,
)


# 便捷工厂函数
def fixed(value):
    """固定值"""
    return FixedStrategy(value)


def random_string(length=10, charset=None):
    """随机字符串"""
    if charset:
        return RandomStringStrategy(length=length, charset=charset)
    return RandomStringStrategy(length=length)


def range_int(min_val=0, max_val=100):
    """整数范围"""
    return RangeStrategy(min_val=min_val, max_val=max_val, is_float=False)


def range_float(min_val=0.0, max_val=100.0, precision=2):
    """浮点数范围"""
    return RangeStrategy(min_val=min_val, max_val=max_val, is_float=True, precision=precision)


def enum(choices, weights=None):
    """枚举选择"""
    return EnumStrategy(choices=choices, weights=weights)


def regex(pattern):
    """正则生成"""
    return RegexStrategy(pattern=pattern)


def seq(start=1, step=1, prefix="", suffix="", padding=0):
    """自增序列"""
    return SequenceStrategy(start=start, step=step, prefix=prefix, suffix=suffix, padding=padding)


def faker(method, locale="zh_CN", **kwargs):
    """Faker 集成"""
    return FakerStrategy(method=method, locale=locale, **kwargs)


def callable_strategy(func):
    """自定义函数"""
    return CallableStrategy(func=func)


def ref(path, transform=None):
    """引用其他字段"""
    return RefStrategy(ref_path=path, transform=transform)


def llm(config, prompt, system_prompt=None, json_output=False):
    """LLM 生成策略，config 为 LLMConfig 实例"""
    kwargs = {"config": config, "prompt": prompt, "json_output": json_output}
    if system_prompt is not None:
        kwargs["system_prompt"] = system_prompt
    return LLMStrategy(**kwargs)


def password(
    length=12,
    use_digits=True,
    use_uppercase=True,
    use_lowercase=True,
    use_special=True,
    special_chars=None,
):
    """密码生成策略，符合 Linux/Windows 密码策略要求

    参数：
        length: 密码长度，8-32 之间，默认 12
        use_digits: 是否包含数字，默认 True
        use_uppercase: 是否包含大写字母，默认 True
        use_lowercase: 是否包含小写字母，默认 True
        use_special: 是否包含特殊字符，默认 True
        special_chars: 自定义特殊字符集，默认 "!@#$%^&*()_+-=[]{}|;:,.<>?"
    """
    return PasswordStrategy(
        length=length,
        use_digits=use_digits,
        use_uppercase=use_uppercase,
        use_lowercase=use_lowercase,
        use_special=use_special,
        special_chars=special_chars,
    )


def array_count(source):
    """控制数组字段元素数量"""
    return ArrayCountStrategy(source)


def property_count(source):
    """控制对象属性数量"""
    return PropertyCountStrategy(source)


def property_selection(properties):
    """控制对象生成哪些属性"""
    return PropertySelectionStrategy(properties)


def contains_count(source):
    """控制数组中 contains 元素数量"""
    return ContainsCountStrategy(source)


def schema_selection(source):
    """控制 oneOf/anyOf 分支选择"""
    return SchemaSelectionStrategy(source)


def datetime(
    start=None,
    end=None,
    format="%Y-%m-%d %H:%M:%S",
    timezone=None,
    anchor=None,
    offset=None,
    date_range=None,
    time_range=None,
    specific_date=None,
    specific_time=None,
):
    """日期时间策略"""
    return DateTimeStrategy(
        start=start,
        end=end,
        format=format,
        timezone=timezone,
        anchor=anchor,
        offset=offset,
        date_range=date_range,
        time_range=time_range,
        specific_date=specific_date,
        specific_time=specific_time,
    )


def concat(strategies, separators=None):
    """级联合并多个策略的值"""
    return ConcatStrategy(strategies=strategies, separators=separators)


def email(email_type="random", locale="zh_CN", domains=None):
    """邮箱生成策略"""
    return EmailFakerStrategy(email_type=email_type, locale=locale, domains=domains)


def ipv4(ip_class="any", ip_address_type="unicast", ip_subnet_mask=None, ip_multicast_groups=None):
    """IPv4 地址生成策略"""
    from .strategies.value.network import IPv4Strategy
    return IPv4Strategy(ip_class=ip_class, ip_address_type=ip_address_type, 
                       subnet_mask=ip_subnet_mask, multicast_groups=ip_multicast_groups)


def ipv6(ip_class="global_unicast", ip_address_type="unicast", ip_scope="global"):
    """IPv6 地址生成策略"""
    from .strategies.value.network import IPv6Strategy
    return IPv6Strategy(address_type=ip_address_type, scope=ip_scope)


def domain(domain_type="ascii", tld_list=None, max_level=3):
    """域名生成策略"""
    from .strategies.value.network import DomainStrategy
    return DomainStrategy(domain_type=domain_type, tld_list=tld_list, max_level=max_level)


def url(
    scheme: str = "https",
    url_type: str = "absolute",
    host: str = None,
    port: int = None,
    path: str = None,
    include_query: bool = False,
    include_fragment: bool = False,
    use_ip_host: bool = False,
    iri_mode: bool = False,
    output_format: str = "unicode",
):
    """URL/URI/IRI 生成策略"""
    from .strategies.value.network import URLStrategy
    return URLStrategy(
        scheme=scheme,
        url_type=url_type,
        host=host,
        port=port,
        path=path,
        include_query=include_query,
        include_fragment=include_fragment,
        use_ip_host=use_ip_host,
        iri_mode=iri_mode,
        output_format=output_format,
    )


def mac(oui=None, address_type="unicast", administration_type="global", broadcast_address=False):
    """MAC 地址生成策略"""
    from .strategies.value.network import MACStrategy
    return MACStrategy(oui=oui, address_type=address_type, 
                      administration_type=administration_type, broadcast_address=broadcast_address)


def cidr(ip_version=4, prefix_length=None, network_class=None):
    """CIDR 表示法生成策略"""
    from .strategies.value.network import CIDRStrategy
    return CIDRStrategy(version=ip_version, prefix_length=prefix_length, network_class=network_class)


def ip_range(ip_version=4, ip_class="any"):
    """IP 范围生成策略"""
    from .strategies.value.network import IPRangeStrategy
    return IPRangeStrategy(version=ip_version, ip_class=ip_class)


def hostname(
    include_tld: bool = False,
    tld: Optional[str] = None,
    labels: int = 1,
    idn: bool = False,
    idn_suffixes: Optional[List[str]] = None,
    output_format: str = "unicode",
):
    """主机名生成策略"""
    from .strategies.value.network import HostnameStrategy
    return HostnameStrategy(
        include_tld=include_tld,
        tld=tld,
        labels=labels,
        idn=idn,
        idn_suffixes=idn_suffixes,
        output_format=output_format,
    )


def id_card(min_age: int = 18, max_age: int = 65, gender: str = "random", region: Optional[str] = None):
    """身份证号生成策略"""
    from .strategies.value.string import IdCardStrategy
    return IdCardStrategy(min_age=min_age, max_age=max_age, gender=gender, region=region)


def bank_card(bank: str = "random", card_type: str = "debit"):
    """银行卡号生成策略"""
    from .strategies.value.string import BankCardStrategy
    return BankCardStrategy(bank=bank, card_type=card_type)


def phone(carrier: str = "random", number_type: str = "normal"):
    """手机号生成策略"""
    from .strategies.value.string import PhoneStrategy
    return PhoneStrategy(carrier=carrier, number_type=number_type)


def username(
    min_length: int = 6,
    max_length: int = 20,
    charset: str = "alphanumeric_underscore",
    reserved_words: Optional[List[str]] = None,
    allow_uppercase: bool = True,
):
    """用户名生成策略"""
    from .strategies.value.string import UsernameStrategy
    return UsernameStrategy(
        min_length=min_length,
        max_length=max_length,
        charset=charset,
        reserved_words=reserved_words,
        allow_uppercase=allow_uppercase,
    )


__all__ = [
    # 核心类
    "DataBuilder",
    "BuilderConfig",
    "FieldPolicy",
    # 策略类
    "Strategy",
    "StrategyContext",
    "StructureStrategy",
    "FixedStrategy",
    "RandomStringStrategy",
    "RangeStrategy",
    "EnumStrategy",
    "RegexStrategy",
    "SequenceStrategy",
    "FakerStrategy",
    "EmailFakerStrategy",
    "CallableStrategy",
    "RefStrategy",
    "DateTimeStrategy",
    "LLMStrategy",
    "LLMConfig",
    "ConcatStrategy",
    "PasswordStrategy",
    "IdCardStrategy",
    "BankCardStrategy",
    "PhoneStrategy",
    "UsernameStrategy",
    "ArrayCountStrategy",
    "SchemaAwareStrategy",
    "PropertyCountStrategy",
    "PropertySelectionStrategy",
    "ContainsCountStrategy",
    "SchemaSelectionStrategy",
    "StrategyRegistry",
    # 异常
    "DataBuilderError",
    "SchemaError",
    "StrategyError",
    "StrategyNotFoundError",
    "FieldPathError",
    # 工具类
    "InvalidDataGenerator",
    # 便捷函数
    "fixed",
    "random_string",
    "range_int",
    "range_float",
    "enum",
    "regex",
    "seq",
    "faker",
    "callable_strategy",
    "ref",
    "array_count",
    "property_count",
    "property_selection",
    "contains_count",
    "schema_selection",
    "llm",
    "datetime",
    # 网络策略
    "concat",
    "email",
    "ipv4",
    "ipv6",
    "domain",
    "url",
    "mac",
    "cidr",
    "ip_range",
    "hostname",
    # 账户类策略
    "id_card",
    "bank_card",
    "phone",
    "username",
    # 组合生成
    "CombinationMode",
    "CombinationSpec",
    "Constraint",
    # 过滤器
    "deduplicate",
    "constraint_filter",
    "limit",
    "tag_rows",
    "__version__",
]
