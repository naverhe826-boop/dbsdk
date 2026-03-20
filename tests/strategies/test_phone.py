"""手机号策略测试

测试覆盖：
- 合法值生成
- 运营商号段
- 边界值
- 等价类
- 非法值
- 参数校验
"""

import pytest

from data_builder import PhoneStrategy, StrategyContext
from data_builder.exceptions import StrategyError


class TestPhoneStrategy:
    """手机号策略测试"""
    
    def test_basic_generation(self):
        """测试基本生成功能"""
        strategy = PhoneStrategy()
        
        for _ in range(10):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(phone) == 11
            
            # 验证格式
            assert phone.isdigit()
            
            # 验证以1开头
            assert phone[0] == "1"
    
    def test_mobile_carrier(self):
        """测试中国移动号段"""
        strategy = PhoneStrategy(carrier="mobile")
        
        mobile_prefixes = [
            "134", "135", "136", "137", "138", "139",
            "147", "150", "151", "152", "157", "158", "159",
            "178", "182", "183", "184", "187", "188", "198",
        ]
        
        for _ in range(20):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            prefix = phone[:3]
            
            assert prefix in mobile_prefixes, f"号段 {prefix} 不属于中国移动"
    
    def test_unicom_carrier(self):
        """测试中国联通号段"""
        strategy = PhoneStrategy(carrier="unicom")
        
        unicom_prefixes = [
            "130", "131", "132", "145", "155", "156", "166",
            "175", "176", "185", "186",
        ]
        
        for _ in range(20):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            prefix = phone[:3]
            
            assert prefix in unicom_prefixes, f"号段 {prefix} 不属于中国联通"
    
    def test_telecom_carrier(self):
        """测试中国电信号段"""
        strategy = PhoneStrategy(carrier="telecom")
        
        telecom_prefixes = [
            "133", "149", "153", "173", "174", "177",
            "180", "181", "189", "191", "199",
        ]
        
        for _ in range(20):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            prefix = phone[:3]
            
            assert prefix in telecom_prefixes, f"号段 {prefix} 不属于中国电信"
    
    def test_virtual_carrier(self):
        """测试虚拟运营商号段"""
        strategy = PhoneStrategy(number_type="virtual")
        
        virtual_prefixes = ["170", "171", "162", "165", "167"]
        
        for _ in range(20):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            prefix = phone[:3]
            
            assert prefix in virtual_prefixes, f"号段 {prefix} 不属于虚拟运营商"
    
    def test_random_carrier(self):
        """测试随机运营商"""
        strategy = PhoneStrategy(carrier="random")
        
        for _ in range(10):
            phone = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(phone) == 11
            
            # 验证以1开头
            assert phone[0] == "1"
    
    def test_boundary_values(self):
        """测试边界值"""
        strategy = PhoneStrategy()
        boundaries = strategy.boundary_values()
        
        assert boundaries is not None
        assert len(boundaries) >= 4
        
        # 验证所有边界值都是11位
        for phone in boundaries:
            assert len(phone) == 11
            assert phone.isdigit()
    
    def test_equivalence_classes(self):
        """测试等价类"""
        strategy = PhoneStrategy()
        classes = strategy.equivalence_classes()
        
        assert classes is not None
        assert len(classes) >= 4
        
        # 验证每个等价类都有样本
        for cls in classes:
            assert len(cls) >= 1
            
            # 验证所有样本都是11位
            for phone in cls:
                assert len(phone) == 11
    
    def test_invalid_values(self):
        """测试非法值"""
        strategy = PhoneStrategy()
        invalid = strategy.invalid_values()
        
        assert invalid is not None
        assert len(invalid) >= 5
        
        # 验证非法值列表包含不同类型的错误
        error_types = {
            "位数错误": False,
            "非法字符": False,
            "非法开头": False,
            "类型错误": False,
        }
        
        for value in invalid:
            if isinstance(value, int) or value is None:
                error_types["类型错误"] = True
            elif isinstance(value, str):
                if len(value) != 11:
                    error_types["位数错误"] = True
                elif not value.isdigit():
                    error_types["非法字符"] = True
                elif value[0] != "1":
                    error_types["非法开头"] = True
        
        # 至少包含3种错误类型
        assert sum(error_types.values()) >= 3
    
    def test_invalid_carrier(self):
        """测试无效运营商参数"""
        with pytest.raises(StrategyError):
            PhoneStrategy(carrier="unknown_carrier")
    
    def test_invalid_number_type(self):
        """测试无效号码类型参数"""
        with pytest.raises(StrategyError):
            PhoneStrategy(number_type="unknown_type")
