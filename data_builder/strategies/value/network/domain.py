"""域名生成策略"""

import idna
import random
import re
from enum import Enum
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import COMMON_TLDS, RESERVED_TLDS, COMMON_SUBDOMAINS, IDN_DOMAINS


class DomainOutputFormat(Enum):
    """域名输出格式"""
    UNICODE = "unicode"      # Unicode 原文
    PUNYCODE = "punycode"    # Punycode 编码
    BOTH = "both"            # 同时输出两种格式


def _encode_domain_punycode(domain: str) -> str:
    """将 Unicode 域名转换为 Punycode 编码

    只对包含非 ASCII 字符的标签进行编码，ASCII 标签保持不变。
    """
    try:
        labels = domain.split(".")
        encoded_labels = []
        for label in labels:
            try:
                # 尝试编码标签，如果标签已经是纯 ASCII，则原样返回
                # idna.encode() 会检查标签是否包含非 ASCII 字符
                encoded_label = idna.encode(label).decode("ascii")
                encoded_labels.append(encoded_label)
            except (idna.IDNAError, UnicodeError):
                # 编码失败（通常是因为标签已经是纯 ASCII），保持原样
                encoded_labels.append(label)
        return ".".join(encoded_labels)
    except Exception:
        return domain


def _generate_label(min_len: int = 1, max_len: int = 63) -> str:
    """生成单个域名标签

    标签规则：
    - 只包含字母、数字、连字符
    - 不能以连字符开头或结尾
    - 长度 1-63 字符
    """
    # 域名标签字符集（字母、数字、连字符）
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    
    # 随机长度（倾向于较短的标签）
    length = random.randint(min_len, min(max_len, 20))
    
    # 生成标签
    label = []
    for i in range(length):
        if i == 0 or i == length - 1:
            # 首尾只能是字母或数字
            label.append(random.choice("abcdefghijklmnopqrstuvwxyz0123456789"))
        else:
            # 中间可以包含连字符（概率 10%）
            if random.random() < 0.1:
                label.append("-")
            else:
                label.append(random.choice(chars))
    
    return "".join(label)


def _generate_word_label() -> str:
    """生成基于单词的标签（更真实）"""
    # 常见单词前缀和后缀
    prefixes = ["my", "the", "web", "app", "api", "dev", "test", "demo", "blog", "shop"]
    suffixes = ["app", "web", "site", "hub", "lab", "io", "box", "now", "one", "pro"]
    
    # 随机选择组合方式
    if random.random() < 0.3:
        # 单个单词
        return random.choice(prefixes + suffixes)
    elif random.random() < 0.5:
        # 前缀 + 数字
        return f"{random.choice(prefixes)}{random.randint(1, 999)}"
    else:
        # 前缀 + 后缀
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"


