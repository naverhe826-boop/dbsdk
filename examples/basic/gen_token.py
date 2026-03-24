#!/usr/bin/env python3
"""
Token 策略示例

展示如何使用 TokenStrategy 生成不同类型的认证令牌。

支持的 token 类型：
- api_key: API 密钥，固定长度随机字符串（默认前缀 sk-）
- openai_key: OpenAI API Key，51字符（sk- + 48位字母数字）
- jwt: JWT 令牌，三段式 Base64 编码
- bearer: Bearer 令牌，可选 "Bearer " 前缀
- session: 会话令牌，普通随机字符串
- access: 访问令牌
- refresh: 刷新令牌
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_builder import DataBuilder, FieldPolicy, token, BuilderConfig


def example_api_key():
    """API Key 类型示例"""
    print("\n" + "=" * 70)
    print("API Key 示例（默认无前缀，可自定义）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "api_key": {"type": "string"},
            "service_name": {"type": "string"},
        },
        "required": ["api_key"]
    }
    
    # 默认无前缀
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "api_key", "strategy": {"type": "token", "token_type": "api_key", "length": 32}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    print("默认（无前缀）:")
    for i, item in enumerate(data, 1):
        print(f"{i}. api_key: {item['api_key']}")
    
    # 自定义前缀
    config2 = DataBuilder.config_from_dict({
        "policies": [
            {"path": "api_key", "strategy": {"type": "token", "token_type": "api_key", "length": 32, "prefix": "sk-"}}
        ]
    })
    builder2 = DataBuilder(schema, config2)
    
    data2 = builder2.build(count=2)
    print("\n自定义前缀 sk-:")
    for i, item in enumerate(data2, 1):
        print(f"{i}. api_key: {item['api_key']}")


def example_openai_key():
    """OpenAI API Key 类型示例"""
    print("\n" + "=" * 70)
    print("OpenAI API Key 示例（sk- + 48位 = 51字符）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "openai_api_key": {"type": "string"},
        },
        "required": ["openai_api_key"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "openai_api_key", "strategy": {"type": "token", "token_type": "openai_key"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        key = item['openai_api_key']
        print(f"{i}. openai_api_key: {key}")
        print(f"   长度: {len(key)}, 前缀: {key[:3]}")


def example_jwt():
    """JWT Token 类型示例"""
    print("\n" + "=" * 70)
    print("JWT Token 示例")
    print("=" * 70)
    
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
    for i, item in enumerate(data, 1):
        print(f"{i}. authorization: {item['authorization']}")


def example_bearer():
    """Bearer Token 类型示例"""
    print("\n" + "=" * 70)
    print("Bearer Token 示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "bearer_token": {"type": "string"},
        },
        "required": ["bearer_token"]
    }
    
    # 带前缀
    config1 = DataBuilder.config_from_dict({
        "policies": [
            {"path": "bearer_token", "strategy": {"type": "token", "token_type": "bearer", "include_prefix": True}}
        ]
    })
    builder1 = DataBuilder(schema, config1)
    
    print("带 'Bearer ' 前缀:")
    data = builder1.build(count=2)
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['bearer_token']}")
    
    # 不带前缀
    config2 = DataBuilder.config_from_dict({
        "policies": [
            {"path": "bearer_token", "strategy": {"type": "token", "token_type": "bearer", "include_prefix": False}}
        ]
    })
    builder2 = DataBuilder(schema, config2)
    
    print("\n不带前缀:")
    data = builder2.build(count=2)
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['bearer_token']}")


def example_session():
    """Session Token 类型示例"""
    print("\n" + "=" * 70)
    print("Session Token 示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "session_token": {"type": "string"},
            "user_id": {"type": "integer"},
        },
        "required": ["session_token", "user_id"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "session_token", "strategy": {"type": "token", "token_type": "session", "length": 32}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        print(f"{i}. session_token: {item['session_token']}")


def example_access_and_refresh():
    """Access Token 和 Refresh Token 类型示例"""
    print("\n" + "=" * 70)
    print("Access Token & Refresh Token 示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"},
            "expires_in": {"type": "integer"},
        },
        "required": ["access_token", "refresh_token"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "access_token", "strategy": {"type": "token", "token_type": "access", "length": 32}},
            {"path": "refresh_token", "strategy": {"type": "token", "token_type": "refresh", "length": 64}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        print(f"{i}. access_token:  {item['access_token']}")
        print(f"   refresh_token: {item['refresh_token']}")
        print()


def example_custom_prefix():
    """自定义前缀示例"""
    print("\n" + "=" * 70)
    print("自定义前缀示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "custom_token": {"type": "string"},
        },
        "required": ["custom_token"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "custom_token", "strategy": {
                "type": "token",
                "token_type": "session",
                "length": 24,
                "prefix": "MYAPP_"
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        print(f"{i}. custom_token: {item['custom_token']}")


def example_dynamic_config():
    """动态配置示例"""
    print("\n" + "=" * 70)
    print("动态配置示例（从字典加载）")
    print("=" * 70)
    
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
                    "token_type": "jwt",
                    "length": 32
                }
            }
        ]
    }
    
    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=2)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. token: {item['token']}")


if __name__ == "__main__":
    """运行所有示例"""
    example_api_key()
    example_openai_key()
    example_jwt()
    example_bearer()
    example_session()
    example_access_and_refresh()
    example_custom_prefix()
    example_dynamic_config()
