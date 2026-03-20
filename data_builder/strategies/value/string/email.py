import idna
import re
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 域名池常量
DOMAINS_CN = [
    "qq.com",
    "163.com",
    "126.com",
    "sina.com",
    "sohu.com",
    "139.com",
]

DOMAINS_INTL = [
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "icloud.com",
    "protonmail.com",
    "mail.com",
]

DEFAULT_DOMAINS = DOMAINS_CN + DOMAINS_INTL

# IDN 国际化域名池
DOMAINS_IDN = [
    "中国.cn",
    "公司.cn",
    "网络.cn",
    "中国.com",
    "中国.net",
    "世界.org",
    "日本.jp",
    "한국.kr",
    "德国.de",
    "法国.fr",
    "俄国.ru",
    "西班牙.es",
    "意大利.it",
    "巴西.br",
    "印度.in",
]

DEFAULT_IDN_DOMAINS = DOMAINS_IDN.copy()


class OutputFormat(Enum):
    """IDN 邮箱输出格式枚举"""
    UNICODE = "unicode"  # Unicode 原文，如 user@中国.cn
    PUNYCODE = "punycode"  # Punycode 编码，如 user@xn--fiqs8s.cn
    BOTH = "both"  # 同时输出两种格式


def _encode_domain_punycode(domain: str) -> str:
    """将 Unicode 域名转换为 Punycode 编码"""
    try:
        return idna.encode(domain).decode()
    except Exception:
        # 如果转换失败，返回原域名
        return domain


def _generate_qq_username() -> str:
    """生成5-11位纯数字QQ用户名"""
    length = random.randint(5, 11)
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def _generate_gmail_username(faker) -> str:
    """生成 first.last 格式的Gmail用户名（小写，中间点号）"""
    first = faker.first_name().lower()
    last = faker.last_name().lower()
    return f"{first}.{last}"


def _generate_163_username(faker) -> str:
    """生成163邮箱用户名（使用Faker user_name）"""
    return faker.user_name()


def _generate_outlook_username(faker) -> str:
    """生成Outlook邮箱用户名（前8位+2位随机数字）"""
    base = faker.user_name()[:8]
    suffix = "".join([str(random.randint(0, 9)) for _ in range(2)])
    return f"{base}{suffix}"


