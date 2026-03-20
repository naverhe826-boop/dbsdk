"""银行卡号生成策略

支持生成符合Luhn算法的银行卡号：
- 6位BIN号段（银行识别码）
- 9位账号部分（随机生成）
- 1位校验位（Luhn算法自动计算）
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 加载银行BIN数据
def _load_bank_bins() -> Dict[str, Dict[str, Any]]:
    """加载银行BIN数据"""
    data_file = Path(__file__).parent.parent.parent.parent / "data" / "bank_bins.json"
    if not data_file.exists():
        # 如果文件不存在，返回基本数据
        return {
            "icbc": {"name": "工商银行", "bins": ["622202", "622203"]},
            "cbc": {"name": "建设银行", "bins": ["622700", "622280"]},
            "abc": {"name": "农业银行", "bins": ["622848", "622849"]},
            "boc": {"name": "中国银行", "bins": ["621660", "621661"]},
        }
    
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


# 银行BIN缓存
_BANK_BINS = _load_bank_bins()


def _luhn_check(card_number: str) -> bool:
    """验证银行卡号是否符合Luhn算法
    
    Args:
        card_number: 银行卡号
        
    Returns:
        是否有效
    """
    # 从右向左，偶数位乘以2，大于9则减9
    total = 0
    reverse_digits = card_number[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:  # 偶数位（从右向左，索引为奇数）
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


def _calculate_luhn_check_digit(card_number_15: str) -> int:
    """计算Luhn校验位
    
    Args:
        card_number_15: 银行卡号前15位
        
    Returns:
        校验位（第16位）
    """
    # 从右向左，偶数位乘以2，大于9则减9
    total = 0
    reverse_digits = card_number_15[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 0:  # 奇数位（从右向左，索引为偶数，但最后一位还没加）
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    # 计算校验位
    check_digit = (10 - (total % 10)) % 10
    return check_digit


def _generate_account_number(length: int = 9) -> str:
    """生成账号部分（随机数字）
    
    Args:
        length: 账号长度
        
    Returns:
        账号字符串
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


class BankCardStrategy(Strategy):
    """银行卡号生成策略
    
    参数：
    - bank: 银行代码（"icbc", "cbc", "abc", "boc", "ccb", "psbc", "cmb", "citic", 
                      "cebb", "hxb", "cib", "cmbc", "pingan", "pab", "gdb", "random"）
    - card_type: 卡类型（"debit", "credit"，暂未区分，默认 "debit"）
    
    示例：
        >>> strategy = BankCardStrategy(bank="icbc")
        >>> card = strategy.generate(StrategyContext(field_path="", field_schema={}))
        '6222021234567890'
    """
    
    SUPPORTED_BANKS = [
        "icbc", "cbc", "abc", "boc", "ccb", "psbc", "cmb", "citic",
        "cebb", "hxb", "cib", "cmbc", "pingan", "pab", "gdb", "random"
    ]
    
    def __init__(
        self,
        bank: str = "random",
        card_type: str = "debit",
    ):
        # 参数校验
        if bank not in self.SUPPORTED_BANKS:
            raise StrategyError(
                f"BankCardStrategy: 不支持的银行 {bank!r}，"
                f"可选值: {self.SUPPORTED_BANKS}"
            )
        
        if card_type not in ["debit", "credit"]:
            raise StrategyError(
                f"BankCardStrategy: card_type 必须是 'debit' 或 'credit'，当前为 {card_type!r}"
            )
        
        self.bank = bank
        self.card_type = card_type
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成银行卡号"""
        # 1. 选择银行BIN
        if self.bank == "random":
            # 随机选择一个银行
            bank_code = random.choice(list(_BANK_BINS.keys()))
        else:
            bank_code = self.bank
        
        # 获取该银行的BIN列表
        if bank_code not in _BANK_BINS:
            raise StrategyError(f"BankCardStrategy: 找不到银行 {bank_code} 的BIN数据")
        
        bin_list = _BANK_BINS[bank_code]["bins"]
        bin_code = random.choice(bin_list)
        
        # 2. 生成账号部分（9位）
        account_number = _generate_account_number(9)
        
        # 3. 组合前15位
        card_number_15 = bin_code + account_number
        
        # 4. 计算校验位
        check_digit = _calculate_luhn_check_digit(card_number_15)
        
        # 5. 返回完整银行卡号（16位）
        return card_number_15 + str(check_digit)
    
    def values(self) -> Optional[List[str]]:
        """完整值域（银行卡号空间巨大，返回 None）"""
        return None
    
    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = []
        
        # 不同银行的代表卡号
        for bank_code in ["icbc", "cbc", "abc", "boc"]:
            strategy = BankCardStrategy(bank=bank_code)
            boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        return boundaries
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        classes = []
        
        # 按银行分组
        for bank_code in ["icbc", "cbc", "abc", "boc", "cmb"]:
            strategy = BankCardStrategy(bank=bank_code)
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
        
        return classes
    
    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "123456789012345",      # 15位
            "12345678901234567",    # 17位
            "6222021234567890",     # 正确位数但Luhn校验错误
            "9999991234567890",     # 非法BIN
            "6222021234A67890",     # 包含字母
            "6222021234 67890",     # 包含空格
            6222021234567890,       # 数字类型
            None,                   # None
            "",                     # 空字符串
        ]
