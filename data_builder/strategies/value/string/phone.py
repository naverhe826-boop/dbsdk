"""手机号生成策略

支持生成符合国内手机号格式：
- 11位手机号（1开头）
- 支持三大运营商号段（移动、联通、电信）
- 支持虚拟运营商号段
"""

import random
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 运营商号段数据
# 数据来源：https://zh.wikipedia.org/wiki/中国手机号码
CARRIER_PREFIXES = {
    "mobile": [  # 中国移动
        "134", "135", "136", "137", "138", "139",
        "147", "150", "151", "152", "157", "158", "159",
        "178", "182", "183", "184", "187", "188", "198",
    ],
    "unicom": [  # 中国联通
        "130", "131", "132", "145", "155", "156", "166",
        "175", "176", "185", "186",
    ],
    "telecom": [  # 中国电信
        "133", "149", "153", "173", "174", "177",
        "180", "181", "189", "191", "199",
    ],
}

# 虚拟运营商号段
VIRTUAL_PREFIXES = [
    "170", "171", "162", "165", "167",
]

# 所有号段（不包括虚拟运营商）
ALL_PREFIXES = (
    CARRIER_PREFIXES["mobile"] +
    CARRIER_PREFIXES["unicom"] +
    CARRIER_PREFIXES["telecom"]
)


def _generate_suffix(length: int = 8) -> str:
    """生成手机号后8位
    
    Args:
        length: 后缀长度
        
    Returns:
        后缀字符串
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


class PhoneStrategy(Strategy):
    """手机号生成策略
    
    参数：
    - carrier: 运营商（"mobile", "unicom", "telecom", "random"，默认 "random"）
    - number_type: 号码类型（"normal", "virtual"，默认 "normal"）
    
    示例：
        >>> strategy = PhoneStrategy(carrier="mobile")
        >>> phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
        '13812345678'
    """
    
    SUPPORTED_CARRIERS = ["mobile", "unicom", "telecom", "random"]
    
    def __init__(
        self,
        carrier: str = "random",
        number_type: str = "normal",
    ):
        # 参数校验
        if carrier not in self.SUPPORTED_CARRIERS:
            raise StrategyError(
                f"PhoneStrategy: 不支持的运营商 {carrier!r}，"
                f"可选值: {self.SUPPORTED_CARRIERS}"
            )
        
        if number_type not in ["normal", "virtual"]:
            raise StrategyError(
                f"PhoneStrategy: number_type 必须是 'normal' 或 'virtual'，当前为 {number_type!r}"
            )
        
        self.carrier = carrier
        self.number_type = number_type
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成手机号"""
        # 1. 选择号段前缀
        if self.number_type == "virtual":
            # 虚拟运营商号段
            prefix = random.choice(VIRTUAL_PREFIXES)
        elif self.carrier == "random":
            # 随机选择任意号段
            prefix = random.choice(ALL_PREFIXES)
        else:
            # 指定运营商号段
            prefix = random.choice(CARRIER_PREFIXES[self.carrier])
        
        # 2. 生成后8位
        suffix = _generate_suffix(8)
        
        # 3. 返回完整手机号（11位）
        return prefix + suffix
    
    def values(self) -> Optional[List[str]]:
        """完整值域（手机号空间巨大，返回 None）"""
        return None
    
    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = []
        
        # 不同运营商的代表号码
        for carrier in ["mobile", "unicom", "telecom"]:
            strategy = PhoneStrategy(carrier=carrier)
            boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        # 虚拟运营商
        strategy = PhoneStrategy(number_type="virtual")
        boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        return boundaries
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        classes = []
        
        # 按运营商分组
        for carrier in ["mobile", "unicom", "telecom"]:
            strategy = PhoneStrategy(carrier=carrier)
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
        
        # 虚拟运营商
        strategy = PhoneStrategy(number_type="virtual")
        classes.append([
            strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(2)
        ])
        
        return classes
    
    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "1234567890",           # 10位
            "123456789012",         # 12位
            "22345678901",          # 非法开头（2开头）
            "02345678901",          # 非法开头（0开头）
            "1234567890A",          # 包含字母
            "12345-67890",          # 包含特殊字符
            12345678901,            # 数字类型
            None,                   # None
            "",                     # 空字符串
        ]
