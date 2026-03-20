"""主机名生成策略

支持生成符合 RFC 1123 的 ASCII 主机名和符合 RFC 5890 的国际化主机名（IDN）。
"""

import idna
import random
import re
from enum import Enum
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import COMMON_TLDS, RESERVED_TLDS, IDN_DOMAINS


class HostnameOutputFormat(Enum):
    """IDN 主机名输出格式"""
    UNICODE = "unicode"      # Unicode 原文
    PUNYCODE = "punycode"    # Punycode 编码
    BOTH = "both"            # 同时输出两种格式


def _encode_hostname_punycode(hostname: str) -> str:
    """将 Unicode 主机名转换为 Punycode 编码"""
    try:
        return idna.encode(hostname).decode()
    except Exception:
        return hostname


def _generate_ascii_label(min_len: int = 1, max_len: int = 63) -> str:
    """生成单个 ASCII 主机名标签

    标签规则（RFC 1123）：
    - 只包含字母、数字、连字符
    - 不能以连字符开头或结尾
    - 长度 1-63 字符
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    length = random.randint(min_len, min(max_len, 20))
    
    label = []
    for i in range(length):
        if i == 0 or i == length - 1:
            label.append(random.choice("abcdefghijklmnopqrstuvwxyz0123456789"))
        else:
            if random.random() < 0.1:
                label.append("-")
            else:
                label.append(random.choice(chars))
    
    return "".join(label)


def _generate_word_label() -> str:
    """生成基于单词的标签（更真实）"""
    prefixes = ["web", "app", "api", "db", "mail", "ftp", "cdn", "proxy",
                "server", "node", "master", "slave", "primary", "secondary",
                "dev", "test", "prod", "staging", "demo", "beta"]
    suffixes = ["01", "02", "1", "2", "-main", "-backup", "-standby"]
    
    if random.random() < 0.5:
        return random.choice(prefixes)
    else:
        return random.choice(prefixes) + random.choice(suffixes)


# IDN 主机名后缀（用于国际化主机名）
IDN_HOSTNAME_SUFFIXES = [
    "中国", "公司", "网络",  # 中文
    "日本",                  # 日文
    "한국",                  # 韩文
]


class HostnameStrategy(Strategy):
    """主机名生成策略

    生成符合 RFC 1123 的 ASCII 主机名或符合 RFC 5890 的国际化主机名。

    参数：
    - include_tld: 是否包含 TLD（默认 False）
    - tld: 指定 TLD（如 "com"，可选）
    - labels: 标签数量，不含 TLD（默认 1，范围 1-5）
    - idn: 是否生成国际化主机名（默认 False）
    - idn_suffixes: IDN 后缀列表（默认 IDN_HOSTNAME_SUFFIXES）
    - output_format: IDN 输出格式（unicode/punycode/both，默认 unicode）
    - use_words: 是否使用常见单词生成标签（默认 True）
    - locale: Faker 区域设置（默认 zh_CN）

    hostname vs domain 区别：
    - hostname 可以没有 TLD（如 localhost、web-server）
    - domain 必须有 TLD（如 example.com）
    """

    def __init__(
        self,
        include_tld: bool = False,
        tld: Optional[str] = None,
        labels: int = 1,
        idn: bool = False,
        idn_suffixes: Optional[List[str]] = None,
        output_format: str = "unicode",
        use_words: bool = True,
        locale: str = "zh_CN",
    ):
        self.include_tld = include_tld
        self.tld = tld.lstrip(".") if tld else None
        self.labels = max(1, min(labels, 5))  # 限制 1-5 个标签
        self.idn = idn
        self.idn_suffixes = idn_suffixes if idn_suffixes is not None else IDN_HOSTNAME_SUFFIXES.copy()
        self.use_words = use_words
        self.locale = locale

        # 解析输出格式
        try:
            self.output_format = HostnameOutputFormat(output_format)
        except ValueError:
            self.output_format = HostnameOutputFormat.UNICODE

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
        """生成主机名"""
        if self.idn:
            return self._generate_idn_hostname()
        return self._generate_ascii_hostname()

    def _generate_ascii_hostname(self) -> str:
        """生成 ASCII 主机名"""
        hostname_labels = []

        # 生成各级标签
        for _ in range(self.labels):
            if self.use_words:
                hostname_labels.append(_generate_word_label())
            else:
                hostname_labels.append(_generate_ascii_label())

        # 是否包含 TLD
        if self.include_tld:
            if self.tld:
                tld = self.tld
            else:
                tld = random.choice(COMMON_TLDS)
            hostname_labels.append(tld)

        # 组合主机名
        hostname = ".".join(hostname_labels)

        # 确保总长度不超过 253 字符
        while len(hostname) > 253 and len(hostname_labels) > 1:
            shortest_idx = min(range(len(hostname_labels)), key=lambda i: len(hostname_labels[i]))
            hostname_labels.pop(shortest_idx)
            hostname = ".".join(hostname_labels)

        return hostname.lower()

    def _generate_idn_hostname(self) -> Union[str, dict]:
        """生成国际化主机名（IDN）"""
        # 选择 IDN 后缀
        idn_suffix = random.choice(self.idn_suffixes)

        # 生成主机名标签
        if self.use_words:
            style = random.choice(["name", "word", "random"])
            if style == "name":
                label = self.faker.first_name()
            elif style == "word":
                label = self.faker.word()
            else:
                label = _generate_ascii_label(2, 8)
        else:
            label = _generate_ascii_label(2, 8)

        # 组合主机名
        hostname = f"{label}.{idn_suffix}"

        # 根据输出格式返回
        if self.output_format == HostnameOutputFormat.UNICODE:
            return hostname
        elif self.output_format == HostnameOutputFormat.PUNYCODE:
            return _encode_hostname_punycode(hostname)
        else:  # BOTH
            return {
                "unicode": hostname,
                "punycode": _encode_hostname_punycode(hostname),
            }

    def values(self) -> Optional[List[str]]:
        """完整值域（主机名空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "a",                                    # 最短主机名
            "a" * 63,                               # 最长标签
            ".".join(["a"] * 127),                  # 最深层级（127 个标签）
            "localhost",                            # 保留主机名
            "中国.中国",                            # IDN 主机名
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["web-server"],                         # 普通主机名
            ["localhost"],                          # 保留主机名
            ["中国.中国"],                          # IDN 主机名
            ["db-master-01"],                       # 多标签主机名
            ["xn--fiqs8s.xn--fiqs8s"],              # Punycode 主机名
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "-hostname",                            # 以连字符开头
            "hostname-",                            # 以连字符结尾
            "host--name",                           # 连续连字符（某些情况下非法）
            ".hostname",                            # 以点号开头
            "hostname.",                            # 以点号结尾（技术上合法，但通常不推荐）
            "",                                     # 空字符串
            None,                                   # None
            "a" * 64,                               # 标签超长
            "host..name",                           # 连续点号
            "host name",                            # 包含空格
            "host#name",                            # 包含非法字符
        ]
