"""
结构策略示例：演示 property_count/property_selection/schema_selection/contains_count/array_count 控制数据结构。

包含以下示例：
- property_count：控制对象属性数量
- property_selection：精确选择属性
- schema_selection：控制 oneOf 分支选择
- contains_count：控制数组中特殊元素数量
- array_count + 子字段策略：精确控制数组
- 多策略组合：同时使用多种结构策略
"""

import json

from data_builder import DataBuilder


def example_property_count():
    """property_count 示例"""
    print("=" * 60)
    print("1. property_count — 控制对象属性数量")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "profile": {
                "type": "object",
                "properties": {
                    "name":  {"type": "string"},
                    "age":   {"type": "integer", "minimum": 18, "maximum": 65},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "city":  {"type": "string"},
                },
                "required": ["name"],
            }
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "profile", "strategy": {"type": "property_count", "count": 3}},
            {"path": "profile.name", "strategy": {"type": "faker", "method": "name"}},
        ]
    })

    results = DataBuilder(schema, config).build(count=3)
    print("每条记录的 profile 只有 3 个属性（name 必选）：")
    for r in results:
        print(f"  属性: {list(r['profile'].keys())}")


def example_property_selection():
    """property_selection 示例"""
    print("\n" + "=" * 60)
    print("2. property_selection — 精确选择属性")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "profile": {
                "type": "object",
                "properties": {
                    "name":  {"type": "string"},
                    "age":   {"type": "integer", "minimum": 18, "maximum": 65},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "city":  {"type": "string"},
                },
                "required": ["name"],
            }
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "profile", "strategy": {"type": "property_selection", "properties": ["name", "email"]}},
            {"path": "profile.name", "strategy": {"type": "faker", "method": "name"}},
        ]
    })

    result = DataBuilder(schema, config).build()
    print(f"只生成 name 和 email: {list(result['profile'].keys())}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    # 动态选择：根据 index 生成不同属性（需要使用 callable）
    print("\n动态选择（按 index 交替）：")
    # 注意：dict 配置中暂不支持动态 property_selection 复杂逻辑，回退到静态示例
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "profile", "strategy": {"type": "property_selection", "properties": ["name", "age", "city"]}},
            {"path": "profile.name", "strategy": {"type": "faker", "method": "name"}},
        ]
    })

    results = DataBuilder(schema, config).build(count=2)
    for i, r in enumerate(results):
        print(f"  [{i}] 属性: {list(r['profile'].keys())}")


def example_schema_selection():
    """schema_selection 示例"""
    print("\n" + "=" * 60)
    print("3. schema_selection — 控制 oneOf 分支选择")
    print("=" * 60)

    payment_schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"},
            "payment": {
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "method": {"type": "string", "const": "card"},
                            "card_no": {"type": "string"},
                            "bank":    {"type": "string"},
                        },
                    },
                    {
                        "type": "object",
                        "properties": {
                            "method":  {"type": "string", "const": "alipay"},
                            "account": {"type": "string", "format": "email"},
                        },
                    },
                ]
            },
        },
    }

    # 固定选择分支 0（银行卡）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "order_id", "strategy": {"type": "sequence", "start": 1}},
            {"path": "payment", "strategy": {"type": "schema_selection", "index": 0}},
            {"path": "payment.card_no", "strategy": {"type": "sequence", "prefix": "6222-", "padding": 12}},
            {"path": "payment.bank", "strategy": {"type": "enum", "choices": ["工商银行", "建设银行", "招商银行"]}},
        ]
    })
    results = DataBuilder(payment_schema, config).build(count=3)
    print("固定银行卡分支：")
    for r in results:
        print(f"  订单 {r['order_id']}: {r['payment']}")

    # 动态交替分支（需要使用 callable，dict 配置中暂不支持复杂动态逻辑）
    print("\n固定选择支付宝分支：")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "order_id", "strategy": {"type": "sequence", "start": 1}},
            {"path": "payment", "strategy": {"type": "schema_selection", "index": 1}},
            {"path": "payment.account", "strategy": {"type": "faker", "method": "email"}},
        ]
    })
    results = DataBuilder(payment_schema, config).build(count=2)
    for r in results:
        print(f"  订单 {r['order_id']}: method={r['payment'].get('method')}, keys={list(r['payment'].keys())}")


def example_contains_count():
    """contains_count 示例"""
    print("\n" + "=" * 60)
    print("4. contains_count — 控制数组中特殊元素数量")
    print("=" * 60)

    mixed_array_schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "contains": {"type": "integer", "minimum": 999, "maximum": 999},
                "minItems": 5,
                "maxItems": 5,
            }
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "items", "strategy": {"type": "contains_count", "count": 2}},
        ]
    })

    results = DataBuilder(mixed_array_schema, config).build(count=3)
    print("每个数组 5 个元素，其中 2 个为 999（contains 元素）：")
    for r in results:
        arr = r["items"]
        int_count = sum(1 for x in arr if isinstance(x, int))
        print(f"  {arr}  (整数个数: {int_count})")


def example_array_count_with_subfields():
    """array_count + 子字段策略示例"""
    print("\n" + "=" * 60)
    print("5. array_count + 子字段策略")
    print("=" * 60)

    list_schema = {
        "type": "object",
        "properties": {
            "students": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":    {"type": "string"},
                        "name":  {"type": "string"},
                        "score": {"type": "number"},
                    },
                },
                "minItems": 1,
                "maxItems": 10,
            }
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "students", "strategy": {"type": "array_count", "count": 4}},
            {"path": "students[*].id", "strategy": {"type": "sequence", "start": 1, "prefix": "STU-", "padding": 3}},
            {"path": "students[*].name", "strategy": {"type": "faker", "method": "name"}},
            {"path": "students[*].score", "strategy": {"type": "range", "min": 60.0, "max": 100.0, "precision": 1}},
        ]
    })

    result = DataBuilder(list_schema, config).build()
    print("固定 4 个学生，ID 连续递增：")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def example_multiple_strategies():
    """多策略组合示例"""
    print("\n" + "=" * 60)
    print("6. 多策略组合 — property_count + array_count + schema_selection")
    print("=" * 60)

    complex_schema = {
        "type": "object",
        "properties": {
            "config": {
                "type": "object",
                "properties": {
                    "timeout":  {"type": "integer", "minimum": 1, "maximum": 60},
                    "retries":  {"type": "integer", "minimum": 0, "maximum": 5},
                    "verbose":  {"type": "boolean"},
                    "log_level": {"type": "string"},
                },
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 10,
            },
            "output": {
                "oneOf": [
                    {"type": "object", "properties": {"format": {"type": "string", "const": "json"}, "indent": {"type": "integer", "minimum": 2, "maximum": 4}}},
                    {"type": "object", "properties": {"format": {"type": "string", "const": "csv"}, "delimiter": {"type": "string", "const": ","}}},
                ]
            },
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "config", "strategy": {"type": "property_count", "count": 2}},
            {"path": "tags", "strategy": {"type": "array_count", "count": 3}},
            {"path": "tags[*]", "strategy": {"type": "enum", "choices": ["测试", "生产", "预发", "灰度", "开发"]}},
            {"path": "output", "strategy": {"type": "schema_selection", "index": 0}},
        ]
    })

    results = DataBuilder(complex_schema, config).build(count=2)
    for r in results:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        print("-" * 40)


if __name__ == "__main__":
    print("结构策略示例")
    print("=" * 60)
    example_property_count()
    example_property_selection()
    example_schema_selection()
    example_contains_count()
    example_array_count_with_subfields()
    example_multiple_strategies()
