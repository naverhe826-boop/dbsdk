"""IP 范围生成策略"""

import ipaddress
import random
from enum import Enum
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class IPRangeVersion(Enum):
    """IP 版本"""
    IPV4 = 4
    IPV6 = 6
    BOTH = 0  # 两者随机


class IPRangeStrategy(Strategy):
    """IP 范围生成策略

    生成起始 IP 到结束 IP 的字符串表示，例如 192.168.1.10-192.168.1.100。

    参数：
    - version: IP 版本（4/6/0，0 表示随机，默认 4）
    - start_ip: 指定起始 IP（可选）
    - end_ip: 指定结束 IP（可选）
    - network: 指定网段 CIDR（从中生成范围，可选）
    - min_range: 最小范围大小（IP 数量，默认 2）
    - max_range: 最大范围大小（默认 256 for IPv4, 65536 for IPv6）
    - separator: 分隔符（默认 "-"）
    """

    def __init__(
        self,
        version: int = 4,
        start_ip: Optional[str] = None,
        end_ip: Optional[str] = None,
        network: Optional[str] = None,
        min_range: int = 2,
        max_range: Optional[int] = None,
        separator: str = "-",
    ):
        # 解析 version
        if version not in (4, 6, 0):
            raise StrategyError(
                f"IPRangeStrategy: IP 版本必须是 4、6 或 0（随机），得到: {version}"
            )
        self.version = IPRangeVersion(version) if version else IPRangeVersion.BOTH

        # 解析起始和结束 IP
        self.start_ip = None
        self.end_ip = None

        if start_ip:
            try:
                self.start_ip = ipaddress.ip_address(start_ip)
            except ValueError as e:
                raise StrategyError(f"IPRangeStrategy: 无效的起始 IP {start_ip!r}: {e}")

        if end_ip:
            try:
                self.end_ip = ipaddress.ip_address(end_ip)
            except ValueError as e:
                raise StrategyError(f"IPRangeStrategy: 无效的结束 IP {end_ip!r}: {e}")

        # 验证起始 <= 结束
        if self.start_ip and self.end_ip:
            if self.start_ip > self.end_ip:
                raise StrategyError(
                    f"IPRangeStrategy: 起始 IP ({self.start_ip}) 不能大于结束 IP ({self.end_ip})"
                )
            # 验证同一地址族
            if self.start_ip.version != self.end_ip.version:
                raise StrategyError(
                    f"IPRangeStrategy: 起始 IP 和结束 IP 必须属于同一地址族"
                )

        # 解析网段
        self.network = None
        if network:
            try:
                self.network = ipaddress.ip_network(network, strict=False)
            except ValueError as e:
                raise StrategyError(f"IPRangeStrategy: 无效的网段 {network!r}: {e}")

        self.min_range = max(2, min_range)
        self.max_range = max_range
        self.separator = separator

    def generate(self, ctx: StrategyContext) -> str:
        """生成 IP 范围字符串"""
        # 如果指定了起始和结束 IP
        if self.start_ip and self.end_ip:
            return f"{self.start_ip}{self.separator}{self.end_ip}"

        # 如果指定了起始 IP，需要生成结束 IP
        if self.start_ip:
            end = self._generate_end_ip(self.start_ip)
            return f"{self.start_ip}{self.separator}{end}"

        # 如果指定了网段，从网段中生成
        if self.network:
            return self._generate_from_network()

        # 根据版本生成
        if self.version == IPRangeVersion.BOTH:
            is_ipv6 = random.random() < 0.3
        else:
            is_ipv6 = self.version == IPRangeVersion.IPV6

        if is_ipv6:
            return self._generate_ipv6_range()
        return self._generate_ipv4_range()

    def _generate_end_ip(self, start: ipaddress.IPv4Address) -> str:
        """根据起始 IP 生成结束 IP"""
        start_int = int(start)
        version = start.version

        # 确定范围大小
        max_range = self.max_range if self.max_range else (65536 if version == 6 else 256)
        range_size = random.randint(self.min_range, min(max_range, 10000))

        # 计算结束 IP
        end_int = start_int + range_size - 1

        # 确保不溢出
        if version == 4:
            max_int = 0xFFFFFFFF
        else:
            max_int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

        end_int = min(end_int, max_int)

        if version == 4:
            return str(ipaddress.IPv4Address(end_int))
        return str(ipaddress.IPv6Address(end_int))

    def _generate_from_network(self) -> str:
        """从网段中生成 IP 范围"""
        # 计算可用主机数量
        num_addresses = self.network.num_addresses
        num_hosts = max(0, num_addresses - 2)  # 排除网络地址和广播地址

        if num_hosts < 2:
            # 网络太小，返回网络地址范围
            return f"{self.network.network_address}{self.separator}{self.network.broadcast_address}"

        # 随机选择范围大小
        max_range = self.max_range if self.max_range else num_hosts
        range_size = random.randint(self.min_range, min(max_range, num_hosts))

        # 随机选择起始位置（使用整数计算，避免列举所有主机）
        start_offset = random.randint(0, num_hosts - range_size)

        # 计算起始和结束 IP
        start_ip = self.network.network_address + start_offset + 1  # +1 跳过网络地址
        end_ip = start_ip + range_size - 1

        return f"{start_ip}{self.separator}{end_ip}"

    def _generate_ipv4_range(self) -> str:
        """生成 IPv4 范围"""
        # 从常用网段中随机选择
        networks = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "192.0.2.0/24",  # TEST-NET-1
        ]

        network_str = random.choice(networks)
        network = ipaddress.IPv4Network(network_str, strict=False)

        # 计算可用主机数量
        num_addresses = network.num_addresses
        num_hosts = max(0, num_addresses - 2)  # 排除网络地址和广播地址

        # 确定范围大小
        max_range = self.max_range if self.max_range else min(256, num_hosts)
        range_size = random.randint(self.min_range, min(max_range, num_hosts))

        # 随机选择起始位置（使用整数计算，避免列举所有主机）
        if num_hosts >= 1:
            start_offset = random.randint(0, num_hosts - range_size)
        else:
            start_offset = 0

        # 计算起始和结束 IP
        start_ip = network.network_address + start_offset + 1  # +1 跳过网络地址
        end_ip = start_ip + range_size - 1

        return f"{start_ip}{self.separator}{end_ip}"

    def _generate_ipv6_range(self) -> str:
        """生成 IPv6 范围"""
        # 生成随机起始地址
        start_int = random.randint(0x20000000000000000000000000000000, 0x3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        start = ipaddress.IPv6Address(start_int)

        # 确定范围大小
        max_range = self.max_range if self.max_range else 65536
        range_size = random.randint(self.min_range, min(max_range, 10000))

        end_int = start_int + range_size - 1
        end = ipaddress.IPv6Address(end_int)

        return f"{start}{self.separator}{end}"

    def values(self) -> Optional[List[str]]:
        """完整值域（IP 范围空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "0.0.0.0-0.0.0.1",                  # IPv4 最小范围
            "0.0.0.0-255.255.255.255",           # IPv4 最大范围
            "192.168.1.1-192.168.1.254",         # 典型私有网段
            "10.0.0.1-10.0.0.100",               # A 类私有
            "172.16.0.1-172.16.0.100",           # B 类私有
            "::-::1",                            # IPv6 最小范围
            "::-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # IPv6 最大范围
            "2001:db8::1-2001:db8::100",         # IPv6 文档网段
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["192.168.1.1-192.168.1.100"],       # IPv4 私有
            ["10.0.0.1-10.0.0.10"],              # IPv4 A 类私有
            ["2001:db8::1-2001:db8::100"],       # IPv6 文档
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "192.168.1.100-192.168.1.1",         # 起始 > 结束
            "192.168.1.1-2001::1",               # 混合地址族
            "192.168.1.256-192.168.1.100",       # 非法 IP
            "192.168.1.1",                       # 只有起始
            "-192.168.1.100",                    # 只有结束
            "",                                  # 空字符串
            None,                                # None
            "192.168.1.1--192.168.1.100",        # 多个分隔符
            "gggg::1-gggg::100",                 # 非法字符
        ]
