"""身份证号生成示例

演示如何使用 DataBuilder + config 字典方式生成身份证号。
"""

import json
from data_builder import DataBuilder, BuilderConfig


def example_basics():
    """基本用法示例：生成身份证号"""
    print("=" * 60)
    print("1. 基本用法：生成身份证号")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "id_number": {"type": "string"}
        },
        "required": ["id_number"]
    }
    
    config_dict = {
        "policies": [
            {"path": "id_number", "strategy": {"type": "id_card"}}
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['id_number']}")
    
    print()


def example_age_range():
    """指定年龄范围示例"""
    print("\n" + "=" * 60)
    print("2. 指定年龄范围：25-35岁")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "id_number": {"type": "string"}
        },
        "required": ["id_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "id_number",
                "strategy": {
                    "type": "id_card",
                    "params": {"min_age": 25, "max_age": 35}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        print(f"{i}. {item['id_number']}")
    
    print()


def example_gender_specific():
    """指定性别示例"""
    print("\n" + "=" * 60)
    print("3. 指定性别")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "id_number": {"type": "string"}
        },
        "required": ["id_number"]
    }
    
    # 男性（第17位为奇数）
    print("男性身份证号（第17位为奇数）：")
    config_dict = {
        "policies": [
            {
                "path": "id_number",
                "strategy": {
                    "type": "id_card",
                    "params": {"gender": "male"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=3)
    
    for i, item in enumerate(data, 1):
        id_num = item['id_number']
        gender_digit = int(id_num[16])
        print(f"{i}. {id_num} (性别位: {gender_digit}, 奇数)")
    
    print()
    
    # 女性（第17位为偶数）
    print("女性身份证号（第17位为偶数）：")
    config_dict = {
        "policies": [
            {
                "path": "id_number",
                "strategy": {
                    "type": "id_card",
                    "params": {"gender": "female"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=3)
    
    for i, item in enumerate(data, 1):
        id_num = item['id_number']
        gender_digit = int(id_num[16])
        print(f"{i}. {id_num} (性别位: {gender_digit}, 偶数)")
    
    print()


def example_region_specific():
    """指定地区码示例"""
    print("\n" + "=" * 60)
    print("4. 指定地区码：北京市东城区（110101）")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "id_number": {"type": "string"}
        },
        "required": ["id_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "id_number",
                "strategy": {
                    "type": "id_card",
                    "params": {"region": "110101"}
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        id_num = item['id_number']
        region_code = id_num[:6]
        print(f"{i}. {id_num} (地区码: {region_code})")
    
    print()


def example_combined_config():
    """组合配置示例"""
    print("\n" + "=" * 60)
    print("5. 组合配置：25-35岁男性 + 北京地区")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "id_number": {"type": "string"}
        },
        "required": ["id_number"]
    }
    
    config_dict = {
        "policies": [
            {
                "path": "id_number",
                "strategy": {
                    "type": "id_card",
                    "params": {
                        "min_age": 25,
                        "max_age": 35,
                        "gender": "male",
                        "region": "110101"
                    }
                }
            }
        ]
    }
    
    config = BuilderConfig.from_dict(config_dict)
    builder = DataBuilder(schema, config)
    data = builder.build(count=5)
    
    for i, item in enumerate(data, 1):
        id_num = item['id_number']
        region_code = id_num[:6]
        gender_digit = int(id_num[16])
        print(f"{i}. {id_num} (地区: {region_code}, 性别位: {gender_digit})")
    
    print()


if __name__ == "__main__":
    example_basics()
    example_age_range()
    example_gender_specific()
    example_region_specific()
    example_combined_config()
