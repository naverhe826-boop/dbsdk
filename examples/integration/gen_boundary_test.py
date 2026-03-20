"""
边界值测试数据生成示例

展示如何生成边界值测试数据。
"""
import json
from data_builder import DataBuilder


def example_integer_boundary():
    """整数边界值测试"""
    print("=" * 50)
    print("整数边界值测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "age": {"type": "integer", "minimum": 0, "maximum": 120}
        }
    }

    # 使用字典配置：边界值组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "BOUNDARY",
                    "fields": ["age"]
                }
            ]
        })
    ).build(count=10)
    print("\n年龄边界值测试数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_range_boundary():
    """数值范围边界值测试"""
    print("\n" + "=" * 50)
    print("数值范围边界值测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 100, "multipleOf": 10}
        }
    }

    # 使用字典配置：边界值组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "BOUNDARY",
                    "fields": ["score"]
                }
            ]
        })
    ).build(count=10)
    print("\n分数边界值测试数据 (10的倍数):")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_string_length_boundary():
    """字符串长度边界值测试"""
    print("\n" + "=" * 50)
    print("字符串长度边界值测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3, "maxLength": 20}
        }
    }

    # 使用字典配置：边界值组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "BOUNDARY",
                    "fields": ["username"]
                }
            ]
        })
    ).build(count=10)
    print("\n用户名长度边界值测试数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_array_boundary():
    """数组边界值测试"""
    print("\n" + "=" * 50)
    print("数组边界值测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "items": {"type": "integer"}
            }
        }
    }

    # 使用字典配置：边界值组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "BOUNDARY",
                    "fields": ["items"]
                }
            ]
        })
    ).build(count=10)
    print("\n数组元素数量边界值测试数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_multi_field_boundary():
    """多字段组合边界值测试"""
    print("\n" + "=" * 50)
    print("多字段组合边界值测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "price": {"type": "number", "minimum": 0, "maximum": 1000, "multipleOf": 100},
            "quantity": {"type": "integer", "minimum": 1, "maximum": 100},
            "discount": {"type": "number", "minimum": 0, "maximum": 0.5}
        }
    }

    # 使用字典配置：边界值组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "BOUNDARY",
                    "fields": ["price", "quantity", "discount"]
                }
            ]
        })
    ).build(count=20)
    print("\n多字段组合边界值测试数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_equivalence_class():
    """等价类测试"""
    print("\n" + "=" * 50)
    print("等价类测试")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["pending", "active", "inactive", "deleted"]},
            "priority": {"type": "integer", "minimum": 1, "maximum": 5}
        }
    }

    # 使用字典配置：等价类组合模式
    result = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict({
            "combinations": [
                {
                    "mode": "EQUIVALENCE",
                    "fields": ["status", "priority"]
                }
            ]
        })
    ).build(count=20)
    print("\n等价类测试数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    example_integer_boundary()
    example_range_boundary()
    example_string_length_boundary()
    example_array_boundary()
    example_multi_field_boundary()
    example_equivalence_class()
