"""身份证号生成策略

支持生成符合国家标准的18位身份证号：
- 6位地区码（支持全国省市区）
- 8位出生日期（YYYYMMDD）
- 3位顺序码（第17位奇数为男性，偶数为女性）
- 1位校验码（根据前17位自动计算）
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 加载地区码数据
def _load_region_codes() -> Dict[str, str]:
    """加载地区码数据"""
    data_file = Path(__file__).parent.parent.parent.parent / "data" / "region_codes.json"
    if not data_file.exists():
        # 如果文件不存在，返回基本的省级代码
        return {
            "110000": "北京市",
            "120000": "天津市",
            "310000": "上海市",
            "440000": "广东省",
            "330000": "浙江省",
            "320000": "江苏省",
            "370000": "山东省",
            "510000": "四川省",
        }
    
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


# 地区码缓存
_REGION_CODES = _load_region_codes()

# 校验码加权因子
WEIGHTED_FACTORS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]

# 校验码对照表（余数 -> 校验码）
CHECK_CODE_MAP = {
    0: "1", 1: "0", 2: "X", 3: "9", 4: "8",
    5: "7", 6: "6", 7: "5", 8: "4", 9: "3", 10: "2"
}


def _calculate_check_code(id17: str) -> str:
    """计算身份证号校验码
    
    Args:
        id17: 身份证号前17位
        
    Returns:
        校验码（第18位）
    """
    # 计算加权和
    weighted_sum = sum(int(id17[i]) * WEIGHTED_FACTORS[i] for i in range(17))
    
    # 计算余数
    remainder = weighted_sum % 11
    
    # 返回对应的校验码
    return CHECK_CODE_MAP[remainder]


def _generate_birthday(min_age: int, max_age: int) -> str:
    """生成出生日期（YYYYMMDD）
    
    Args:
        min_age: 最小年龄
        max_age: 最大年龄
        
    Returns:
        8位出生日期字符串
    """
    today = datetime.now()
    
    # 计算年龄范围对应的日期范围
    max_birth_date = today - timedelta(days=min_age * 365)
    min_birth_date = today - timedelta(days=max_age * 365)
    
    # 在日期范围内随机选择
    days_range = (max_birth_date - min_birth_date).days
    random_days = random.randint(0, days_range)
    birth_date = min_birth_date + timedelta(days=random_days)
    
    return birth_date.strftime("%Y%m%d")


def _generate_sequence_code(gender: str = "random") -> str:
    """生成3位顺序码
    
    第17位：奇数为男性，偶数为女性
    
    Args:
        gender: 性别（"male", "female", "random"）
        
    Returns:
        3位顺序码
    """
    # 生成前2位
    seq = random.randint(0, 99)
    seq_str = f"{seq:02d}"
    
    # 生成第3位（性别位）
    if gender == "male":
        gender_digit = random.choice([1, 3, 5, 7, 9])
    elif gender == "female":
        gender_digit = random.choice([0, 2, 4, 6, 8])
    else:  # random
        gender_digit = random.randint(0, 9)
    
    return seq_str + str(gender_digit)


class IdCardStrategy(Strategy):
    """身份证号生成策略
    
    参数：
    - min_age: 最小年龄（默认 18）
    - max_age: 最大年龄（默认 65）
    - gender: 性别（"male", "female", "random"，默认 "random"）
    - region: 地区码（6位），None 表示随机
    
    示例：
        >>> strategy = IdCardStrategy(min_age=25, max_age=35, gender="male")
        >>> id_card = strategy.generate(StrategyContext(field_path="", field_schema={}))
        '110101199501011234'
    """
    
    def __init__(
        self,
        min_age: int = 18,
        max_age: int = 65,
        gender: str = "random",
        region: Optional[str] = None,
    ):
        # 参数校验
        if min_age < 0 or max_age > 150:
            raise StrategyError(
                f"IdCardStrategy: 年龄范围必须在 0-150 之间，当前 min_age={min_age}, max_age={max_age}"
            )
        
        if min_age > max_age:
            raise StrategyError(
                f"IdCardStrategy: min_age({min_age}) 不能大于 max_age({max_age})"
            )
        
        if gender not in ["male", "female", "random"]:
            raise StrategyError(
                f"IdCardStrategy: gender 必须是 'male', 'female' 或 'random'，当前为 {gender!r}"
            )
        
        # 校验地区码
        if region is not None:
            if len(region) != 6 or not region.isdigit():
                raise StrategyError(
                    f"IdCardStrategy: 地区码必须是6位数字，当前为 {region!r}"
                )
            if region not in _REGION_CODES:
                raise StrategyError(
                    f"IdCardStrategy: 无效的地区码 {region!r}"
                )
        
        self.min_age = min_age
        self.max_age = max_age
        self.gender = gender
        self.region = region
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成身份证号"""
        # 1. 地区码（6位）
        if self.region:
            region_code = self.region
        else:
            # 随机选择一个地区码
            region_code = random.choice(list(_REGION_CODES.keys()))
        
        # 2. 出生日期（8位）
        birthday = _generate_birthday(self.min_age, self.max_age)
        
        # 3. 顺序码（3位）
        sequence_code = _generate_sequence_code(self.gender)
        
        # 4. 组合前17位
        id17 = region_code + birthday + sequence_code
        
        # 5. 计算校验码
        check_code = _calculate_check_code(id17)
        
        # 6. 返回完整身份证号
        return id17 + check_code
    
    def values(self) -> Optional[List[str]]:
        """完整值域（身份证号空间巨大，返回 None）"""
        return None
    
    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = []
        
        # 最小年龄
        strategy = IdCardStrategy(min_age=0, max_age=0, gender="male", region="110101")
        boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        # 最大年龄
        strategy = IdCardStrategy(min_age=150, max_age=150, gender="female", region="110101")
        boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        return boundaries
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        classes = []
        
        # 男性
        male_strategy = IdCardStrategy(min_age=25, max_age=35, gender="male")
        classes.append([
            male_strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(3)
        ])
        
        # 女性
        female_strategy = IdCardStrategy(min_age=25, max_age=35, gender="female")
        classes.append([
            female_strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(3)
        ])
        
        # 不同年龄段
        age_ranges = [(0, 18), (18, 60), (60, 150)]
        for min_age, max_age in age_ranges:
            strategy = IdCardStrategy(min_age=min_age, max_age=max_age)
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
        
        return classes
    
    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "123456789012345",      # 15位（旧版，不推荐）
            "12345678901234567",    # 17位（位数错误）
            "1234567890123456789",  # 19位（位数错误）
            "123456789012345678",   # 正确位数但校验码错误
            "999999199001011234",   # 非法地区码
            "110000199002301234",   # 非法出生日期（2月30日）
            "110000199013011234",   # 非法出生日期（13月）
            "110000199000001234",   # 非法出生日期（00日）
            123456789012345678,     # 数字类型
            None,                   # None
            "",                     # 空字符串
            "ABCDEFGHJKLMNPQRST",  # 纯字母
        ]
