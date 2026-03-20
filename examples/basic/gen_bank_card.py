"""银行卡号生成示例

演示如何使用 DataBuilder + config 字典方式生成银行卡号。
"""

import json
from data_builder import DataBuilder, BuilderConfig


def example_basics():
    """基本用法示例：生成银行卡号"""
    print("=" * 60)
    print("1. 基本用法：生成银行卡号")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "card_number": {"type": "string"}
        },
        "required": ["card_number"]
    }
    
    config_dict = {
        "policies": [
            {"path": "card_number", "strategy": {"type": "bank_card"}}
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['card_number']}")
    
    print()


def example_specific_bank():
    """指定银行示例"""
    print("\n" + "=" * 60)
    print("2. 指定银行")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "card_number": {"type": "string"}
        },
        "required": ["card_number"]
    }
    
    banks = {
        "icbc": "工商银行",
        "cbc": "建设银行",
        "abc": "农业银行",
        "boc": "中国银行",
        "cmb": "招商银行",
    }
    
    for bank_code, bank_name in banks.items():
        config_dict = {
            "policies": [
                {
                    "path": "card_number",
                    "strategy": {
                        "type": "bank_card",
                        "params": {"bank": bank_code}
                    }
                }
            ]
        }
        
        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        item = builder.build()
        card_num = item['card_number']
        bin_code = card_num[:6]
        print(f"{bank_name}: {card_num} (BIN: {bin_code})")
    
    print()


def example_card_type():
    """指定卡类型示例"""
    print("\n" + "=" * 60)
    print("3. 指定卡类型")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "card_number": {"type": "string"}
        },
        "required": ["card_number"]
    }
    
    # 借记卡
    print("借记卡：")
    config_dict = {
        "policies": [
            {
                "path": "card_number",
                "strategy": {
                    "type": "bank_card",
                    "params": {"card_type": "debit"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=3)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['card_number']}")
    
    print()
    
    # 信用卡
    print("信用卡：")
    config_dict = {
        "policies": [
            {
                "path": "card_number",
                "strategy": {
                    "type": "bank_card",
                    "params": {"card_type": "credit"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=3)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['card_number']}")
    
    print()


def example_combined_config():
    """组合配置示例"""
    print("\n" + "=" * 60)
    print("4. 组合配置：工商银行借记卡")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "card_number": {"type": "string"}
        },
        "required": ["card_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "card_number",
                "strategy": {
                    "type": "bank_card",
                    "params": {
                        "bank": "icbc",
                        "card_type": "debit"
                    }
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        card_num = item['card_number']
        bin_code = card_num[:6]
        print(f"{i}. {card_num} (BIN: {bin_code})")
    
    print()


if __name__ == "__main__":
    example_basics()
    example_specific_bank()
    example_card_type()
    example_combined_config()
