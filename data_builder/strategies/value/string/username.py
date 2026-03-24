"""用户名生成策略

支持生成符合规则的系统用户名：
- 支持长度配置（默认6-20位）
- 支持字符集配置（字母、数字、下划线、点等）
- 支持保留字过滤（如 admin、root 等）
- 支持中文姓名、英文姓名、昵称等生成模式
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

# 常见中文姓氏（百家姓前100）
COMMON_SURNAMES = [
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
    "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
    "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎",
    "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜",
    "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆",
    "郝", "孔", "白", "崔", "康", "毛", "邱", "秦", "江", "史",
    "顾", "侯", "邵", "孟", "龙", "万", "段", "漕", "钱", "汤",
    "尹", "黎", "易", "常", "武", "乔", "贺", "赖", "龚", "文",
]

# 昵称特征词
NICKNAME_PREFIXES = ["小", "老", "大", "阿"]
NICKNAME_SUFFIXES = ["哥", "姐", "弟", "妹", "爷", "叔", "姨"]

# 常见名字用字（单字）
COMMON_NAME_CHARS = [
    "伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
    "勇", "艳", "杰", "涛", "明", "超", "秀", "霞", "平", "刚",
    "桂", "英", "华", "建", "文", "玲", "斌", "波", "辉", "鹏",
    "俊", "浩", "宇", "轩", "博", "然", "飞", "峰", "龙", "翔",
    "婷", "欣", "怡", "悦", "佳", "慧", "琳", "璐", "雪", "颖",
]


class UsernameStrategy(Strategy):
    """用户名生成策略
    
    参数：
    - style: 生成模式（"random", "chinese_name", "english_name", "nickname"，默认 "random"）
    - min_length: 最小长度（默认 6，仅 random 模式）
    - max_length: 最大长度（默认 20，仅 random 模式）
    - charset: 字符集（仅 random 模式，"alphanumeric", "alphanumeric_underscore", 
                       "alphanumeric_dot", "alphanumeric_dash"，
                       默认 "alphanumeric_underscore"）
    - reserved_words: 保留字列表（默认使用 DEFAULT_RESERVED_WORDS）
    - allow_uppercase: 是否允许大写字母（默认 True，仅 random 模式）
    - gender: 性别过滤（"male", "female", "random"，默认 "random"，仅姓名模式）
    - suffix_type: 昵称后缀类型（"number", "char", "none"，默认 "none"，仅 nickname 模式）
    
    示例：
        >>> # 随机字符
        >>> strategy = UsernameStrategy(style="random", min_length=8, max_length=16)
        >>> username = strategy.generate(StrategyContext(field_path="", field_schema={}))
        'user_12345'
        
        >>> # 中文姓名
        >>> strategy = UsernameStrategy(style="chinese_name")
        >>> name = strategy.generate(StrategyContext(field_path="", field_schema={}))
        '张伟'
        
        >>> # 英文姓名
        >>> strategy = UsernameStrategy(style="english_name")
        >>> name = strategy.generate(StrategyContext(field_path="", field_schema={}))
        'John Smith'
        
        >>> # 昵称
        >>> strategy = UsernameStrategy(style="nickname", suffix_type="number")
        >>> nick = strategy.generate(StrategyContext(field_path="", field_schema={}))
        '小明123'
    """
    
    CHARSET_MAP = {
        "alphanumeric": string.ascii_lowercase + string.digits,
        "alphanumeric_underscore": string.ascii_lowercase + string.digits + "_",
        "alphanumeric_dot": string.ascii_lowercase + string.digits + ".",
        "alphanumeric_dash": string.ascii_lowercase + string.digits + "-",
    }
    
    # 支持的生成模式
    STYLES = {"random", "chinese_name", "english_name", "nickname"}
    GENDERS = {"male", "female", "random"}
    SUFFIX_TYPES = {"number", "char", "none"}
    
    def __init__(
        self,
        min_length: int = 6,
        max_length: int = 20,
        charset: str = "alphanumeric_underscore",
        reserved_words: Optional[List[str]] = None,
        allow_uppercase: bool = True,
        style: str = "random",
        gender: str = "random",
        suffix_type: str = "none",
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
        
        if style not in self.STYLES:
            raise StrategyError(
                f"UsernameStrategy: 不支持的生成模式 {style!r}，"
                f"可选值: {list(self.STYLES)}"
            )
        
        if gender not in self.GENDERS:
            raise StrategyError(
                f"UsernameStrategy: 不支持的性别 {gender!r}，"
                f"可选值: {list(self.GENDERS)}"
            )
        
        if suffix_type not in self.SUFFIX_TYPES:
            raise StrategyError(
                f"UsernameStrategy: 不支持的后缀类型 {suffix_type!r}，"
                f"可选值: {list(self.SUFFIX_TYPES)}"
            )
        
        self.min_length = min_length
        self.max_length = max_length
        self.charset_name = charset
        self.charset = self.CHARSET_MAP[charset]
        if allow_uppercase:
            self.charset += string.ascii_uppercase
        self.reserved_words: Set[str] = set(reserved_words or DEFAULT_RESERVED_WORDS)
        self.allow_uppercase = allow_uppercase
        self.style = style
        self.gender = gender
        self.suffix_type = suffix_type
        
        # 特殊字符（非字母数字开头）
        self._special_chars = set("_-.") & set(self.charset)
        
        # Faker 实例延迟初始化
        self._faker_zh = None
        self._faker_en = None
    
    def _get_faker_zh(self):
        """获取中文 Faker 实例（延迟初始化）"""
        if self._faker_zh is None:
            from faker import Faker
            self._faker_zh = Faker("zh_CN")
        return self._faker_zh
    
    def _get_faker_en(self):
        """获取英文 Faker 实例（延迟初始化）"""
        if self._faker_en is None:
            from faker import Faker
            self._faker_en = Faker("en_US")
        return self._faker_en
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成用户名"""
        # 根据模式选择生成方法
        if self.style == "random":
            return self._generate_random()
        elif self.style == "chinese_name":
            return self._generate_chinese_name()
        elif self.style == "english_name":
            return self._generate_english_name()
        elif self.style == "nickname":
            return self._generate_nickname()
        else:
            # 兜底
            return self._generate_random()
    
    def _generate_random(self) -> str:
        """生成随机字符用户名"""
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
    
    def _generate_chinese_name(self) -> str:
        """生成中文姓名
        
        使用 Faker 库生成真实中文姓名，支持性别过滤
        """
        faker = self._get_faker_zh()
        
        max_attempts = 100
        for _ in range(max_attempts):
            # 根据性别选择生成方式
            if self.gender == "male":
                name = faker.name_male()
            elif self.gender == "female":
                name = faker.name_female()
            else:
                name = faker.name()
            
            # 检查保留字
            if name not in self.reserved_words:
                return name
        
        # 备用方案：自定义生成
        surname = random.choice(COMMON_SURNAMES)
        name_char = random.choice(COMMON_NAME_CHARS)
        # 随机决定单字名或双字名
        if random.random() < 0.5:
            return f"{surname}{name_char}"
        else:
            name_char2 = random.choice(COMMON_NAME_CHARS)
            return f"{surname}{name_char}{name_char2}"
    
    def _generate_english_name(self) -> str:
        """生成英文姓名
        
        使用 Faker 库生成真实英文姓名，支持性别过滤
        """
        faker = self._get_faker_en()
        
        max_attempts = 100
        for _ in range(max_attempts):
            # 根据性别选择生成方式
            if self.gender == "male":
                name = faker.name_male()
            elif self.gender == "female":
                name = faker.name_female()
            else:
                name = faker.name()
            
            # 检查保留字
            if name.lower() not in {w.lower() for w in self.reserved_words}:
                return name
        
        # 备用方案：使用常见名字组合
        first_names = ["John", "Michael", "David", "James", "Robert",
                       "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                      "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_nickname(self) -> str:
        """生成中文昵称
        
        规则：特征词 + 姓氏/名字 + 可选后缀
        示例：小李、老王、张三丰、阿明123
        """
        max_attempts = 100
        
        for _ in range(max_attempts):
            # 选择生成方式
            pattern = random.choice(["prefix_surname", "prefix_name", "surname_suffix"])
            
            if pattern == "prefix_surname":
                # 特征词 + 姓氏（如：小李、老王）
                prefix = random.choice(NICKNAME_PREFIXES)
                surname = random.choice(COMMON_SURNAMES)
                nickname = f"{prefix}{surname}"
            elif pattern == "prefix_name":
                # 特征词 + 名字（如：小明、阿龙）
                prefix = random.choice(NICKNAME_PREFIXES)
                name_char = random.choice(COMMON_NAME_CHARS)
                nickname = f"{prefix}{name_char}"
            else:
                # 姓氏 + 后缀（如：李哥、王姐）
                surname = random.choice(COMMON_SURNAMES)
                suffix = random.choice(NICKNAME_SUFFIXES)
                nickname = f"{surname}{suffix}"
            
            # 添加可选后缀
            if self.suffix_type == "number":
                suffix = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
                nickname = f"{nickname}{suffix}"
            elif self.suffix_type == "char":
                suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(2, 3)))
                nickname = f"{nickname}{suffix}"
            
            # 检查保留字
            if nickname not in self.reserved_words:
                return nickname
        
        # 备用方案
        prefix = random.choice(NICKNAME_PREFIXES)
        surname = random.choice(COMMON_SURNAMES)
        suffix = ''.join(random.choices(string.digits, k=3))
        return f"{prefix}{surname}{suffix}"
    
    def values(self) -> Optional[List[str]]:
        """完整值域（用户名空间巨大，返回 None）"""
        return None
    
    def boundary_values(self) -> Optional[List[str]]:
        """边界值"""
        boundaries = []
        
        if self.style == "random":
            # 最小长度
            strategy = UsernameStrategy(
                min_length=self.min_length, 
                max_length=self.min_length,
                style="random"
            )
            boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
            
            # 最大长度
            strategy = UsernameStrategy(
                min_length=self.max_length, 
                max_length=self.max_length,
                style="random"
            )
            boundaries.append(strategy.generate(StrategyContext(field_path="", field_schema={})))
        else:
            # 姓名和昵称模式：各生成一个示例
            boundaries.append(self.generate(StrategyContext(field_path="", field_schema={})))
        
        return boundaries
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """等价类分组"""
        classes = []
        
        if self.style == "random":
            # 纯字母
            strategy = UsernameStrategy(charset="alphanumeric", style="random")
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
            
            # 字母数字混合
            strategy = UsernameStrategy(charset="alphanumeric_underscore", style="random")
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
            
            # 包含特殊字符
            strategy = UsernameStrategy(charset="alphanumeric_dot", style="random")
            classes.append([
                strategy.generate(StrategyContext(field_path="", field_schema={}))
                for _ in range(2)
            ])
        else:
            # 姓名和昵称模式：按性别分组
            if self.style in ("chinese_name", "english_name"):
                male_strategy = UsernameStrategy(style=self.style, gender="male")
                female_strategy = UsernameStrategy(style=self.style, gender="female")
                classes.append([
                    male_strategy.generate(StrategyContext(field_path="", field_schema={}))
                    for _ in range(2)
                ])
                classes.append([
                    female_strategy.generate(StrategyContext(field_path="", field_schema={}))
                    for _ in range(2)
                ])
            else:
                # 昵称按后缀类型分组
                for suffix_type in ["none", "number", "char"]:
                    strategy = UsernameStrategy(style="nickname", suffix_type=suffix_type)
                    classes.append([
                        strategy.generate(StrategyContext(field_path="", field_schema={}))
                        for _ in range(2)
                    ])
        
        return classes
    
    def invalid_values(self) -> Optional[List[Any]]:
        """非法值"""
        if self.style == "random":
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
        elif self.style in ("chinese_name", "english_name"):
            return [
                "",                     # 空字符串
                "123",                  # 纯数字
                "admin",                # 保留字
                12345,                  # 数字类型
                None,                   # None
            ]
        else:  # nickname
            return [
                "",                     # 空字符串
                "123",                  # 纯数字
                "admin",                # 保留字
                12345,                  # 数字类型
                None,                   # None
            ]
