"""手机号生成示例

演示如何使用 DataBuilder + config 字典方式生成手机号。
"""

import json
from data_builder import DataBuilder, BuilderConfig


def example_basics():
    """基本用法示例：生成手机号"""
    print("=" * 60)
    print("1. 基本用法：生成手机号")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string"}
        },
        "required": ["phone_number"]
    }
    
    config_dict = {
        "policies": [
            {"path": "phone_number", "strategy": {"type": "phone"}}
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['phone_number']}")
    
    print()


def example_specific_carrier():
    """指定运营商示例"""
    print("\n" + "=" * 60)
    print("2. 指定运营商")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string"}
        },
        "required": ["phone_number"]
    }
    
    carriers = {
        "mobile": "中国移动",
        "unicom": "中国联通",
        "telecom": "中国电信",
    }
    
    for carrier_code, carrier_name in carriers.items():
        config_dict = {
            "policies": [
                {
                    "path": "phone_number",
                    "strategy": {
                        "type": "phone",
                        "params": {"carrier": carrier_code}
                    }
                }
            ]
        }
        
        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        item = builder.build()
        phone_num = item['phone_number']
        prefix = phone_num[:3]
        print(f"{carrier_name}: {phone_num} (号段: {prefix})")
    
    print()


def example_virtual_carrier():
    """虚拟运营商示例"""
    print("\n" + "=" * 60)
    print("3. 虚拟运营商")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string"}
        },
        "required": ["phone_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "phone_number",
                "strategy": {
                    "type": "phone",
                    "params": {"number_type": "virtual"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    print("虚拟运营商号段（170、171等）：")
    for i, item in enumerate(data, 1):
        phone_num = item['phone_number']
        prefix = phone_num[:3]
        print(f"{i}. {phone_num} (号段: {prefix})")
    
    print()


def example_combined_config():
    """组合配置示例"""
    print("\n" + "=" * 60)
    print("4. 组合配置：中国移动普通号码")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string"}
        },
        "required": ["phone_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "phone_number",
                "strategy": {
                    "type": "phone",
                    "params": {
                        "carrier": "mobile",
                        "number_type": "normal"
                    }
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        phone_num = item['phone_number']
        prefix = phone_num[:3]
        print(f"{i}. {phone_num} (号段: {prefix})")
    
    print()


if __name__ == "__main__":
    example_basics()
    example_specific_carrier()
    example_virtual_carrier()
    example_combined_config()