def _generate_custom_username(faker) -> str:
    """生成安全用户名（字母数字点号下划线，避免首尾点和连续点）"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._"
    length = random.randint(6, 16)
    username = "".join(random.choice(chars) for _ in range(length))
    # 避免首尾点号
    username = username.strip(".")
    # 避免连续点号
    while ".." in username:
        username = username.replace("..", ".")
    # 确保不为空
    if not username:
        username = faker.user_name()
    return username


def _generate_safe_email(faker, domains: List[str]) -> str:
    """生成Faker内置email，支持指定域名"""
    email = faker.email()
    if domains:
        domain = random.choice(domains)
        local = email.split("@")[0]
        return f"{local}@{domain}"
    return email


def _generate_idn_username(faker, locale: str = "zh_CN") -> str:
    """生成支持 Unicode 的用户名"""
    # 随机选择用户名风格
    style = random.choice(["name", "word", "random"])

    if style == "name":
        # 使用姓名作为用户名
        first = faker.first_name()
        last = faker.last_name()
        # 随机选择全名、姓名首字母等形式
        choice = random.randint(0, 2)
        if choice == 0:
            return f"{first}{last}"
        elif choice == 1:
            return f"{first}_{last}"
        else:
            return f"{first}{random.randint(100, 999)}"
    elif style == "word":
        # 使用单词+数字
        word = faker.word()
        suffix = random.randint(1, 999)
        return f"{word}{suffix}"
    else:
        # 纯随机用户名
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        length = random.randint(6, 12)
        return "".join(random.choice(chars) for _ in range(length))


def _generate_idn_email(
    faker,
    idn_domains: List[str],
    output_format: OutputFormat,
    locale: str = "zh_CN",
) -> Union[str, Dict[str, str]]:
    """生成 IDN 邮箱

    Args:
        faker: Faker 实例
        idn_domains: IDN 域名列表
        output_format: 输出格式
        locale: 区域语言

    Returns:
        根据 output_format 返回字符串或字典
    """
    # 随机选择一个 IDN 域名
    idn_domain = random.choice(idn_domains)

    # 生成用户名
    username = _generate_idn_username(faker, locale)

    # 根据输出格式生成结果
    if output_format == OutputFormat.UNICODE:
        return f"{username}@{idn_domain}"
    elif output_format == OutputFormat.PUNYCODE:
        punycode_domain = _encode_domain_punycode(idn_domain)
        return f"{username}@{punycode_domain}"
    else:  # OutputFormat.BOTH
        punycode_domain = _encode_domain_punycode(idn_domain)
        return {
            "unicode": f"{username}@{idn_domain}",
            "punycode": f"{username}@{punycode_domain}",
        }


class EmailFakerStrategy(Strategy):
    """邮箱地址生成策略

    支持的邮箱类型：
    - qq: 5-11位纯数字用户名
    - gmail: first.last 格式（小写，中间点号）
    - 163: 使用 Faker user_name()
    - outlook: 前8位 + 2位随机数字
    - custom: 随机域名 + 安全用户名
    - safe: Faker 内置 email()，支持指定域名
    - idn: 国际化域名邮箱（支持 Unicode 域名）
    - random: 随机取其它类型的邮箱

    参数：
    - email_type: 邮箱类型（默认 "random"）
    - locale: 区域语言（默认 "zh_CN"）
    - domains: 普通邮箱域名列表（默认使用 DEFAULT_DOMAINS）
    - idn_domains: IDN 域名列表（默认使用 DOMAINS_IDN）
    - output_format: IDN 邮箱输出格式（unicode/punycode/both，默认 "unicode"）
    - include_idn: 当 email_type=random 时是否包含 IDN 邮箱（默认 False）
    """

    SUPPORTED_TYPES = {"qq", "gmail", "163", "outlook", "custom", "safe", "idn", "random"}
    # 基本类型列表（不包含 random 和 idn）
    _BASE_TYPES = ["qq", "gmail", "163", "outlook", "custom", "safe"]

    def __init__(
        self,
        email_type: str = "random",
        locale: str = "zh_CN",
        domains: Optional[List[str]] = None,
        idn_domains: Optional[List[str]] = None,
        output_format: str = "unicode",
        include_idn: bool = False,
    ):
        self.email_type = email_type
        self.locale = locale
        self.domains = domains if domains is not None else DEFAULT_DOMAINS.copy()
        self.idn_domains = idn_domains if idn_domains is not None else DEFAULT_IDN_DOMAINS.copy()
        self.include_idn = include_idn

        # 处理 output_format 参数
        if isinstance(output_format, str):
            try:
                self.output_format = OutputFormat(output_format)
            except ValueError:
                self.output_format = OutputFormat.UNICODE
        else:
            self.output_format = output_format

        if email_type not in self.SUPPORTED_TYPES:
            raise StrategyError(f"EmailFakerStrategy: 不支持的邮箱类型 {email_type!r}")

        from faker import Faker
        self._faker = Faker(self.locale)

    def generate(self, ctx: StrategyContext) -> Any:
        email_type = self.email_type

        if email_type == "qq":
            username = _generate_qq_username()
            domain = "qq.com"  # 固定使用 qq.com 域名
            return f"{username}@{domain}"

        elif email_type == "gmail":
            username = _generate_gmail_username(self._faker)
            domain = "gmail.com"
            return f"{username}@{domain}"

        elif email_type == "163":
            username = _generate_163_username(self._faker)
            domain = random.choice([d for d in self.domains if d in DOMAINS_CN]) or "163.com"
            return f"{username}@{domain}"

        elif email_type == "outlook":
            username = _generate_outlook_username(self._faker)
            domain = random.choice([d for d in self.domains if d in ["outlook.com", "hotmail.com"]]) or "outlook.com"
            return f"{username}@{domain}"

        elif email_type == "custom":
            username = _generate_custom_username(self._faker)
            domain = random.choice(self.domains)
            return f"{username}@{domain}"

        elif email_type == "safe":
            return _generate_safe_email(self._faker, self.domains)

        elif email_type == "idn":
            return _generate_idn_email(
                self._faker,
                self.idn_domains,
                self.output_format,
                self.locale,
            )

        elif email_type == "random":
            # 动态构建可选的随机类型列表
            random_types = self._BASE_TYPES.copy()
            if self.include_idn:
                random_types.append("idn")
            
            # 随机选择一个其它类型生成邮箱
            chosen_type = random.choice(random_types)
            # 递归调用 generate 方法处理选中的类型（通过临时修改 email_type）
            original_type = self.email_type
            self.email_type = chosen_type
            try:
                result = self.generate(ctx)
            finally:
                self.email_type = original_type
            return result

        raise StrategyError(f"EmailFakerStrategy: 未处理的邮箱类型 {email_type!r}")

    def values(self) -> Optional[List[Any]]:
        return None

    def boundary_values(self) -> Optional[List[Any]]:
        return None

    def equivalence_classes(self) -> Optional[List[List[Any]]]:
        return None

    def invalid_values(self) -> Optional[List[Any]]:
        return [
            "not-an-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user name@domain.com",
            "user@domain@extra.com",
            "",
            "user@ domain.com",
            "user@.com",
            "user@com.",
        ]
