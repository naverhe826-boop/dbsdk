"""IPv6 地址生成策略"""

import ipaddress
import random
from enum import Enum
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import (
    IPV6_UNSPECIFIED,
    IPV6_LOOPBACK,
    IPV6_IPV4_MAPPED_PREFIX,
    IPV6_LINK_LOCAL_PREFIX,
    IPV6_UNIQUE_LOCAL_PREFIX,
    IPV6_MULTICAST_PREFIX,
    IPV6_GLOBAL_UNICAST_PREFIX,
)


class IPv6AddressType(Enum):
    """IPv6 地址类型"""
    ANY = "any"                    # 任意合法地址
    GLOBAL = "global"              # 全局单播
    LINK_LOCAL = "link_local"      # 链路本地
    UNIQUE_LOCAL = "unique_local"  # 唯一本地
    MULTICAST = "multicast"        # 组播地址
    LOOPBACK = "loopback"          # 回环地址
    UNSPECIFIED = "unspecified"    # 未指定地址
    IPV4_MAPPED = "ipv4_mapped"    # IPv4映射地址


class IPv6Format(Enum):
    """IPv6 输出格式"""
    FULL = "full"                  # 完整格式（8组）
    COMPRESSED = "compressed"      # 压缩格式（:: 省略零）
    IPV4_COMPAT = "ipv4_compat"    # IPv4兼容格式（::ffff:x.x.x.x）


def _random_hex_group(length: int = 4) -> str:
    """生成随机十六进制组"""
    return format(random.randint(0, 0xFFFF), f"0{length}x")


def _generate_random_ipv6_in_prefix(prefix: str) -> str:
    """在指定前缀内生成随机 IPv6 地址"""
    network = ipaddress.IPv6Network(prefix, strict=False)
    # 获取网络地址的整数表示
    network_int = int(network.network_address)
    # 计算主机部分的最大值
    host_bits = network.max_prefixlen - network.prefixlen
    # 生成随机主机部分
    random_host = random.randint(1, (1 << host_bits) - 2)  # 排除全0和全1
    # 组合成完整地址
    address_int = network_int | random_host
    return str(ipaddress.IPv6Address(address_int))


def _generate_global_unicast() -> str:
    """生成全局单播地址（2000::/3）"""
    # 2000::/3 范围：2000::-3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff
    return _generate_random_ipv6_in_prefix(IPV6_GLOBAL_UNICAST_PREFIX)


def _generate_link_local() -> str:
    """生成链路本地地址（fe80::/10）"""
    # fe80::/10: 前10位固定为 1111111010，后118位随机
    # 即 0xFE80 到 0xFEBF 范围
    # 使用 ipaddress 模块确保正确性
    base_int = 0xFE80 << 112  # fe80:0000:0000:0000
    # 后 54 位随机（接口标识符部分）
    random_suffix = random.randint(0, (1 << 54) - 1)
    address_int = base_int | random_suffix
    return str(ipaddress.IPv6Address(address_int))


def _generate_unique_local() -> str:
    """生成唯一本地地址（fc00::/7）"""
    # fc00::/7 或 fd00::/8
    # 使用 fd00::/8（L位=1，本地分配）
    prefix = random.choice(["fc00::/8", "fd00::/8"])
    return _generate_random_ipv6_in_prefix(prefix)


def _generate_multicast() -> str:
    """生成组播地址（ff00::/8）"""
    # ff00::/8，标志和范围字段
    # ff0s:gggg:gggg:gggg，s=范围，g=组ID
    scope = random.choice([1, 2, 5, 14])  # 接口本地、链路本地、站点本地、全球
    # 生成组ID（112位）
    group_id = random.randint(1, (1 << 112) - 1)
    # 组合地址
    address_int = (0xFF << 120) | (scope << 112) | group_id
    return str(ipaddress.IPv6Address(address_int))


def _generate_ipv4_mapped() -> str:
    """生成 IPv4 映射地址（::ffff:x.x.x.x）"""
    # 生成随机 IPv4 地址
    ipv4_int = random.randint(1, 0xFFFFFFFE)
    ipv4_parts = [
        (ipv4_int >> 24) & 0xFF,
        (ipv4_int >> 16) & 0xFF,
        (ipv4_int >> 8) & 0xFF,
        ipv4_int & 0xFF,
    ]
    # 组合成 IPv4 映射地址
    return f"::ffff:{ipv4_parts[0]}.{ipv4_parts[1]}.{ipv4_parts[2]}.{ipv4_parts[3]}"


