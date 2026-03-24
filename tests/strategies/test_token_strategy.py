"""TokenStrategy 测试用例"""

import pytest
from data_builder import DataBuilder, token
from data_builder.strategies.value.string.token import TokenStrategy
from data_builder.strategies.basic import StrategyContext
from data_builder.exceptions import StrategyError


class TestTokenStrategy:
    """TokenStrategy 测试"""
    
    def test_init_default(self):
        """测试默认初始化"""
        strategy = TokenStrategy()
        assert strategy.token_type == "session"
        assert strategy.length == 32
        assert strategy.include_prefix is True
    
    def test_init_with_type(self):
        """测试指定 token_type"""
        for token_type in TokenStrategy.TOKEN_TYPES:
            strategy = TokenStrategy(token_type=token_type)
            assert strategy.token_type == token_type
    
    def test_init_invalid_type(self):
        """测试无效 token_type"""
        with pytest.raises(StrategyError, match="token_type"):
            TokenStrategy(token_type="invalid_type")
    
    def test_init_invalid_length_too_small(self):
        """测试长度过小"""
        with pytest.raises(StrategyError, match="length.*不能小于 8"):
            TokenStrategy(length=5)
    
    def test_init_invalid_length_too_large(self):
        """测试长度过大"""
        with pytest.raises(StrategyError, match="length.*不能大于 256"):
            TokenStrategy(length=300)
    
    def test_generate_api_key(self):
        """测试 API Key 生成"""
        strategy = TokenStrategy(token_type="api_key", length=32)
        ctx = StrategyContext(field_path="api_key", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert len(result) == 32
            assert result.isalnum()
    
    def test_generate_api_key_with_prefix(self):
        """测试 API Key 生成（带前缀 sk-）"""
        strategy = TokenStrategy(token_type="api_key", length=32, prefix="sk-")
        ctx = StrategyContext(field_path="api_key", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert result.startswith("sk-")
            assert len(result) == 35  # sk- (3) + 32
    
    def test_generate_openai_key(self):
        """测试 OpenAI API Key 生成"""
        strategy = TokenStrategy(token_type="openai_key")
        ctx = StrategyContext(field_path="openai_key", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert result.startswith("sk-")
            assert len(result) == 51  # sk- (3) + 48
    
    def test_generate_jwt(self):
        """测试 JWT Token 生成"""
        strategy = TokenStrategy(token_type="jwt", length=32)
        ctx = StrategyContext(field_path="jwt", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            # JWT 格式：header.payload.signature
            parts = result.split(".")
            assert len(parts) == 3
            # 每段都应该是 Base64 编码的字符串
            for part in parts:
                assert len(part) > 0
    
    def test_generate_bearer_with_prefix(self):
        """测试 Bearer Token 生成（带前缀）"""
        strategy = TokenStrategy(token_type="bearer", include_prefix=True)
        ctx = StrategyContext(field_path="bearer", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert result.startswith("Bearer ")
            assert len(result) > 7  # 前缀 + token
    
    def test_generate_bearer_without_prefix(self):
        """测试 Bearer Token 生成（不带前缀）"""
        strategy = TokenStrategy(token_type="bearer", include_prefix=False)
        ctx = StrategyContext(field_path="bearer", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert not result.startswith("Bearer ")
    
    def test_generate_session(self):
        """测试 Session Token 生成"""
        strategy = TokenStrategy(token_type="session", length=32)
        ctx = StrategyContext(field_path="session", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert len(result) >= 32  # 可能有前缀
    
    def test_generate_access(self):
        """测试 Access Token 生成"""
        strategy = TokenStrategy(token_type="access", length=32)
        ctx = StrategyContext(field_path="access", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert len(result) >= 32  # 可能有前缀
    
    def test_generate_refresh(self):
        """测试 Refresh Token 生成"""
        strategy = TokenStrategy(token_type="refresh", length=64)
        ctx = StrategyContext(field_path="refresh", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert len(result) >= 64  # 可能有前缀
    
    def test_custom_charset(self):
        """测试自定义字符集"""
        strategy = TokenStrategy(token_type="api_key", length=16, charset="0123456789", include_prefix=False)
        ctx = StrategyContext(field_path="api_key", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert result.isdigit()
            assert len(result) == 16
    
    def test_custom_prefix(self):
        """测试自定义前缀"""
        strategy = TokenStrategy(token_type="session", prefix="CUSTOM_", length=32)
        ctx = StrategyContext(field_path="session", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert result.startswith("CUSTOM_")
    
    def test_boundary_values(self):
        """测试边界值"""
        strategy = TokenStrategy(token_type="api_key")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 2  # 最小和最大
        for value in boundary:
            assert isinstance(value, str)
    
    def test_boundary_values_jwt(self):
        """测试 JWT 边界值"""
        strategy = TokenStrategy(token_type="jwt")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 2
        for value in boundary:
            # JWT 格式验证
            assert len(value.split(".")) == 3
    
    def test_boundary_values_bearer(self):
        """测试 Bearer 边界值"""
        strategy = TokenStrategy(token_type="bearer")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 2
        # 一个有前缀，一个没有
        has_prefix = any(v.startswith("Bearer ") for v in boundary)
        assert has_prefix
    
    def test_equivalence_classes(self):
        """测试等价类"""
        strategy = TokenStrategy(token_type="api_key")
        classes = strategy.equivalence_classes()
        
        assert isinstance(classes, list)
        assert len(classes) > 0
        for cls in classes:
            assert isinstance(cls, list)
            assert len(cls) > 0
    
    def test_invalid_values(self):
        """测试非法值"""
        strategy = TokenStrategy(token_type="api_key")
        invalid = strategy.invalid_values()
        
        assert isinstance(invalid, list)
        assert len(invalid) > 0
        assert "" in invalid
        assert None in invalid
        assert 12345 in invalid  # 非字符串
    
    def test_invalid_values_jwt(self):
        """测试 JWT 非法值"""
        strategy = TokenStrategy(token_type="jwt")
        invalid = strategy.invalid_values()
        
        assert "invalid.jwt.format" in invalid
        assert "not-a-jwt" in invalid
    
    def test_invalid_values_bearer(self):
        """测试 Bearer 非法值"""
        strategy = TokenStrategy(token_type="bearer")
        invalid = strategy.invalid_values()
        
        assert "Bearer " in invalid  # 空 Bearer 令牌
    
    def test_values_returns_none(self):
        """测试 values() 返回 None（不可枚举）"""
        strategy = TokenStrategy(token_type="api_key")
        assert strategy.values() is None


class TestTokenFactory:
    """token() 工厂函数测试"""
    
    def test_factory_default(self):
        """测试工厂函数默认参数"""
        strategy = token()
        assert isinstance(strategy, TokenStrategy)
        assert strategy.token_type == "session"
    
    def test_factory_with_type(self):
        """测试工厂函数指定类型"""
        strategy = token(token_type="jwt")
        assert isinstance(strategy, TokenStrategy)
        assert strategy.token_type == "jwt"
    
    def test_factory_with_length(self):
        """测试工厂函数指定长度"""
        strategy = token(length=64)
        assert strategy.length == 64
    
    def test_factory_with_prefix(self):
        """测试工厂函数指定前缀"""
        strategy = token(prefix="TEST_")
        assert strategy.prefix == "TEST_"
        assert strategy.include_prefix is True


class TestDataBuilderIntegration:
    """DataBuilder 集成测试"""
    
    def test_databuilder_with_api_key(self):
        """测试 DataBuilder 集成 API Key"""
        schema = {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
            },
            "required": ["api_key"]
        }
        
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "api_key", "strategy": {"type": "token", "token_type": "api_key", "length": 32}}
            ]
        })
        builder = DataBuilder(schema, config)
        
        data = builder.build(count=5)
        assert isinstance(data, list)
        assert len(data) == 5
        
        for item in data:
            assert "api_key" in item
            assert len(item["api_key"]) == 32
            assert item["api_key"].isalnum()
    
    def test_databuilder_with_openai_key(self):
        """测试 DataBuilder 集成 OpenAI API Key"""
        schema = {
            "type": "object",
            "properties": {
                "openai_key": {"type": "string"},
            },
            "required": ["openai_key"]
        }
        
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "openai_key", "strategy": {"type": "token", "token_type": "openai_key"}}
            ]
        })
        builder = DataBuilder(schema, config)
        
        data = builder.build(count=5)
        assert isinstance(data, list)
        assert len(data) == 5
        
        for item in data:
            assert "openai_key" in item
            assert item["openai_key"].startswith("sk-")
            assert len(item["openai_key"]) == 51
    
    def test_databuilder_with_jwt(self):
        """测试 DataBuilder 集成 JWT"""
        schema = {
            "type": "object",
            "properties": {
                "authorization": {"type": "string"},
            },
            "required": ["authorization"]
        }
        
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "authorization", "strategy": {"type": "token", "token_type": "jwt"}}
            ]
        })
        builder = DataBuilder(schema, config)
        
        data = builder.build(count=3)
        assert isinstance(data, list)
        assert len(data) == 3
        
        for item in data:
            assert "authorization" in item
            parts = item["authorization"].split(".")
            assert len(parts) == 3
    
    def test_databuilder_with_bearer(self):
        """测试 DataBuilder 集成 Bearer"""
        schema = {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
            },
            "required": ["token"]
        }
        
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "token", "strategy": {"type": "token", "token_type": "bearer", "include_prefix": True}}
            ]
        })
        builder = DataBuilder(schema, config)
        
        data = builder.build(count=3)
        for item in data:
            assert item["token"].startswith("Bearer ")
    
    def test_databuilder_dynamic_config(self):
        """测试动态配置"""
        schema = {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
            },
            "required": ["token"]
        }
        
        config_dict = {
            "policies": [
                {
                    "path": "token",
                    "strategy": {
                        "type": "token",
                        "token_type": "api_key",
                        "length": 48
                    }
                }
            ]
        }
        
        config = DataBuilder.config_from_dict(config_dict)
        builder = DataBuilder(schema, config)
        data = builder.build()
        
        assert "token" in data
        assert len(data["token"]) == 48
