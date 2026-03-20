"""银行卡号策略测试

测试覆盖：
- 合法值生成
- Luhn算法验证
- 边界值
- 等价类
- 非法值
- 参数校验
"""

import pytest

from data_builder import BankCardStrategy, StrategyContext
from data_builder.exceptions import StrategyError


def luhn_check(card_number: str) -> bool:
    """验证银行卡号是否符合Luhn算法"""
    total = 0
    reverse_digits = card_number[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:  # 偶数位
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


class TestBankCardStrategy:
    """银行卡号策略测试"""
    
    def test_basic_generation(self):
        """测试基本生成功能"""
        strategy = BankCardStrategy()
        
        for _ in range(10):
            card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(card) == 16
            
            # 验证格式
            assert card.isdigit()
            
            # 验证Luhn算法
            assert luhn_check(card), f"银行卡号 {card} 不符合Luhn算法"
    
    def test_specific_bank(self):
        """测试指定银行"""
        banks = ["icbc", "cbc", "abc", "boc", "cmb"]
        
        for bank in banks:
            strategy = BankCardStrategy(bank=bank)
            card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(card) == 16
            
            # 验证Luhn算法
            assert luhn_check(card)
    
    def test_random_bank(self):
        """测试随机银行"""
        strategy = BankCardStrategy(bank="random")
        
        for _ in range(10):
            card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(card) == 16
            
            # 验证Luhn算法
            assert luhn_check(card)
    
    def test_luhn_algorithm_validation(self):
        """测试Luhn算法验证"""
        strategy = BankCardStrategy()
        
        # 生成100个卡号，全部验证通过
        for _ in range(100):
            card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            assert luhn_check(card), f"银行卡号 {card} Luhn验证失败"
    
    def test_boundary_values(self):
        """测试边界值"""
        strategy = BankCardStrategy()
        boundaries = strategy.boundary_values()
        
        assert boundaries is not None
        assert len(boundaries) >= 4
        
        # 验证所有边界值都是16位且符合Luhn算法
        for card in boundaries:
            assert len(card) == 16
            assert luhn_check(card)
    
    def test_equivalence_classes(self):
        """测试等价类"""
        strategy = BankCardStrategy()
        classes = strategy.equivalence_classes()
        
        assert classes is not None
        assert len(classes) >= 5
        
        # 验证每个等价类都有样本
        for cls in classes:
            assert len(cls) >= 1
            
            # 验证所有样本符合Luhn算法
            for card in cls:
                assert luhn_check(card)
    
    def test_invalid_values(self):
        """测试非法值"""
        strategy = BankCardStrategy()
        invalid = strategy.invalid_values()
        
        assert invalid is not None
        assert len(invalid) >= 5
        
        # 验证非法值列表包含不同类型的错误
        error_types = {
            "位数错误": False,
            "Luhn校验错误": False,
            "非法BIN": False,
            "类型错误": False,
        }
        
        for value in invalid:
            if isinstance(value, int) or value is None:
                error_types["类型错误"] = True
            elif isinstance(value, str):
                if len(value) != 16:
                    error_types["位数错误"] = True
                elif value[:6] == "999999":
                    error_types["非法BIN"] = True
        
        # 至少包含3种错误类型
        assert sum(error_types.values()) >= 3
    
    def test_invalid_bank(self):
        """测试无效银行参数"""
        with pytest.raises(StrategyError):
            BankCardStrategy(bank="unknown_bank")
    
    def test_invalid_card_type(self):
        """测试无效卡类型参数"""
        with pytest.raises(StrategyError):
            BankCardStrategy(card_type="unknown_type")
    
    def test_bin_prefix(self):
        """测试BIN前缀"""
        strategy = BankCardStrategy(bank="icbc")
        
        # 生成10张工商银行卡
        for _ in range(10):
            card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            bin_code = card[:6]
            
            # 工商银行的BIN应该在数据文件中定义的范围内
            # 这里只验证长度和数字格式
            assert len(bin_code) == 6
            assert bin_code.isdigit()