class IPv6Strategy(Strategy):
    """IPv6 地址生成策略

    支持的地址类型（address_type）：
    - any: 任意合法地址
    - global: 全局单播地址（2000::/3）
    - link_local: 链路本地地址（fe80::/10）
    - unique_local: 唯一本地地址（fc00::/7）
    - multicast: 组播地址（ff00::/8）
    - loopback: 回环地址（::1）
    - unspecified: 未指定地址（::）
    - ipv4_mapped: IPv4映射地址（::ffff:x.x.x.x）

    参数：
    - address_type: 地址类型（默认 "any"）
    - format: 输出格式（full/compressed/ipv4_compat，默认 "compressed"）
    - prefix_length: 子网前缀长度（默认 64）
    """

    def __init__(
        self,
        address_type: str = "any",
        format: str = "compressed",
        prefix_length: int = 64,
    ):
        # 解析 address_type
        try:
            self.address_type = IPv6AddressType(address_type.lower())
        except ValueError:
            raise StrategyError(
                f"IPv6Strategy: 不支持的地址类型 {address_type!r}，"
                f"可选值: {[t.value for t in IPv6AddressType]}"
            )

        # 解析 format
        try:
            self.output_format = IPv6Format(format.lower())
        except ValueError:
            raise StrategyError(
                f"IPv6Strategy: 不支持的输出格式 {format!r}，"
                f"可选值: {[f.value for f in IPv6Format]}"
            )

        self.prefix_length = prefix_length

        # 验证前缀长度
        if not 0 <= self.prefix_length <= 128:
            raise StrategyError(
                f"IPv6Strategy: 前缀长度必须在 0-128 范围内，当前为 {self.prefix_length}"
            )

    def generate(self, ctx: StrategyContext) -> str:
        """生成 IPv6 地址"""
        ip = self._generate_by_type()
        return self._format_output(ip)

    def _generate_by_type(self) -> str:
        """根据地址类型生成"""
        if self.address_type == IPv6AddressType.ANY:
            return self._generate_any()
        elif self.address_type == IPv6AddressType.GLOBAL:
            return _generate_global_unicast()
        elif self.address_type == IPv6AddressType.LINK_LOCAL:
            return _generate_link_local()
        elif self.address_type == IPv6AddressType.UNIQUE_LOCAL:
            return _generate_unique_local()
        elif self.address_type == IPv6AddressType.MULTICAST:
            return _generate_multicast()
        elif self.address_type == IPv6AddressType.LOOPBACK:
            return IPV6_LOOPBACK
        elif self.address_type == IPv6AddressType.UNSPECIFIED:
            return IPV6_UNSPECIFIED
        elif self.address_type == IPv6AddressType.IPV4_MAPPED:
            return _generate_ipv4_mapped()
        else:
            raise StrategyError(f"IPv6Strategy: 未处理的地址类型 {self.address_type}")

    def _generate_any(self) -> str:
        """生成任意合法地址"""
        # 随机选择一种地址类型（排除特殊类型）
        types = [
            IPv6AddressType.GLOBAL,
            IPv6AddressType.UNIQUE_LOCAL,
            IPv6AddressType.LINK_LOCAL,
        ]
        chosen_type = random.choice(types)
        # 临时修改类型并生成
        original_type = self.address_type
        self.address_type = chosen_type
        try:
            return self._generate_by_type()
        finally:
            self.address_type = original_type

    def _format_output(self, ip: str) -> str:
        """格式化输出"""
        if self.output_format == IPv6Format.COMPRESSED:
            # 使用 Python 内置的压缩格式
            return str(ipaddress.IPv6Address(ip))
        elif self.output_format == IPv6Format.FULL:
            # 完整格式（展开所有零）
            addr = ipaddress.IPv6Address(ip)
            return addr.exploded
        elif self.output_format == IPv6Format.IPV4_COMPAT:
            # 如果是 IPv4 映射地址，保持原格式
            if ip.startswith("::ffff:"):
                return ip
            # 否则转换为压缩格式
            return str(ipaddress.IPv6Address(ip))
        return ip

    def values(self) -> Optional[List[str]]:
        """完整值域（IPv6 地址空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            IPV6_UNSPECIFIED,                     # ::（未指定）
            IPV6_LOOPBACK,                        # ::1（回环）
            "2000::",                             # 全局单播最小
            "2000::1",                            # 全局单播最小主机
            "3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # 全局单播最大
            "fe80::",                             # 链路本地最小
            "febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # 链路本地最大
            "fc00::",                             # 唯一本地最小
            "fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # 唯一本地最大
            "ff00::",                             # 组播最小
            "ff0f:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # 组播最大
            "::ffff:0.0.0.0",                     # IPv4映射最小
            "::ffff:255.255.255.255",             # IPv4映射最大
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            [IPV6_UNSPECIFIED],                   # 未指定
            [IPV6_LOOPBACK],                      # 回环
            ["2000::1"],                          # 全局单播
            ["fe80::1"],                          # 链路本地
            ["fd00::1"],                          # 唯一本地
            ["ff02::1"],                          # 组播
            ["::ffff:192.168.1.1"],               # IPv4映射
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "gggg::",                             # 非法字符
            "1:2:3:4:5:6:7:8:9",                  # 超过8组
            "1:2:3:4:5:6:7",                      # 少于8组（无压缩）
            "::1::2",                             # 多个 ::
            "1:2:3:4:5:6:7:8:9:10",               # 过长
            "",                                   # 空字符串
            None,                                 # None
            "1:2:3:4:5:6:7:8:",                   # 尾随冒号
            ":1:2:3:4:5:6:7:8",                   # 前导冒号（非压缩）
            "1::2::3",                            # 多个压缩
        ]
