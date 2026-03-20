"""URL/URI/IRI 生成策略

支持生成符合 RFC 3986 的 URL/URI，以及符合 RFC 3987 的 IRI。
"""

import idna
import random
import urllib.parse
from enum import Enum
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import URL_SCHEMES, WELL_KNOWN_PORTS, URL_PATHS, IDN_DOMAINS


class URLType(Enum):
    """URL 类型"""
    ABSOLUTE = "absolute"     # 绝对 URL（含 scheme）
    RELATIVE = "relative"     # 相对 URL（不含 scheme）
    BOTH = "both"             # 两种都有


class IRIOutputFormat(Enum):
    """IRI 输出格式"""
    UNICODE = "unicode"      # Unicode 原文
    PUNYCODE = "punycode"    # Punycode 编码（仅主机名）
    BOTH = "both"            # 同时输出两种格式


# IRI 路径字符（包含 Unicode 字符）
IRI_UNRESERVED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
IRI_GEN_DELIMS = ":/?#[]@"
IRI_SUB_DELIMS = "!$&'()*+,;="
IRI_PATH_CHARS = IRI_UNRESERVED_CHARS + IRI_SUB_DELIMS


def _encode_hostname_punycode(hostname: str) -> str:
    """将 Unicode 主机名转换为 Punycode 编码"""
    try:
        return idna.encode(hostname).decode()
    except Exception:
        return hostname


def _generate_unicode_path_segment(min_len: int = 1, max_len: int = 20) -> str:
    """生成 Unicode 路径段（用于 IRI）"""
    # Unicode 字符范围
    unicode_ranges = [
        (0x0041, 0x005A),  # A-Z
        (0x0061, 0x007A),  # a-z
        (0x0030, 0x0039),  # 0-9
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0xAC00, 0xD7AF),  # Hangul Syllables
    ]
    
    length = random.randint(min_len, max_len)
    chars = []
    
    for _ in range(length):
        # 70% ASCII，30% Unicode
        if random.random() < 0.7:
            chars.append(random.choice(IRI_PATH_CHARS))
        else:
            # 选择一个 Unicode 范围
            rng = random.choice(unicode_ranges)
            char_code = random.randint(rng[0], rng[1])
            chars.append(chr(char_code))
    
    return "".join(chars)


def _generate_query_param(iri_mode: bool = False) -> str:
    """生成单个查询参数

    参数：
        iri_mode: 是否启用 IRI 模式
    """
    keys = ["id", "name", "page", "limit", "sort", "order", "q", "search", "type", "status"]
    key = random.choice(keys)

    # 生成值
    if key in ["page", "limit"]:
        value = str(random.randint(1, 100))
    elif key in ["sort", "order"]:
        value = random.choice(["asc", "desc", "name", "date", "price"])
    elif key == "id":
        value = str(random.randint(1, 10000))
    elif iri_mode:
        # IRI 模式：使用 Unicode 字符
        value = _generate_unicode_path_segment(3, 8)
    else:
        value = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(3, 8)))

    return f"{key}={value}"


def _generate_fragment() -> str:
    """生成片段标识符"""
    fragments = [
        "top", "bottom", "content", "main", "header", "footer",
        "section1", "section2", "overview", "details", "comments",
    ]
    return random.choice(fragments)