class DomainStrategy(Strategy):
    """域名生成策略

    生成符合 RFC 1034/1035 的合法域名。

    参数：
    - tld: 指定顶级域名（如 ".com" 或 "com"，可选）
    - tld_list: 自定义 TLD 列表（可选）
    - prefix: 域名前缀（如 "test-"，可选）
    - suffix: 域名后缀（如 ".local"，可选）
    - levels: 域名层级（默认 2，即 example.com）
    - use_reserved_tld: 是否使用保留 TLD（如 .test, .example）
    - idn: 是否生成国际化域名（IDN）
    - idn_domains: IDN 域名后缀列表（可选）
    - output_format: IDN 输出格式（unicode/punycode/both）
    - use_words: 是否使用常见单词生成标签（默认 True）
    - locale: Faker 区域设置（默认 "zh_CN"）
    """

    def __init__(
        self,
        tld: Optional[str] = None,
        tld_list: Optional[List[str]] = None,
        prefix: str = "",
        suffix: str = "",
        levels: int = 2,
        use_reserved_tld: bool = False,
        idn: bool = False,
        idn_domains: Optional[List[str]] = None,
        output_format: str = "unicode",
        use_words: bool = True,
        locale: str = "zh_CN",
    ):
        self.prefix = prefix
        self.suffix = suffix
        self.levels = max(1, min(levels, 5))  # 限制 1-5 级
        self.use_reserved_tld = use_reserved_tld
        self.idn = idn
        self.idn_domains = idn_domains if idn_domains is not None else IDN_DOMAINS.copy()
        self.use_words = use_words
        self.locale = locale

        # 处理 TLD
        if tld:
            # 统一格式（去除前导点）
            self.tld = tld.lstrip(".")
        else:
            self.tld = None

        # 设置 TLD 列表
        if tld_list:
            self.tld_list = [t.lstrip(".") for t in tld_list]
        elif use_reserved_tld:
            self.tld_list = RESERVED_TLDS
        else:
            self.tld_list = COMMON_TLDS

        # 解析输出格式
        try:
            self.output_format = DomainOutputFormat(output_format)
        except ValueError:
            self.output_format = DomainOutputFormat.UNICODE

        # 初始化 Faker（延迟加载）
        self._faker = None

    @property
    def faker(self):
        """延迟加载 Faker"""
        if self._faker is None:
            from faker import Faker
            self._faker = Faker(self.locale)
        return self._faker

    def generate(self, ctx: StrategyContext) -> Union[str, dict]:
        """生成域名"""
        if self.idn:
            return self._generate_idn_domain()
        return self._generate_ascii_domain()

    def _generate_ascii_domain(self) -> str:
        """生成 ASCII 域名"""
        labels = []

        # 生成各级子域名
        for i in range(self.levels - 1):
            if self.use_words:
                labels.append(_generate_word_label())
            else:
                labels.append(_generate_label())

        # 添加前缀到第一个标签
        if self.prefix and labels:
            labels[0] = self.prefix + labels[0]

        # 选择 TLD
        if self.tld:
            tld = self.tld
        else:
            tld = random.choice(self.tld_list)

        # 添加后缀
        if self.suffix:
            tld = self.suffix.lstrip(".") + "." + tld

        # 组合域名
        domain = ".".join(labels + [tld])

        # 确保总长度不超过 253 字符
        while len(domain) > 253 and len(labels) > 1:
            # 删除最短的标签
            shortest_idx = min(range(len(labels)), key=lambda i: len(labels[i]))
            labels.pop(shortest_idx)
            domain = ".".join(labels + [tld])

        return domain.lower()

    def _generate_idn_domain(self) -> Union[str, dict]:
        """生成国际化域名（IDN）"""
        # 选择 IDN 后缀
        idn_suffix = random.choice(self.idn_domains)

        # 生成主域名标签
        if self.use_words:
            # 使用 Faker 生成多语言标签
            style = random.choice(["name", "word", "random"])
            if style == "name":
                label = self.faker.first_name() + self.faker.last_name()
            elif style == "word":
                label = self.faker.word() + str(random.randint(1, 999))
            else:
                label = _generate_label(3, 10)
        else:
            label = _generate_label(3, 10)

        # 添加前缀
        if self.prefix:
            label = self.prefix + label

        # 组合域名
        domain = f"{label}.{idn_suffix}"

        # 根据输出格式返回
        if self.output_format == DomainOutputFormat.UNICODE:
            return domain
        elif self.output_format == DomainOutputFormat.PUNYCODE:
            return _encode_domain_punycode(domain)
        else:  # BOTH
            return {
                "unicode": domain,
                "punycode": _encode_domain_punycode(domain),
            }

    def values(self) -> Optional[List[str]]:
        """完整值域（域名空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "a.com",                              # 最短域名
            "a" * 63 + ".com",                    # 最长标签
            ".".join(["a"] * 127) + ".com",       # 最深层级（127个标签 + TLD）
            "test.test",                          # 保留 TLD
            "example.example",                    # 保留 TLD
            "中国.cn",                            # IDN 域名
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["example.com"],                      # 普通域名
            ["test.test"],                        # 保留 TLD
            ["中国.cn"],                          # IDN 域名
            ["sub.domain.example.com"],           # 多级域名
            ["xn--fiqs8s.cn"],                    # Punycode 域名
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "-example.com",                       # 以连字符开头
            "example-.com",                       # 以连字符结尾
            "ex--ample.com",                      # 连续连字符（某些情况下非法）
            ".example.com",                       # 以点号开头
            "example.com.",                       # 以点号结尾（技术上合法，但通常不推荐）
            "",                                   # 空字符串
            None,                                 # None
            "a" * 64 + ".com",                    # 标签超长
            "example..com",                       # 连续点号
            "example.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com.com",  # 总长度超长
            "例子.测试",                           # 非法 TLD（如果不在 IDN 列表中）
        ]
