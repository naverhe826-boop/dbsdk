"""IPv4 地址生成策略"""

import ipaddress
import random
from enum import Enum
from typing import Any, List, Optional, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import (
    IPV4_CLASS_A, IPV4_CLASS_B, IPV4_CLASS_C, IPV4_CLASS_D, IPV4_CLASS_E,
    IPV4_PRIVATE_A, IPV4_PRIVATE_B, IPV4_PRIVATE_C,
    IPV4_LOOPBACK, IPV4_LINK_LOCAL, IPV4_ANY, IPV4_BROADCAST,
    IPV4_MULTICAST_LOCAL, IPV4_MULTICAST_ADMIN,
    IPV4_TEST_NET_1, IPV4_TEST_NET_2, IPV4_TEST_NET_3,
    SUBNET_MASKS,
)


class IPv4Class(Enum):
    """IPv4 地址类别"""
    ANY = "any"                # 任意地址
    A = "a"                    # A类地址
    B = "b"                    # B类地址
    C = "c"                    # C类地址
    D = "d"                    # D类地址（组播）
    E = "e"                    # E类地址（保留）
    PRIVATE = "private"        # 私有地址
    LOOPBACK = "loopback"      # 回环地址
    LINK_LOCAL = "link_local"  # 链路本地地址
    MULTICAST = "multicast"    # 组播地址
    RESERVED = "reserved"      # 保留地址
    TEST = "test"              # 测试网络


class IPv4Format(Enum):
    """IPv4 输出格式"""
    DECIMAL = "decimal"        # 点分十进制（默认）
    BINARY = "binary"          # 二进制
    CIDR = "cidr"              # CIDR 格式


def _tuple_to_ip(t: tuple) -> str:
    """将四元组转换为点分十进制 IP 字符串"""
    return f"{t[0]}.{t[1]}.{t[2]}.{t[3]}"


def _ip_to_tuple(ip: str) -> tuple:
    """将 IP 字符串转换为四元组"""
    parts = ip.split(".")
    return tuple(int(p) for p in parts)


def _ip_to_int(ip: str) -> int:
    """将 IP 字符串转换为整数"""
    return int(ipaddress.IPv4Address(ip))


def _int_to_ip(n: int) -> str:
    """将整数转换为 IP 字符串"""
    return str(ipaddress.IPv4Address(n))


def _random_ip_in_range(start: tuple, end: tuple) -> str:
    """在指定范围内生成随机 IP"""
    start_int = _ip_to_int(_tuple_to_ip(start))
    end_int = _ip_to_int(_tuple_to_ip(end))
    return _int_to_ip(random.randint(start_int, end_int))


def _random_ip_in_network(network: str) -> str:
    """在指定网络内生成随机 IP（排除网络地址和广播地址）"""
    net = ipaddress.IPv4Network(network, strict=False)
    
    # 计算可用主机数量
    num_addresses = net.num_addresses
    
    if num_addresses <= 2:
        # /31 或 /32 网段，返回网络地址
        return str(net.network_address)
    
    # 在主机地址范围内随机选择（排除网络地址 0 和广播地址 num_addresses-1）
    host_index = random.randint(1, num_addresses - 2)
    return str(net.network_address + host_index)


def _get_class_range(ip_class: IPv4Class) -> tuple:
    """获取地址类别对应的范围"""
    ranges = {
        IPv4Class.A: IPV4_CLASS_A,
        IPv4Class.B: IPV4_CLASS_B,
        IPv4Class.C: IPV4_CLASS_C,
        IPv4Class.D: IPV4_CLASS_D,
        IPv4Class.E: IPV4_CLASS_E,
    }
    return ranges.get(ip_class)


