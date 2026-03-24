"""认证令牌生成策略"""

import base64
import json
import random
import string
from typing import Any, Dict, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


class TokenStrategy(Strategy):
    """认证令牌生成策略，支持多种 token 类型
    
    支持的 token 类型：
    - api_key: API 密钥，固定长度随机字符串（默认32位，无前缀）
    - openai_key: OpenAI API Key，51字符（sk- + 48位字母数字）
    - jwt: JWT 令牌，三段式 Base64 编码格式
    - bearer: Bearer 令牌，可选 "Bearer " 前缀
    - session: 会话令牌，普通随机字符串（默认类型）
    - access: 访问令牌，类似 api_key
    - refresh: 刷新令牌，更长生命周期
    """
    
    TOKEN_TYPES = ("api_key", "openai_key", "jwt", "bearer", "session", "access", "refresh")
    
    # 默认长度配置
    DEFAULT_LENGTHS = {
        "api_key": 32,
        "openai_key": 48,  # OpenAI API Key: sk- + 48位 = 51字符
        "jwt": 32,  # 每段长度
        "bearer": 32,
        "session": 32,
        "access": 32,
        "refresh": 64,
    }
    
    # 默认前缀
    DEFAULT_PREFIXES = {
        "api_key": "",
        "openai_key": "sk-",
        "jwt": "",
        "bearer": "Bearer ",
        "session": "sess_",
        "access": "acc_",
        "refresh": "ref_",
    }
    
    def __init__(
        self,
        token_type: str = "session",
        length: Optional[int] = None,
        charset: Optional[str] = None,
        prefix: Optional[str] = None,
        include_prefix: Optional[bool] = None,
        algorithm: str = "HS256",
    ):
        """
        初始化 TokenStrategy
        
        :param token_type: 令牌类型（api_key/openai_key/jwt/bearer/session/access/refresh）
        :param length: 字符串长度，None 时使用类型默认长度
        :param charset: 自定义字符集，None 时使用字母数字
        :param prefix: 自定义前缀，None 时使用类型默认前缀
        :param include_prefix: 是否包含前缀（仅 bearer 类型有效）
        :param algorithm: JWT 算法（仅 jwt 类型有效）
        """
        # 参数校验：token_type
        if token_type not in self.TOKEN_TYPES:
            raise StrategyError(
                f"TokenStrategy: token_type({token_type}) 必须是 "
                f"{'/'.join(self.TOKEN_TYPES)} 之一"
            )
        
        self.token_type = token_type
        self.algorithm = algorithm
        
        # 设置长度
        self.length = length if length is not None else self.DEFAULT_LENGTHS.get(token_type, 32)
        
        # 参数校验：length
        if self.length < 8:
            raise StrategyError(f"TokenStrategy: length({self.length}) 不能小于 8")
        if self.length > 256:
            raise StrategyError(f"TokenStrategy: length({self.length}) 不能大于 256")
        
        # 设置字符集
        self.charset = charset if charset is not None else string.ascii_letters + string.digits
        
        # 设置前缀
        if prefix is not None:
            self.prefix = prefix
            self.include_prefix = True
        else:
            self.prefix = self.DEFAULT_PREFIXES.get(token_type, "")
            # bearer 类型：include_prefix 默认 True
            if include_prefix is not None:
                self.include_prefix = include_prefix
            else:
                self.include_prefix = True if token_type == "bearer" else bool(self.prefix)
    
    def generate(self, ctx: StrategyContext) -> str:
        """生成认证令牌"""
        if self.token_type == "api_key":
            return self._generate_api_key()
        elif self.token_type == "openai_key":
            return self._generate_openai_key()
        elif self.token_type == "jwt":
            return self._generate_jwt()
        elif self.token_type == "bearer":
            return self._generate_bearer()
        elif self.token_type == "session":
            return self._generate_session()
        elif self.token_type == "access":
            return self._generate_access()
        elif self.token_type == "refresh":
            return self._generate_refresh()
        else:
            # 兜底：生成随机字符串
            return self._generate_random()
    
    def _generate_random(self, length: Optional[int] = None) -> str:
        """生成随机字符串"""
        actual_length = length if length is not None else self.length
        return ''.join(random.choices(self.charset, k=actual_length))
    
    def _generate_api_key(self) -> str:
        """生成 API Key"""
        token = self._generate_random()
        if self.include_prefix and self.prefix:
            return f"{self.prefix}{token}"
        return token
    
    def _generate_openai_key(self) -> str:
        """生成 OpenAI API Key
        
        格式：sk- + 48位字母数字 = 51字符
        OpenAI API Key 特征：
        - 以 sk- 开头
        - 总长度 51 字符
        - 字符集：字母数字（大小写+数字）
        """
        token = self._generate_random()
        # openai_key 默认始终包含前缀
        return f"{self.prefix}{token}"
    
    def _generate_jwt(self) -> str:
        """生成 JWT Token（三段式 Base64 编码）
        
        格式：header.payload.signature
        每段都是 Base64 编码的 JSON 对象
        """
        # 生成 header
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        header_b64 = self._encode_base64(json.dumps(header))
        
        # 生成 payload
        payload = {
            "sub": self._generate_random(16),
            "iat": random.randint(1000000000, 9999999999),
            "exp": random.randint(1000000000, 9999999999),
            "jti": self._generate_random(16),
        }
        payload_b64 = self._encode_base64(json.dumps(payload))
        
        # 生成 signature（模拟签名，不是真实签名）
        signature_content = f"{header_b64}.{payload_b64}"
        signature_b64 = self._encode_base64(signature_content)[:self.length]
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def _generate_bearer(self) -> str:
        """生成 Bearer Token"""
        token = self._generate_random()
        if self.include_prefix:
            return f"{self.prefix}{token}"
        return token
    
    def _generate_session(self) -> str:
        """生成 Session Token"""
        token = self._generate_random()
        if self.include_prefix and self.prefix:
            return f"{self.prefix}{token}"
        return token
    
    def _generate_access(self) -> str:
        """生成 Access Token"""
        token = self._generate_random()
        if self.include_prefix and self.prefix:
            return f"{self.prefix}{token}"
        return token
    
    def _generate_refresh(self) -> str:
        """生成 Refresh Token"""
        token = self._generate_random()
        if self.include_prefix and self.prefix:
            return f"{self.prefix}{token}"
        return token
    
    @staticmethod
    def _encode_base64(data: str) -> str:
        """Base64 编码（URL 安全，无填充）"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        encoded = base64.urlsafe_b64encode(data).decode('utf-8')
        # 移除填充字符
        return encoded.rstrip('=')
    
    def boundary_values(self) -> Optional[List[str]]:
        """返回边界值
        
        边界情况：
        - api_key: 最小长度8，最大长度128
        - jwt: 无签名JWT、空payload
        - bearer: 有/无前缀
        - session/access/refresh: 短令牌、长令牌
        """
        if self.token_type == "jwt":
            # JWT 边界：最短和最长
            short_jwt = self._generate_jwt()
            original_length = self.length
            self.length = 128
            long_jwt = self._generate_jwt()
            self.length = original_length
            return [short_jwt, long_jwt]
        elif self.token_type == "bearer":
            # Bearer 边界：有前缀、无前缀
            with_prefix = self._generate_bearer()
            original_include = self.include_prefix
            self.include_prefix = False
            without_prefix = self._generate_bearer()
            self.include_prefix = original_include
            return [with_prefix, without_prefix]
        else:
            # 其他类型：最小和最大长度
            original_length = self.length
            self.length = 8
            min_token = self.generate(StrategyContext(field_path="", field_schema={}))
            self.length = 128
            max_token = self.generate(StrategyContext(field_path="", field_schema={}))
            self.length = original_length
            return [min_token, max_token]
    
    def equivalence_classes(self) -> Optional[List[List[str]]]:
        """返回等价类
        
        按 token 类型分类：
        - 每种类型生成 3 个样本
        """
        samples = []
        for _ in range(3):
            samples.append(self.generate(StrategyContext(field_path="", field_schema={})))
        return [samples]
    
    def invalid_values(self) -> Optional[List[Any]]:
        """返回非法值"""
        invalid = [
            "",                    # 空字符串
            "short",               # 太短
            12345,                 # 非字符串
            None,                  # None值
        ]
        
        # 类型特定的非法值
        if self.token_type == "bearer":
            invalid.append("Bearer ")  # 空Bearer令牌
        elif self.token_type == "jwt":
            invalid.append("invalid.jwt.format")  # 无效JWT格式
            invalid.append("not-a-jwt")  # 不是JWT格式
        
        return invalid
    
    def values(self) -> Optional[List[str]]:
        """值域：token 组合可能非常多，返回 None 表示不可枚举"""
        total_combinations = len(self.charset) ** self.length
        if total_combinations > 1000:
            return None  # 不可枚举
        # 对于小规模情况，返回 None（token 通常很长）
        return None
