"""用户名生成策略

支持生成符合规则的系统用户名：
- 支持长度配置（默认6-20位）
- 支持字符集配置（字母、数字、下划线、点等）
- 支持保留字过滤（如 admin、root 等）
"""

import random
import string
from typing import Any, List, Optional, Set

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 默认保留字列表
DEFAULT_RESERVED_WORDS = [
    "admin", "root", "system", "test", "guest",
    "administrator", "user", "demo", "null", "undefined",
    "administrator", "superuser", "manager", "operator",
]


class UsernameStrategy(Strategy):
    """用户名生成策略
    
    参数：
    - min_length: 最小长度（默认 6）
    - max_length: 最大长度（默认 20）
    - charset: 字符集（"alphanumeric", "alphanumeric_underscore", 
                       "alphanumeric_dot", "alphanumeric_dash"，
                       默认 "alphanumeric_underscore"）
    - reserved_words: 保留字列表（默认使用 DEFAULT_RESERVED_WORDS）
    - allow_uppercase: 是否允许大写字母（默认 True）
    
    示例：
        >>> strategy = UsernameStrategy(min_length=8, max_length=16)
        >>> username = strategy.generate(StrategyContext(field_path="", field_schema={}))
        'user_12345'
    """
    
    CHARSET_MAP = {
        "alphanumeric": string.ascii_lowercase + string.digits,
        "alphanumeric_underscore": string.ascii_lowercase + string.digits + "_",
        "alphanumeric_dot": string.ascii_lowercase + string.digits + ".",
        "alphanumeric_dash": string.ascii_lowercase + string.digits + "-",
    }
    
    def __init__(
        self,
        min_length: int = 6,
        max_length: int = 20,
        charset: str = "alphanumeric_underscore",
        reserved_words: Optional[List[str]] = None,
        allow_uppercase: bool = True,
    ):
        # 参数校验
        if min_length < 1 or max_length > 50:
            raise StrategyError(
                f"UsernameStrategy: 长度范围必须在 1-50 之间，"
                f"当前 min_length={min_length}, max_length={max_length}"
            )
        
        if min_length > max_length:
            raise StrategyError(
                f"UsernameStrategy: min_length({min_length}) 不能大于 max_length({max_length})"
            )
        
        if charset not in self.CHARSET_MAP:
            raise StrategyError(
                f"UsernameStrategy: 不支持的字符集 {charset!r}，"
                f"可选值: {list(self.CHARSET_MAP.keys())}"
            )
        
        self.min_length = min_length
        self.max_length = max_length
        self.charset_name = charset
        self.charset = self.CHARSET_MAP[charset]
        if allow_uppercase:
            self.charset += string.ascii_uppercase
        self.reserved_words: Set[str] = set(reserved_words or DEFAULT_RESERVED_WORDS)
        self.allow_uppercase = allow_uppercase
        
        # 特殊字符（非字母数字开头）
        self._special_chars = set("_-.") & set(self.charset)
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成用户名"""
        # 最多尝试100次，避免保留字冲突导致无限循环
        max_attempts = 100
        
        for _ in range(max_attempts):
            # 1. 随机选择长度
            length = random.randint(self.min_length, self.max_length)
            
            # 2. 生成用户名
            username = self._generate_username(length)
            
            # 3. 检查保留字
            if username.lower() not in {w.lower() for w in self.reserved_words}:
                return username
        
        # 如果所有尝试都失败，生成一个带随机后缀的用户名
        base = self._generate_username(self.min_length)
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{base}{suffix}"
    
    def _generate_username(self, length: int) -> str:
        """生成指定长度的用户名
        
        Args:
            length: 用户名长度
            
        Returns:
            用户名字符串
        """
        # 确保首字符不是特殊字符
        first_char = random.choice(
            string.ascii_lowercase + string.ascii_uppercase + string.digits
            if self.allow_uppercase else string.ascii_lowercase + string.digits
        )
        
        # 剩余字符
        remaining_length = length - 1
        if remaining_length > 0:
            remaining_chars = ''.join(random.choices(self.charset, k=remaining_length))
            return first_char + remaining_chars
        
        return first_char
    
    def values(self) -> Optional[List[str]]:
        """完整值域（用户名空间巨大，返回 None）"""
        return None
    
    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = []
        
        # 最小长度
        strategy = UsernameStrategy(min_length=self.min_length, max_length=self.min_length)
        boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        # 最大长度
        strategy = UsernameStrategy(min_length=self.max_length, max_length=self.max_length)
        boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        
        return boundaries
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        classes = []
        
        # 纯字母
        strategy = UsernameStrategy(charset="alphanumeric")
        classes.append([
            strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(2)
        ])
        
        # 字母数字混合
        strategy = UsernameStrategy(charset="alphanumeric_underscore")
        classes.append([
            strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(2)
        ])
        
        # 包含特殊字符
        strategy = UsernameStrategy(charset="alphanumeric_dot")
        classes.append([
            strategy.generate(StrategyContext(field_path="", field_schema={}))
            for _ in range(2)
        ])
        
        return classes
    
    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        return [
            "",                     # 空字符串
            "ab",                   # 过短（< 6位）
            "a" * 21,               # 过长（> 20位）
            "user@name",            # 包含非法字符 @
            "user name",            # 包含空格
            "admin",                # 保留字
            "root",                 # 保留字
            "system",               # 保留字
            12345,                  # 数字类型
            None,                   # None
        ]