class IPv4Strategy(Strategy):
    """IPv4 地址生成策略

    支持的地址类别（ip_class）：
    - any: 任意合法地址
    - a: A类地址（1.0.0.0–126.255.255.255）
    - b: B类地址（128.0.0.0–191.255.255.255）
    - c: C类地址（192.0.0.0–223.255.255.255）
    - d: D类地址/组播（224.0.0.0–239.255.255.255）
    - e: E类地址/保留（240.0.0.0–255.255.255.254）
    - private: 私有地址（10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16）
    - loopback: 回环地址（127.0.0.0/8）
    - link_local: 链路本地（169.254.0.0/16）
    - multicast: 组播地址（D类）
    - reserved: 保留地址
    - test: 测试网络

    参数：
    - ip_class: 地址类别（默认 "any"）
    - subnet: 指定网段 CIDR（可选，如 "10.0.0.0/24"）
    - format: 输出格式（decimal/binary/cidr，默认 "decimal"）
    - prefix_length: CIDR 格式时的前缀长度（默认 24）
    - include_network: 是否包含网络地址（默认 False）
    - include_broadcast: 是否包含广播地址（默认 False）
    """

    # 每个类别对应的私有网络
    _PRIVATE_NETWORKS = [IPV4_PRIVATE_A, IPV4_PRIVATE_B, IPV4_PRIVATE_C]

    def __init__(
        self,
        ip_class: str = "any",
        subnet: Optional[str] = None,
        format: str = "decimal",
        prefix_length: int = 24,
        include_network: bool = False,
        include_broadcast: bool = False,
    ):
        # 解析 ip_class
        try:
            self.ip_class = IPv4Class(ip_class.lower())
        except ValueError:
            raise StrategyError(
                f"IPv4Strategy: 不支持的地址类别 {ip_class!r}，"
                f"可选值: {[c.value for c in IPv4Class]}"
            )

        # 解析 format
        try:
            self.output_format = IPv4Format(format.lower())
        except ValueError:
            raise StrategyError(
                f"IPv4Strategy: 不支持的输出格式 {format!r}，"
                f"可选值: {[f.value for f in IPv4Format]}"
            )

        # 验证 subnet
        if subnet:
            try:
                self.subnet = ipaddress.IPv4Network(subnet, strict=False)
            except ValueError as e:
                raise StrategyError(f"IPv4Strategy: 无效的网段 {subnet!r}: {e}")
        else:
            self.subnet = None

        self.prefix_length = prefix_length
        self.include_network = include_network
        self.include_broadcast = include_broadcast

        # 验证前缀长度
        if not 0 <= self.prefix_length <= 32:
            raise StrategyError(
                f"IPv4Strategy: 前缀长度必须在 0-32 范围内，当前为 {self.prefix_length}"
            )

    def generate(self, ctx: StrategyContext) -> str:
        """生成 IPv4 地址"""
        # 如果指定了网段，在网段内生成
        if self.subnet:
            return self._generate_in_subnet()

        # 否则根据类别生成
        return self._generate_by_class()

    def _generate_in_subnet(self) -> str:
        """在指定网段内生成地址"""
        hosts = list(self.subnet.hosts())
        
        # 构建候选地址列表
        candidates = []
        if hosts:
            candidates = hosts
        if self.include_network:
            candidates.insert(0, self.subnet.network_address)
        if self.include_broadcast:
            candidates.append(self.subnet.broadcast_address)

        if not candidates:
            return str(self.subnet.network_address)

        ip = random.choice(candidates)
        return self._format_output(str(ip))

    def _generate_by_class(self) -> str:
        """根据地址类别生成"""
        if self.ip_class == IPv4Class.ANY:
            # 随机生成任意合法地址（排除特殊用途）
            return self._generate_any()

        elif self.ip_class == IPv4Class.PRIVATE:
            # 从三个私有网段中随机选择一个
            network = random.choice(self._PRIVATE_NETWORKS)
            return self._format_output(_random_ip_in_network(network))

        elif self.ip_class == IPv4Class.LOOPBACK:
            # 在 127.0.0.0/8 中生成
            return self._format_output(_random_ip_in_network(IPV4_LOOPBACK))

        elif self.ip_class == IPv4Class.LINK_LOCAL:
            # 链路本地地址
            return self._format_output(_random_ip_in_network(IPV4_LINK_LOCAL))

        elif self.ip_class == IPv4Class.MULTICAST:
            # 组播地址（D类）
            return self._format_output(_random_ip_in_range(*_get_class_range(IPv4Class.D)))

        elif self.ip_class == IPv4Class.RESERVED:
            # 保留地址（E类 + 特殊地址）
            return self._generate_reserved()

        elif self.ip_class == IPv4Class.TEST:
            # 测试网络
            network = random.choice([IPV4_TEST_NET_1, IPV4_TEST_NET_2, IPV4_TEST_NET_3])
            return self._format_output(_random_ip_in_network(network))

        else:
            # A/B/C/D/E 类
            range_tuple = _get_class_range(self.ip_class)
            if range_tuple:
                return self._format_output(_random_ip_in_range(*range_tuple))

        raise StrategyError(f"IPv4Strategy: 未处理的地址类别 {self.ip_class}")

    def _generate_any(self) -> str:
        """生成任意合法地址"""
        # 排除特殊地址后的范围
        # 1.0.0.0 - 223.255.255.255（排除 D/E 类和特殊用途）
        while True:
            ip_int = random.randint(16777216, 3758096383)  # 1.0.0.0 到 223.255.255.255
            ip = _int_to_ip(ip_int)
            
            # 排除特殊地址
            ip_obj = ipaddress.IPv4Address(ip)
            
            # 跳过回环、链路本地、组播等
            if ip_obj.is_loopback:
                continue
            if ip_obj.is_link_local:
                continue
            if ip_obj.is_multicast:
                continue
            if ip_obj.is_reserved:
                continue
            if str(ip_obj) == IPV4_ANY:
                continue
            
            return self._format_output(ip)

    def _generate_reserved(self) -> str:
        """生成保留地址"""
        # E 类地址或特殊保留地址
        choices = [
            lambda: _random_ip_in_range(*_get_class_range(IPv4Class.E)),
            lambda: IPV4_ANY,
            lambda: IPV4_BROADCAST,
        ]
        return self._format_output(random.choice(choices)())

    def _format_output(self, ip: str) -> str:
        """格式化输出"""
        if self.output_format == IPv4Format.DECIMAL:
            return ip
        elif self.output_format == IPv4Format.BINARY:
            # 转换为二进制点分格式
            parts = ip.split(".")
            binary_parts = [format(int(p), "08b") for p in parts]
            return ".".join(binary_parts)
        elif self.output_format == IPv4Format.CIDR:
            return f"{ip}/{self.prefix_length}"
        return ip

    def values(self) -> Optional[List[str]]:
        """完整值域（IPv4 地址空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = [
            IPV4_ANY,                           # 0.0.0.0
            "1.0.0.0",                          # 最小合法地址
            "126.255.255.255",                  # A类最大
            "128.0.0.0",                        # B类最小
            "191.255.255.255",                  # B类最大
            "192.0.0.0",                        # C类最小
            "223.255.255.255",                  # C类最大
            "224.0.0.0",                        # D类最小（组播）
            "239.255.255.255",                  # D类最大
            "240.0.0.0",                        # E类最小
            "255.255.255.254",                  # E类最大
            IPV4_BROADCAST,                     # 255.255.255.255
            "10.0.0.1",                         # 私有A类最小主机
            "10.255.255.254",                   # 私有A类最大主机
            "172.16.0.1",                       # 私有B类最小主机
            "172.31.255.254",                   # 私有B类最大主机
            "192.168.0.1",                      # 私有C类最小主机
            "192.168.255.254",                  # 私有C类最大主机
            "127.0.0.1",                        # 回环地址
            "169.254.1.0",                      # 链路本地
        ]
        return boundaries

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        # 按地址类别分组
        classes = [
            [IPV4_ANY],                         # 任意地址
            ["1.0.0.1"],                        # A类代表
            ["128.0.0.1"],                      # B类代表
            ["192.0.0.1"],                      # C类代表
            ["224.0.0.1"],                      # D类（组播）
            ["240.0.0.1"],                      # E类（保留）
            ["10.0.0.1"],                       # 私有地址
            ["127.0.0.1"],                      # 回环地址
            ["169.254.1.0"],                    # 链路本地
        ]
        return classes

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "256.0.0.0",                        # 超出范围
            "0.0.0.256",                        # 超出范围
            "1.2.3",                            # 格式错误
            "1.2.3.4.5",                        # 格式错误
            "abc.def.ghi.jkl",                  # 非法字符
            "1.2.3.-1",                         # 负数
            "",                                 # 空字符串
            None,                               # None
            "1.2.3.4.5.6",                      # 过长
            "1..2.3",                           # 连续点号
            ".1.2.3.4",                         # 前导点号
            "1.2.3.4.",                         # 尾随点号
        ]
