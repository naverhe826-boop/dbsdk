"""非法数据生成器

提供统一的非法数据生成能力，支持多种数据类型。
可独立使用，也可被策略的 invalid_values() 方法调用。
"""

from typing import Any, Dict, List, Optional


class InvalidDataGenerator:
    """非法数据生成器
    
    支持多种数据类型的非法数据生成，可作为独立工具使用，
    也可被策略的 invalid_values() 方法调用。
    
    使用示例：
        >>> InvalidDataGenerator.generate("email", count=3)
        ['not-an-email', '@domain.com', 'user@']
        
        >>> InvalidDataGenerator.generate("id_card", count=5)
        ['123456789012345', '123456789012345678', ...]
        
        >>> InvalidDataGenerator.add_template("phone", ["123", "abcdefghijk"])
    """
    
    # 预设模板（基于现有策略实现）
    _TEMPLATES: Dict[str, List[Any]] = {}
    
    @classmethod
    def generate(cls, data_type: str, count: int = 5, **kwargs) -> List[Any]:
        """生成指定类型的非法数据
        
        Args:
            data_type: 数据类型（见 get_all_types()）
            count: 生成数量，默认5
            **kwargs: 额外参数（如范围、格式等，用于智能生成）
            
        Returns:
            非法数据列表
            
        Raises:
            ValueError: 不支持的数据类型
            
        Examples:
            >>> InvalidDataGenerator.generate("email", count=3)
            ['not-an-email', '@domain.com', 'user@']
            
            >>> InvalidDataGenerator.generate("id_card", count=5)
            ['123456789012345', '123456789012345678', ...]
        """
        # 初始化模板（延迟加载）
        if not cls._TEMPLATES:
            cls._initialize_templates()
        
        # 检查数据类型
        if data_type not in cls._TEMPLATES:
            raise ValueError(
                f"不支持的数据类型 {data_type!r}，"
                f"可选值: {cls.get_all_types()}"
            )
        
        # 从模板中随机选择
        import random
        template = cls._TEMPLATES[data_type]
        
        if count >= len(template):
            # 如果请求数量大于模板数量，返回全部模板
            return template.copy()
        else:
            # 随机选择指定数量
            return random.sample(template, count)
    
    @classmethod
    def add_template(cls, data_type: str, values: List[Any]):
        """添加自定义非法数据模板
        
        Args:
            data_type: 数据类型
            values: 非法值列表
            
        Examples:
            >>> InvalidDataGenerator.add_template("phone", [
            ...     "123",           # 过短
            ...     "1234567890123456",  # 过长
            ...     "abcdefghijk",   # 非法字符
            ... ])
        """
        # 初始化模板（延迟加载）
        if not cls._TEMPLATES:
            cls._initialize_templates()
        
        # 添加或合并模板
        if data_type in cls._TEMPLATES:
            # 合并到现有模板（去重）
            existing = set(cls._TEMPLATES[data_type])
            for value in values:
                if value not in existing:
                    cls._TEMPLATES[data_type].append(value)
        else:
            # 创建新模板
            cls._TEMPLATES[data_type] = values.copy()
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """获取支持的所有数据类型
        
        Returns:
            数据类型列表
            
        Examples:
            >>> InvalidDataGenerator.get_all_types()
            ['email', 'password', 'ipv4', 'ipv6', 'mac', 'url', ...]
        """
        # 初始化模板（延迟加载）
        if not cls._TEMPLATES:
            cls._initialize_templates()
        
        return sorted(cls._TEMPLATES.keys())
    
    @classmethod
    def get_template(cls, data_type: str) -> List[Any]:
        """获取指定类型的预设模板
        
        Args:
            data_type: 数据类型
            
        Returns:
            非法值模板列表
            
        Raises:
            ValueError: 不支持的数据类型
            
        Examples:
            >>> InvalidDataGenerator.get_template("email")
            ['not-an-email', '@domain.com', 'user@', ...]
        """
        # 初始化模板（延迟加载）
        if not cls._TEMPLATES:
            cls._initialize_templates()
        
        if data_type not in cls._TEMPLATES:
            raise ValueError(
                f"不支持的数据类型 {data_type!r}，"
                f"可选值: {cls.get_all_types()}"
            )
        
        return cls._TEMPLATES[data_type].copy()
    
    @classmethod
    def _initialize_templates(cls):
        """从现有策略收集非法值模板
        
        初始化时从现有策略的 invalid_values() 方法收集模板，
        避免重复定义。
        """
        # ========== 账户相关 ==========
        
        # email - 从 EmailFakerStrategy 收集
        from ..strategies.value.string.email import EmailFakerStrategy
        cls._TEMPLATES["email"] = EmailFakerStrategy().invalid_values()
        
        # password - 从 PasswordStrategy 收集
        from ..strategies.value.string.password import PasswordStrategy
        cls._TEMPLATES["password"] = PasswordStrategy().invalid_values()
        
        # ========== 网络相关 ==========
        
        # ipv4 - 从 IPv4Strategy 收集
        from ..strategies.value.network.ipv4 import IPv4Strategy
        cls._TEMPLATES["ipv4"] = IPv4Strategy().invalid_values()
        
        # ipv6 - 从 IPv6Strategy 收集
        from ..strategies.value.network.ipv6 import IPv6Strategy
        cls._TEMPLATES["ipv6"] = IPv6Strategy().invalid_values()
        
        # mac - 从 MACStrategy 收集
        from ..strategies.value.network.mac import MACStrategy
        cls._TEMPLATES["mac"] = MACStrategy().invalid_values()
        
        # url - 从 URLStrategy 收集
        from ..strategies.value.network.url import URLStrategy
        cls._TEMPLATES["url"] = URLStrategy().invalid_values()
        
        # domain - 从 DomainStrategy 收集
        from ..strategies.value.network.domain import DomainStrategy
        cls._TEMPLATES["domain"] = DomainStrategy().invalid_values()
        
        # hostname - 从 HostnameStrategy 收集
        from ..strategies.value.network.hostname import HostnameStrategy
        cls._TEMPLATES["hostname"] = HostnameStrategy().invalid_values()
        
        # cidr - 从 CIDRStrategy 收集
        from ..strategies.value.network.cidr import CIDRStrategy
        cls._TEMPLATES["cidr"] = CIDRStrategy().invalid_values()
        
        # ip_range - 从 IPRangeStrategy 收集
        from ..strategies.value.network.ip_range import IPRangeStrategy
        cls._TEMPLATES["ip_range"] = IPRangeStrategy().invalid_values()
        
        # ========== 其他类型 ==========
        
        # string - 从 RandomStringStrategy 收集
        from ..strategies.value.string.random_string import RandomStringStrategy
        cls._TEMPLATES["string"] = RandomStringStrategy().invalid_values()
        
        # datetime - 从 DateTimeStrategy 收集
        from ..strategies.value.datetime.datetime import DateTimeStrategy
        cls._TEMPLATES["datetime"] = DateTimeStrategy().invalid_values()
        
        # ========== 新增：账户类（已实现） ==========
        
        # id_card - 从 IdCardStrategy 收集
        from ..strategies.value.string.id_card import IdCardStrategy
        cls._TEMPLATES["id_card"] = IdCardStrategy().invalid_values()
        
        # bank_card - 从 BankCardStrategy 收集
        from ..strategies.value.string.bank_card import BankCardStrategy
        cls._TEMPLATES["bank_card"] = BankCardStrategy().invalid_values()
        
        # phone - 从 PhoneStrategy 收集
        from ..strategies.value.string.phone import PhoneStrategy
        cls._TEMPLATES["phone"] = PhoneStrategy().invalid_values()
        
        # username - 从 UsernameStrategy 收集
        from ..strategies.value.string.username import UsernameStrategy
        cls._TEMPLATES["username"] = UsernameStrategy().invalid_values()
        
        # uuid - UUID非法值
        cls._TEMPLATES["uuid"] = [
            "not-a-uuid",           # 格式错误
            "12345678-1234-1234-1234-12345678901",   # 位数不对
            "12345678-1234-1234-1234-12345678901234", # 位数不对
            "gggggggg-1234-1234-1234-123456789012",  # 非法字符
            12345,                  # 数字类型
            None,                   # None
            "",                     # 空字符串
        ]
        
        # integer - 整数非法值
        cls._TEMPLATES["integer"] = [
            "not-an-int",           # 字符串
            3.14,                   # 浮点数
            None,                   # None
            [],                     # 列表
            {},                     # 对象
        ]
