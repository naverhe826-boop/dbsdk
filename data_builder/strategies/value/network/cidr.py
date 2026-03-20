"""CIDR 表示法生成策略"""

import ipaddress
import random
from enum import Enum
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class CIDRVersion(Enum):
    """IP 版本"""
    IPV4 = 4
    IPV6 = 6
    BOTH = 0  # 两者随机


class CIDRStrategy(Strategy):
    """CIDR 表示法生成策略

    生成如 192.168.1.0/24 或 2001:db8::/32 的 CIDR 字符串。

    参数：
    - version: IP 版本（4/6/0，0 表示随机，默认 4）
    - network: 指定网络地址（如 "192.168.1.0"，可选）
    - prefix_length: 指定前缀长度（可选）
    - min_prefix: 最小前缀长度（IPv4 默认 8，IPv6 默认 32）
    - max_prefix: 最大前缀长度（IPv4 默认 30，IPv6 默认 128）
    - include_private: 是否包含私有地址网段（默认 True）
    - include_loopback: 是否包含回环网段（默认 False）
    - include_multicast: 是否包含组播网段（默认 False）
    """

    # 默认前缀范围
    DEFAULT_IPV4_MIN_PREFIX = 8
    DEFAULT_IPV4_MAX_PREFIX = 30
    DEFAULT_IPV6_MIN_PREFIX = 32
    DEFAULT_IPV6_MAX_PREFIX = 128

    def __init__(
        self,
        version: int = 4,
        network: Optional[str] = None,
        prefix_length: Optional[int] = None,
        min_prefix: Optional[int] = None,
        max_prefix: Optional[int] = None,
        include_private: bool = True,
        include_loopback: bool = False,
        include_multicast: bool = False,
    ):
        # 解析 version
        if version not in (4, 6, 0):
            raise StrategyError(
                f"CIDRStrategy: IP 版本必须是 4、6 或 0（随机），得到: {version}"
            )
        self.version = CIDRVersion(version) if version else CIDRVersion.BOTH

        # 解析 network
        self.network = None
        if network:
            try:
                # 验证并标准化网络地址
                self.network = ipaddress.ip_network(network, strict=False)
            except ValueError as e:
                raise StrategyError(f"CIDRStrategy: 无效的网络地址 {network!r}: {e}")

        self.prefix_length = prefix_length
        self.include_private = include_private
        self.include_loopback = include_loopback
        self.include_multicast = include_multicast

        # 设置前缀范围
        if self.network:
            self.min_prefix = self.network.prefixlen
            self.max_prefix = self.network.prefixlen
        else:
            self.min_prefix = min_prefix
            self.max_prefix = max_prefix

        # 验证前缀长度
        if self.prefix_length is not None:
            if self.version != CIDRVersion.IPV6:
                if not 0 <= self.prefix_length <= 32:
                    raise StrategyError(
                        f"CIDRStrategy: IPv4 前缀长度必须在 0-32 范围内，当前为 {self.prefix_length}"
                    )
            if self.version != CIDRVersion.IPV4:
                if not 0 <= self.prefix_length <= 128:
                    raise StrategyError(
                        f"CIDRStrategy: IPv6 前缀长度必须在 0-128 范围内，当前为 {self.prefix_length}"
                    )

    def generate(self, ctx: StrategyContext) -> str:
        """生成 CIDR 字符串"""
        # 如果指定了网络，直接使用
        if self.network:
            return str(self.network)

        # 决定 IP 版本
        if self.version == CIDRVersion.BOTH:
            is_ipv6 = random.random() < 0.3  # 30% 概率生成 IPv6
        else:
            is_ipv6 = self.version == CIDRVersion.IPV6

        if is_ipv6:
            return self._generate_ipv6_cidr()
        return self._generate_ipv4_cidr()

    def _generate_ipv4_cidr(self) -> str:
        """生成 IPv4 CIDR"""
        # 确定前缀长度
        if self.prefix_length is not None:
            prefix_len = self.prefix_length
        else:
            min_p = self.min_prefix if self.min_prefix is not None else self.DEFAULT_IPV4_MIN_PREFIX
            max_p = self.max_prefix if self.max_prefix is not None else self.DEFAULT_IPV4_MAX_PREFIX
            prefix_len = random.randint(min_p, min(max_p, 32))

        # 生成网络地址
        # 选择网络类型
        network_types = []
        if self.include_private:
            network_types.extend([
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
            ])
        if self.include_loopback:
            network_types.append("127.0.0.0/8")
        if self.include_multicast:
            network_types.append("224.0.0.0/4")

        # 默认包含公网地址
        network_types.append("global")

        chosen_type = random.choice(network_types)

        if chosen_type == "global":
            # 生成公网地址
            first_octet = random.randint(1, 223)
            # 排除特殊地址
            while first_octet in [10, 127, 172, 192, 224, 240]:
                if first_octet == 10:
                    first_octet = random.randint(1, 223)
                elif first_octet == 127:
                    first_octet = random.randint(1, 223)
                elif first_octet == 172:
                    first_octet = random.choice(list(range(1, 172)) + list(range(173, 224)))
                elif first_octet == 192:
                    first_octet = random.choice(list(range(1, 192)) + list(range(193, 224)))
                else:
                    first_octet = random.randint(1, 223)

            network_int = (first_octet << 24) | random.randint(0, 0xFFFFFF)
        else:
            # 从选定网段中随机生成
            base_network = ipaddress.IPv4Network(chosen_type, strict=False)
            # 计算随机偏移
            max_offset = 1 << (24 - base_network.prefixlen)
            offset = random.randint(0, max_offset - 1)
            network_int = int(base_network.network_address) + (offset << 24 >> base_network.prefixlen << 8)

        # 根据前缀长度对齐网络地址
        network_int = network_int >> (32 - prefix_len) << (32 - prefix_len)

        return f"{self._int_to_ipv4(network_int)}/{prefix_len}"

    def _generate_ipv6_cidr(self) -> str:
        """生成 IPv6 CIDR"""
        # 确定前缀长度
        if self.prefix_length is not None:
            prefix_len = self.prefix_length
        else:
            min_p = self.min_prefix if self.min_prefix is not None else self.DEFAULT_IPV6_MIN_PREFIX
            max_p = self.max_prefix if self.max_prefix is not None else self.DEFAULT_IPV6_MAX_PREFIX
            prefix_len = random.randint(min_p, min(max_p, 128))

        # 生成网络地址
        # 大部分是全局单播（2000::/3）
        if self.include_private or random.random() < 0.7:
            # 全局单播
            prefix_int = 0x2000 << 112  # 2000::/3 的起始
            # 添加随机部分
            random_bits = prefix_len - 3 if prefix_len > 3 else 0
            if random_bits > 0:
                random_part = random.randint(0, (1 << random_bits) - 1)
                prefix_int |= random_part << (128 - prefix_len)
        else:
            # 唯一本地（fd00::/8）
            prefix_int = 0xFD << 120
            random_bits = prefix_len - 8 if prefix_len > 8 else 0
            if random_bits > 0:
                random_part = random.randint(0, (1 << random_bits) - 1)
                prefix_int |= random_part << (128 - prefix_len)

        return f"{self._int_to_ipv6(prefix_int)}/{prefix_len}"

    def _int_to_ipv4(self, n: int) -> str:
        """整数转 IPv4 字符串"""
        return f"{(n >> 24) & 0xFF}.{(n >> 16) & 0xFF}.{(n >> 8) & 0xFF}.{n & 0xFF}"

    def _int_to_ipv6(self, n: int) -> str:
        """整数转 IPv6 字符串"""
        return str(ipaddress.IPv6Address(n))

    def values(self) -> Optional[List[str]]:
        """完整值域（CIDR 空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "0.0.0.0/0",                         # IPv4 最大范围
            "0.0.0.0/32",                        # IPv4 最小范围
            "255.255.255.255/32",                # IPv4 单地址
            "192.168.0.0/16",                    # 私有网段
            "10.0.0.0/8",                        # A 类私有
            "172.16.0.0/12",                     # B 类私有
            "127.0.0.0/8",                       # 回环
            "::/0",                              # IPv6 最大范围
            "::/128",                            # IPv6 最小范围
            "2001:db8::/32",                     # 文档用 IPv6
            "fe80::/10",                         # 链路本地
            "ff00::/8",                          # 组播
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["192.168.0.0/24"],                  # IPv4 私有网段
            ["10.0.0.0/8"],                      # IPv4 A 类私有
            ["2001:db8::/32"],                   # IPv6 文档网段
            ["fe80::/10"],                       # IPv6 链路本地
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "192.168.1.0/33",                    # IPv4 前缀超长
            "192.168.1.0/-1",                    # 负数前缀
            "192.168.1.256/24",                  # 非法 IP
            "192.168.1.0/24/16",                 # 多个前缀
            "192.168.1",                         # 不完整
            "",                                  # 空字符串
            None,                                # None
            "gggg::/64",                         # 非法字符
            "::/129",                            # IPv6 前缀超长
        ]
