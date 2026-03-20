"""身份证号策略测试

测试覆盖：
- 合法值生成
- 边界值（最小/最大年龄）
- 等价类（性别、年龄段、地区）
- 非法值
- 参数校验
"""

import pytest
from datetime import datetime

from data_builder import IdCardStrategy, StrategyContext
from data_builder.exceptions import StrategyError


class TestIdCardStrategy:
    """身份证号策略测试"""
    
    def test_basic_generation(self):
        """测试基本生成功能"""
        strategy = IdCardStrategy()
        
        for _ in range(10):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert len(id_card) == 18
            
            # 验证格式（前17位为数字，最后一位可以是数字或X）
            assert id_card[:17].isdigit()
            assert id_card[17] in "0123456789X"
            
            # 验证地区码（前6位）
            region_code = id_card[:6]
            assert region_code.isdigit()
    
    def test_age_range(self):
        """测试年龄范围"""
        min_age = 25
        max_age = 35
        strategy = IdCardStrategy(min_age=min_age, max_age=max_age)
        
        current_year = datetime.now().year
        
        for _ in range(20):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 提取出生年份
            birth_year = int(id_card[6:10])
            age = current_year - birth_year
            
            # 验证年龄范围（允许±1的误差，因为生日可能还没到）
            assert min_age - 1 <= age <= max_age + 1
    
    def test_gender_male(self):
        """测试男性身份证号（第17位为奇数）"""
        strategy = IdCardStrategy(gender="male")
        
        for _ in range(20):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            gender_digit = int(id_card[16])  # 第17位（索引16）
            
            assert gender_digit % 2 == 1, f"第17位应为奇数，实际为 {gender_digit}"
    
    def test_gender_female(self):
        """测试女性身份证号（第17位为偶数）"""
        strategy = IdCardStrategy(gender="female")
        
        for _ in range(20):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            gender_digit = int(id_card[16])  # 第17位（索引16）
            
            assert gender_digit % 2 == 0, f"第17位应为偶数，实际为 {gender_digit}"
    
    def test_region_specific(self):
        """测试指定地区码"""
        region_code = "110101"  # 北京市东城区
        strategy = IdCardStrategy(region=region_code)
        
        for _ in range(10):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证地区码
            assert id_card[:6] == region_code
    
    def test_check_code_calculation(self):
        """测试校验码计算"""
        strategy = IdCardStrategy()
        
        # 校验码加权因子
        weighted_factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_code_map = {
            0: "1", 1: "0", 2: "X", 3: "9", 4: "8",
            5: "7", 6: "6", 7: "5", 8: "4", 9: "3", 10: "2"
        }
        
        for _ in range(10):
            id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 计算加权和
            weighted_sum = sum(int(id_card[i]) * weighted_factors[i] for i in range(17))
            remainder = weighted_sum % 11
            expected_check_code = check_code_map[remainder]
            
            # 验证校验码
            assert id_card[17] == expected_check_code
    
    def test_boundary_values(self):
        """测试边界值"""
        strategy = IdCardStrategy()
        boundaries = strategy.boundary_values()
        
        assert boundaries is not None
        assert len(boundaries) >= 2
        
        # 验证所有边界值都是18位
        for id_card in boundaries:
            assert len(id_card) == 18
    
    def test_equivalence_classes(self):
        """测试等价类"""
        strategy = IdCardStrategy()
        classes = strategy.equivalence_classes()
        
        assert classes is not None
        assert len(classes) >= 3
        
        # 验证每个等价类都有样本
        for cls in classes:
            assert len(cls) >= 1
    
    def test_invalid_values(self):
        """测试非法值"""
        strategy = IdCardStrategy()
        invalid = strategy.invalid_values()
        
        assert invalid is not None
        assert len(invalid) >= 5
        
        # 验证非法值列表包含不同类型的错误
        error_types = {
            "位数错误": False,
            "校验码错误": False,
            "非法地区码": False,
            "类型错误": False,
        }
        
        for value in invalid:
            if isinstance(value, int) or value is None:
                error_types["类型错误"] = True
            elif isinstance(value, str):
                if len(value) != 18:
                    error_types["位数错误"] = True
                elif value[:6] == "999999":
                    error_types["非法地区码"] = True
        
        # 至少包含3种错误类型
        assert sum(error_types.values()) >= 3
    
    def test_invalid_age_range(self):
        """测试无效年龄范围"""
        # 年龄超出范围
        with pytest.raises(StrategyError):
            IdCardStrategy(min_age=-1)
        
        with pytest.raises(StrategyError):
            IdCardStrategy(max_age=200)
        
        # min_age > max_age
        with pytest.raises(StrategyError):
            IdCardStrategy(min_age=50, max_age=30)
    
    def test_invalid_gender(self):
        """测试无效性别参数"""
        with pytest.raises(StrategyError):
            IdCardStrategy(gender="unknown")
    
    def test_invalid_region(self):
        """测试无效地区码"""
        # 长度不对
        with pytest.raises(StrategyError):
            IdCardStrategy(region="11010")
        
        # 非数字
        with pytest.raises(StrategyError):
            IdCardStrategy(region="11010A")
        
        # 不存在的地区码
        with pytest.raises(StrategyError):
            IdCardStrategy(region="999999")
