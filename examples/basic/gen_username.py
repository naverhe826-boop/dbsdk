"""用户名生成示例

演示如何使用 DataBuilder + config 字典方式生成用户名。
"""

import json
from data_builder import DataBuilder, BuilderConfig


def example_basics():
    """基本用法示例：生成用户名"""
    print("=" * 60)
    print("1. 基本用法：生成用户名")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    config_dict = {
        "policies": [
            {"path": "username", "strategy": {"type": "username"}}
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=10)
    
    for i, item in enumerate(data, 1):
        user = item['username']
        print(f"{i:2d}. {user} (长度: {len(user)})")
    
    print()


def example_length_range():
    """指定长度范围示例"""
    print("\n" + "=" * 60)
    print("2. 指定长度范围：8-12位")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "username",
                "strategy": {
                    "type": "username",
                    "params": {"min_length": 8, "max_length": 12}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=10)
    
    for i, item in enumerate(data, 1):
        user = item['username']
        print(f"{i:2d}. {user} (长度: {len(user)})")
    
    print()


def example_charset_types():
    """不同字符集示例"""
    print("\n" + "=" * 60)
    print("3. 不同字符集")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    charsets = {
        "alphanumeric": "仅字母数字",
        "alphanumeric_underscore": "字母数字+下划线",
        "alphanumeric_dot": "字母数字+点号",
        "alphanumeric_dash": "字母数字+连字符",
    }
    
    for charset, desc in charsets.items():
        config_dict = {
            "policies": [
                {
                    "path": "username",
                    "strategy": {
                        "type": "username",
                        "params": {"charset": charset}
                    }
                }
            ]
        }
        
        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        item = builder.build()
        print(f"{desc:20s}: {item['username']}")
    
    print()


def example_no_uppercase():
    """禁用大写字母示例"""
    print("\n" + "=" * 60)
    print("4. 禁用大写字母")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "username",
                "strategy": {
                    "type": "username",
                    "params": {"allow_uppercase": False}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    print("仅小写字母和数字：")
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['username']}")
    
    print()


def example_custom_reserved():
    """自定义保留字示例"""
    print("\n" + "=" * 60)
    print("5. 自定义保留字")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    custom_words = ["test", "demo", "example", "sample"]
    
    config_dict = {
        "policies": [
            {
                "path": "username",
                "strategy": {
                    "type": "username",
                    "params": {"reserved_words": custom_words}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    print(f"自定义保留字: {custom_words}")
    print("生成的用户名：")
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['username']}")
    
    print()


def example_combined_config():
    """组合配置示例"""
    print("\n" + "=" * 60)
    print("6. 组合配置：8-12位 + 仅小写 + 自定义保留字")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"}
        },
        "required": ["username"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "username",
                "strategy": {
                    "type": "username",
                    "params": {
                        "min_length": 8,
                        "max_length": 12,
                        "allow_uppercase": False,
                        "reserved_words": ["admin", "root", "test"]
                    }
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        user = item['username']
        print(f"{i}. {user} (长度: {len(user)})")
    
    print()


if __name__ == "__main__":
    example_basics()
    example_length_range()
    example_charset_types()
    example_no_uppercase()
    example_custom_reserved()
    example_combined_config()
