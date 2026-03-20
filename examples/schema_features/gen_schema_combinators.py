"""
复杂 allOf/anyOf/oneOf 组合示例

展示多关键字组合的复杂用法。
"""
import json
from data_builder import DataBuilder


def example_allof_combinations():
    """演示 allOf 组合使用场景"""
    print("=" * 50)
    print("allOf 组合示例")
    print("=" * 50)

    # 场景1: 基础 allOf 合并
    schema1 = {
        "type": "object",
        "properties": {
            "user": {
                "allOf": [
                    {"type": "object", "properties": {"name": {"type": "string"}}},
                    {"type": "object", "properties": {"email": {"type": "string", "format": "email"}}}
                ]
            }
        }
    }
    builder1 = DataBuilder(schema1)
    result1 = builder1.build(count=3)
    print("\n1. 基础 allOf 合并:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    # 场景2: allOf + required
    schema2 = {
        "type": "object",
        "properties": {
            "data": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                        "required": ["id"]
                    },
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"]
                    }
                ]
            }
        }
    }
    builder2 = DataBuilder(schema2)
    result2 = builder2.build(count=2)
    print("\n2. allOf + required 合并:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))


def example_anyof_combinations():
    """演示 anyOf 组合使用场景"""
    print("\n" + "=" * 50)
    print("anyOf 组合示例")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "payment": {
                "anyOf": [
                    {"type": "object", "properties": {"type": {"const": "card"}, "card_no": {"type": "string"}}},
                    {"type": "object", "properties": {"type": {"const": "alipay"}, "ali_id": {"type": "string"}}},
                    {"type": "object", "properties": {"type": {"const": "wechat"}, "wx_id": {"type": "string"}}}
                ]
            }
        }
    }
    builder = DataBuilder(schema)
    result = builder.build(count=5)
    print("\nanyOf 随机选择分支:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_oneof_combinations():
    """演示 oneOf 组合使用场景"""
    print("\n" + "=" * 50)
    print("oneOf 组合示例")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "response": {
                "oneOf": [
                    {"type": "object", "properties": {"status": {"const": "success"}, "data": {"type": "object"}}},
                    {"type": "object", "properties": {"status": {"const": "error"}, "message": {"type": "string"}}}
                ]
            }
        }
    }
    builder = DataBuilder(schema)
    result = builder.build(count=5)
    print("\noneOf 互斥分支:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_complex_combination():
    """演示复杂组合: allOf + anyOf"""
    print("\n" + "=" * 50)
    print("复杂组合: allOf + anyOf")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "request": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    {
                        "anyOf": [
                            {"properties": {"action": {"const": "create"}}},
                            {"properties": {"action": {"const": "update"}}},
                            {"properties": {"action": {"const": "delete"}}}
                        ]
                    }
                ]
            }
        }
    }
    builder = DataBuilder(schema)
    result = builder.build(count=3)
    print("\nallOf + anyOf 组合:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    example_allof_combinations()
    example_anyof_combinations()
    example_oneof_combinations()
    example_complex_combination()
