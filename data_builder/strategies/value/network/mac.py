"""MAC 地址生成策略"""

import random
from enum import Enum
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError
from .constants import VENDOR_OUIS, MAC_FORMATS


class MACFormat(Enum):
    """MAC 地址输出格式"""
    COLON = "colon"          # xx:xx:xx:xx:xx:xx
    HYPHEN = "hyphen"        # xx-xx-xx-xx-xx-xx
    DOT = "dot"              # xxxx.xxxx.xxxx
    NO_SEPARATOR = "no_separator"  # xxxxxxxxxxxx


class MACAddressType(Enum):
    """MAC 地址类型"""
    UNICAST = "unicast"      # 单播地址
    MULTICAST = "multicast"  # 组播地址
    BROADCAST = "broadcast"  # 广播地址
    RANDOM = "random"        # 随机（默认）


class MACAdminType(Enum):
    """MAC 地址管理类型"""
    GLOBAL = "global"        # 全球唯一（UAA）
    LOCAL = "local"          # 本地管理（LAA）
    RANDOM = "random"        # 随机（默认）


def _generate_random_octet() -> int:
    """生成随机字节"""
    return random.randint(0x00, 0xFF)


def _format_mac(octets: List[int], format: MACFormat) -> str:
    """格式化 MAC 地址"""
    hex_octets = [f"{o:02x}" for o in octets]
    
    if format == MACFormat.COLON:
        return ":".join(hex_octets)
    elif format == MACFormat.HYPHEN:
        return "-".join(hex_octets)
    elif format == MACFormat.DOT:
        return f"{hex_octets[0]}{hex_octets[1]}.{hex_octets[2]}{hex_octets[3]}.{hex_octets[4]}{hex_octets[5]}"
    else:  # NO_SEPARATOR
        return "".join(hex_octets)