class URLStrategy(Strategy):
    """URL/URI/IRI 生成策略

    生成符合 RFC 3986 的 URL/URI，或符合 RFC 3987 的 IRI。

    参数：
    - scheme: URL scheme（如 "https"，可选，默认随机选择）
    - scheme_list: 自定义 scheme 列表（可选）
    - url_type: URL 类型（absolute/relative/both，默认 "absolute"）
    - host: 指定主机名（可选）
    - port: 指定端口号（可选）
    - path: 指定路径（可选）
    - path_list: 自定义路径列表（可选）
    - include_userinfo: 是否包含用户信息（默认 False）
    - include_query: 是否包含查询参数（默认 False）
    - include_fragment: 是否包含片段（默认 False）
    - max_query_params: 最大查询参数数量（默认 3）
    - use_ip_host: 使用 IP 地址作为主机（默认 False）
    - locale: Faker 区域设置（默认 "zh_CN"）
    - iri_mode: 是否启用 IRI 模式（默认 False）
    - output_format: IRI 输出格式（unicode/punycode/both，默认 unicode）
    - idn_domains: IDN 域名后缀列表（可选）
    """

    def __init__(
        self,
        scheme: Optional[str] = None,
        scheme_list: Optional[List[str]] = None,
        url_type: str = "absolute",
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[str] = None,
        path_list: Optional[List[str]] = None,
        include_userinfo: bool = False,
        include_query: bool = False,
        include_fragment: bool = False,
        max_query_params: int = 3,
        use_ip_host: bool = False,
        locale: str = "zh_CN",
        iri_mode: bool = False,
        output_format: str = "unicode",
        idn_domains: Optional[List[str]] = None,
    ):
        self.scheme = scheme
        self.scheme_list = scheme_list if scheme_list else URL_SCHEMES
        self.host = host
        self.port = port
        self.path = path
        self.path_list = path_list if path_list else URL_PATHS
        self.include_userinfo = include_userinfo
        self.include_query = include_query
        self.include_fragment = include_fragment
        self.max_query_params = max_query_params
        self.use_ip_host = use_ip_host
        self.locale = locale
        self.iri_mode = iri_mode
        self.idn_domains = idn_domains if idn_domains else IDN_DOMAINS.copy()

        # 解析 url_type
        try:
            self.url_type = URLType(url_type.lower())
        except ValueError:
            raise StrategyError(
                f"URLStrategy: 不支持的 URL 类型 {url_type!r}，"
                f"可选值: {[t.value for t in URLType]}"
            )

        # 解析 output_format
        try:
            self.output_format = IRIOutputFormat(output_format.lower())
        except ValueError:
            self.output_format = IRIOutputFormat.UNICODE

        # 验证端口
        if self.port is not None and not (0 <= self.port <= 65535):
            raise StrategyError(f"URLStrategy: 端口号必须在 0-65535 范围内")

        # 延迟加载 Faker
        self._faker = None

    @property
    def faker(self):
        if self._faker is None:
            from faker import Faker
            self._faker = Faker(self.locale)
        return self._faker

    def generate(self, ctx: StrategyContext) -> str:
        """生成 URL"""
        # 决定是绝对还是相对 URL
        if self.url_type == URLType.RELATIVE:
            return self._generate_relative_url()
        elif self.url_type == URLType.ABSOLUTE:
            return self._generate_absolute_url()
        else:
            # 随机选择
            if random.random() < 0.5:
                return self._generate_relative_url()
            return self._generate_absolute_url()

    def _generate_absolute_url(self) -> str:
        """生成绝对 URL"""
        parts = []

        # Scheme
        scheme = self.scheme if self.scheme else random.choice(self.scheme_list)
        parts.append(f"{scheme}://")

        # 用户信息
        if self.include_userinfo:
            username = self.faker.user_name()
            password = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
            parts.append(f"{username}:{password}@")

        # 主机
        host = self._generate_host()
        parts.append(host)

        # 端口
        if self.port:
            parts.append(f":{self.port}")
        elif random.random() < 0.2:  # 20% 概率添加端口
            port = random.choice(list(WELL_KNOWN_PORTS.keys()) + [8080, 8443, 3000, 5000])
            # 避免默认端口
            if not (scheme == "http" and port == 80) and \
               not (scheme == "https" and port == 443):
                parts.append(f":{port}")

        # 路径
        path = self._generate_path()
        parts.append(path)

        # 查询参数
        if self.include_query:
            query = self._generate_query()
            parts.append(f"?{query}")

        # 片段
        if self.include_fragment:
            fragment = _generate_fragment()
            parts.append(f"#{fragment}")

        return "".join(parts)

    def _generate_relative_url(self) -> str:
        """生成相对 URL"""
        parts = []

        # 路径
        path = self._generate_path()
        parts.append(path)

        # 查询参数
        if self.include_query:
            query = self._generate_query()
            parts.append(f"?{query}")

        # 片段
        if self.include_fragment:
            fragment = _generate_fragment()
            parts.append(f"#{fragment}")

        return "".join(parts)

    def _generate_host(self) -> str:
        """生成主机名"""
        if self.host:
            return self.host

        if self.use_ip_host:
            # 使用 IP 地址作为主机
            if random.random() < 0.2:  # 20% IPv6
                return f"[2001:db8::{random.randint(1, 255)}]"
            else:
                return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        elif self.iri_mode:
            # 使用 IDN 域名
            return self._generate_idn_host()
        else:
            # 使用普通域名
            return self.faker.domain_name()

    def _generate_idn_host(self) -> str:
        """生成国际化域名（IDN 主机名）"""
        # 选择 IDN 后缀
        idn_suffix = random.choice(self.idn_domains)

        # 生成主机名标签
        if random.random() < 0.5:
            # 使用 Faker 生成的名字
            label = self.faker.first_name().lower()
        else:
            # 使用随机标签
            label = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(3, 10)))

        # 组合主机名
        hostname = f"{label}.{idn_suffix}"

        # 根据输出格式返回
        if self.output_format == IRIOutputFormat.UNICODE:
            return hostname
        elif self.output_format == IRIOutputFormat.PUNYCODE:
            return _encode_hostname_punycode(hostname)
        else:  # BOTH - 返回第一个格式作为字符串
            return hostname

    def _generate_path(self) -> str:
        """生成路径"""
        if self.path:
            return self.path

        if self.iri_mode:
            path = _generate_unicode_path_segment()
        else:
            path = random.choice(self.path_list)

        # 有时添加更多路径段
        if random.random() < 0.3:
            segments = random.randint(1, 3)
            for _ in range(segments):
                if self.iri_mode:
                    segment = _generate_unicode_path_segment(3, 10)
                else:
                    segment = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789-", k=random.randint(3, 10)))
                path += f"/{segment}"

        return path

    def _generate_query(self) -> str:
        """生成查询字符串"""
        num_params = random.randint(1, self.max_query_params)
        params = [_generate_query_param(iri_mode=self.iri_mode) for _ in range(num_params)]
        return "&".join(params)

    def values(self) -> Optional[List[str]]:
        """完整值域（URL 空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "http://a.com",                      # 最短 URL
            "https://example.com",               # 基本 HTTPS
            "ftp://ftp.example.com:21/",         # FTP
            "http://user:pass@example.com",      # 含用户信息
            "http://example.com:8080/path",      # 含端口和路径
            "http://example.com?a=1&b=2",        # 含查询参数
            "http://example.com#section",        # 含片段
            "http://192.168.1.1",                # IP 主机
            "http://[::1]",                      # IPv6 主机
            "/relative/path",                    # 相对 URL
            "/path?query=value#fragment",        # 完整相对 URL
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["http://example.com"],              # HTTP
            ["https://example.com"],             # HTTPS
            ["ftp://ftp.example.com"],           # FTP
            ["/relative/path"],                  # 相对 URL
            ["http://example.com?q=test"],       # 含查询参数
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "://example.com",                    # 缺少 scheme
            "http://",                           # 缺少主机
            "http://example.com:99999",          # 端口超出范围
            "http://example.com:abc",            # 非法端口
            "http://user@@example.com",          # 非法用户信息
            "http://example.com/path with space",  # 路径含空格（未编码）
            "",                                  # 空字符串
            None,                                # None
            "http://example.com?q=hello world",  # 查询含空格（未编码）
            "http://example.com#frag#ment",      # 多个片段标识符
        ]