class MACStrategy(Strategy):
    """MAC 地址生成策略

    生成符合 IEEE 802 标准的 MAC 地址。

    MAC 地址结构：
    - 前3字节：OUI（组织唯一标识符）
    - 后3字节：NIC 特定部分

    特殊位：
    - 第1字节最低位：单播/多播（0=单播，1=组播）
    - 第1字节次低位：全局/本地（0=全局，1=本地）

    参数：
    - format: 输出格式（colon/hyphen/dot/no_separator，默认 "colon"）
    - address_type: 地址类型（unicast/multicast/broadcast/random，默认 "random"）
    - admin_type: 管理类型（global/local/random，默认 "random"）
    - oui: 指定 OUI（如 "00:11:22" 或 "001122"，可选）
    - oui_list: 自定义 OUI 列表（可选）
    - use_vendor_oui: 是否使用真实厂商 OUI（默认 True）
    - uppercase: 是否使用大写字母（默认 False）
    """

    # 广播 MAC 地址
    BROADCAST_MAC = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

    def __init__(
        self,
        format: str = "colon",
        address_type: str = "random",
        admin_type: str = "random",
        oui: Optional[str] = None,
        oui_list: Optional[List[str]] = None,
        use_vendor_oui: bool = True,
        uppercase: bool = False,
    ):
        # 解析 format
        try:
            self.output_format = MACFormat(format.lower())
        except ValueError:
            raise StrategyError(
                f"MACStrategy: 不支持的输出格式 {format!r}，"
                f"可选值: {[f.value for f in MACFormat]}"
            )

        # 解析 address_type
        try:
            self.address_type = MACAddressType(address_type.lower())
        except ValueError:
            raise StrategyError(
                f"MACStrategy: 不支持的地址类型 {address_type!r}，"
                f"可选值: {[t.value for t in MACAddressType]}"
            )

        # 解析 admin_type
        try:
            self.admin_type = MACAdminType(admin_type.lower())
        except ValueError:
            raise StrategyError(
                f"MACStrategy: 不支持的管理类型 {admin_type!r}，"
                f"可选值: {[t.value for t in MACAdminType]}"
            )

        # 解析 OUI
        self.oui = self._parse_oui(oui) if oui else None
        self.oui_list = oui_list
        self.use_vendor_oui = use_vendor_oui
        self.uppercase = uppercase

    def _parse_oui(self, oui: str) -> List[int]:
        """解析 OUI 字符串为字节列表"""
        # 移除分隔符
        oui_clean = oui.replace(":", "").replace("-", "").replace(".", "")
        if len(oui_clean) != 6:
            raise StrategyError(f"MACStrategy: OUI 必须是 3 字节（6 个十六进制字符），得到: {oui}")
        try:
            return [int(oui_clean[i:i+2], 16) for i in range(0, 6, 2)]
        except ValueError:
            raise StrategyError(f"MACStrategy: 无效的 OUI 格式: {oui}")

    def generate(self, ctx: StrategyContext) -> str:
        """生成 MAC 地址"""
        octets = self._generate_octets()
        mac = _format_mac(octets, self.output_format)
        if self.uppercase:
            mac = mac.upper()
        return mac

    def _generate_octets(self) -> List[int]:
        """生成 6 字节 MAC 地址"""
        # 广播地址特殊处理
        if self.address_type == MACAddressType.BROADCAST:
            return self.BROADCAST_MAC.copy()

        # 初始化 6 字节
        octets = [0] * 6

        # 生成 OUI（前3字节）
        oui_octets = self._generate_oui()
        octets[:3] = oui_octets

        # 生成 NIC 部分（后3字节）
        nic_octets = [_generate_random_octet() for _ in range(3)]
        octets[3:] = nic_octets

        # 设置单播/多播位（第1字节最低位）
        if self.address_type == MACAddressType.UNICAST:
            octets[0] &= 0xFE  # 清除最低位（单播）
        elif self.address_type == MACAddressType.MULTICAST:
            octets[0] |= 0x01  # 设置最低位（组播）
        # RANDOM 时保持随机

        # 设置全局/本地位（第1字节次低位）
        if self.admin_type == MACAdminType.GLOBAL:
            octets[0] &= 0xFD  # 清除次低位（全局）
        elif self.admin_type == MACAdminType.LOCAL:
            octets[0] |= 0x02  # 设置次低位（本地）
        # RANDOM 时保持随机

        return octets

    def _generate_oui(self) -> List[int]:
        """生成 OUI（前3字节）"""
        # 如果指定了 OUI，使用指定的
        if self.oui:
            return self.oui.copy()

        # 如果有自定义 OUI 列表，从中选择
        if self.oui_list:
            oui_str = random.choice(self.oui_list)
            return self._parse_oui(oui_str)

        # 如果使用真实厂商 OUI
        if self.use_vendor_oui and VENDOR_OUIS:
            oui_str = random.choice(list(VENDOR_OUIS.keys()))
            return self._parse_oui(oui_str)

        # 否则随机生成
        return [_generate_random_octet() for _ in range(3)]

    def values(self) -> Optional[List[str]]:
        """完整值域（MAC 地址空间太大，返回 None）"""
        return None

    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        return [
            "00:00:00:00:00:00",                 # 全零
            "FF:FF:FF:FF:FF:FF",                 # 全一（广播）
            "01:00:00:00:00:00",                 # 组播地址
            "02:00:00:00:00:00",                 # 本地管理地址
            "00:11:22:33:44:55",                 # 典型格式
            "00-11-22-33-44-55",                 # 连字符格式
            "0011.2233.4455",                    # 点分格式
            "001122334455",                      # 无分隔符
        ]

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        return [
            ["00:11:22:33:44:55"],               # 单播、全局
            ["01:11:22:33:44:55"],               # 组播
            ["02:11:22:33:44:55"],               # 本地管理
            ["FF:FF:FF:FF:FF:FF"],               # 广播
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "00:11:22:33:44",                    # 字节数不足
            "00:11:22:33:44:55:66",              # 字节数过多
            "GG:HH:II:JJ:KK:LL",                 # 非法字符
            "00:11:22:33:44:55:66:77",           # 过长
            "00-11-22-33-44",                    # 格式错误
            "",                                  # 空字符串
            None,                                # None
            "00:11:22:33:44:55: ",               # 尾随空格
            " 00:11:22:33:44:55",                # 前导空格
            "00:11:22:33:44:55:extra",           # 额外内容
        ]
