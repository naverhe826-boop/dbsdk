"""
组合生成示例：演示笛卡尔积、成对组合、边界值、等价类等模式。

包含以下示例：
- 笛卡尔积（CARTESIAN）：穷举所有组合
- 成对组合（PAIRWISE）：减少组合数量
- 边界值组合（BOUNDARY）：使用边界值
- 等价类组合（EQUIVALENCE）：按等价类生成
- 带约束过滤：排除不合法组合
- count 采样：从组合结果中随机采样
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_builder import DataBuilder


def example_cartesian():
    """笛卡尔积示例"""
    print("=" * 60)
    print("1. 笛卡尔积（CARTESIAN）")
    print("=" * 60)

    # Schema：支付测试场景
    schema = {
        "type": "object",
        "properties": {
            "pay_method":  {"type": "string"},
            "currency":    {"type": "string"},
            "amount":      {"type": "integer"},
            "user_level":  {"type": "string"},
            "description": {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "pay_method", "strategy": {"type": "enum", "choices": ["alipay", "wechat", "card"]}},
            {"path": "currency", "strategy": {"type": "enum", "choices": ["CNY", "USD"]}},
            {"path": "amount", "strategy": {"type": "fixed", "value": 100}},
        ],
        "combinations": [
            {"mode": "cartesian", "fields": ["pay_method", "currency"]}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build()
    print(f"共 {len(results)} 条（3×2=6）")
    for r in results:
        print(f"  {r['pay_method']:>8s} | {r['currency']} | amount={r['amount']}")


def example_pairwise():
    """成对组合示例"""
    print("\n" + "=" * 60)
    print("2. 成对组合（PAIRWISE）")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "pay_method":  {"type": "string"},
            "currency":    {"type": "string"},
            "user_level":  {"type": "string"},
            "amount":      {"type": "integer"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "pay_method", "strategy": {"type": "enum", "choices": ["alipay", "wechat", "card"]}},
            {"path": "currency", "strategy": {"type": "enum", "choices": ["CNY", "USD", "EUR"]}},
            {"path": "user_level", "strategy": {"type": "enum", "choices": ["normal", "vip", "svip"]}},
            {"path": "amount", "strategy": {"type": "fixed", "value": 200}},
        ],
        "combinations": [
            {"mode": "pairwise"}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build()
    print(f"共 {len(results)} 条（远少于 3×3×3=27 的全组合）")
    for r in results:
        print(f"  {r['pay_method']:>8s} | {r['currency']:>3s} | {r['user_level']:>6s} | amount={r['amount']}")


def example_boundary():
    """边界值组合示例"""
    print("\n" + "=" * 60)
    print("3. 边界值组合（BOUNDARY）")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "pay_method":  {"type": "string"},
            "amount":      {"type": "integer"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "amount", "strategy": {"type": "range", "min": 1, "max": 10000}},
            {"path": "pay_method", "strategy": {"type": "enum", "choices": ["alipay", "wechat", "card"]}},
        ],
        "combinations": [
            {"mode": "boundary"}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build()
    print(f"共 {len(results)} 条")
    for r in results:
        print(f"  amount={r['amount']:>5d} | {r['pay_method']}")


def example_equivalence():
    """等价类组合示例"""
    print("\n" + "=" * 60)
    print("4. 等价类组合（EQUIVALENCE）")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "amount":      {"type": "integer"},
            "currency":    {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "amount", "strategy": {"type": "range", "min": 0, "max": 1000}},
            {"path": "currency", "strategy": {"type": "enum", "choices": ["CNY", "USD"]}},
        ],
        "combinations": [
            {"mode": "equivalence"}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build()
    print(f"共 {len(results)} 条（amount 3个等价类 × currency 2个 = 6）")
    for r in results:
        print(f"  amount={r['amount']:>5d} | {r['currency']}")


def example_with_constraints():
    """带约束过滤的组合示例"""
    print("\n" + "=" * 60)
    print("5. 带约束 + 后置过滤")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "pay_method":  {"type": "string"},
            "currency":    {"type": "string"},
            "amount":      {"type": "integer"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "pay_method", "strategy": {"type": "enum", "choices": ["alipay", "wechat", "card"]}},
            {"path": "currency", "strategy": {"type": "enum", "choices": ["CNY", "USD", "EUR"]}},
            {"path": "amount", "strategy": {"type": "fixed", "value": 500}},
        ],
        "combinations": [
            {
                "mode": "cartesian",
                "constraints": [
                    {
                        "predicate": "not (pay_method == 'card' and currency == 'CNY')",
                        "description": "card 不支持 CNY"
                    }
                ]
            }
        ],
        "post_filters": [
            {"type": "limit", "count": 5}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build()
    print(f"共 {len(results)} 条（过滤 card+CNY 后截断为 5 条）")
    for r in results:
        print(f"  {r['pay_method']:>8s} | {r['currency']:>3s}")


def example_count_sampling():
    """count 采样示例"""
    print("\n" + "=" * 60)
    print("6. count 采样")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "pay_method":  {"type": "string"},
            "currency":    {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "pay_method", "strategy": {"type": "enum", "choices": ["alipay", "wechat", "card"]}},
            {"path": "currency", "strategy": {"type": "enum", "choices": ["CNY", "USD", "EUR"]}},
        ],
        "combinations": [
            {"mode": "cartesian"}
        ],
    })

    builder = DataBuilder(schema, config)
    results = builder.build(count=3)
    print(f"全组合 9 条中随机采样 {len(results)} 条：")
    for r in results:
        print(f"  {r['pay_method']:>8s} | {r['currency']}")


if __name__ == "__main__":
    print("组合生成示例")
    print("=" * 60)
    example_cartesian()
    example_pairwise()
    example_boundary()
    example_equivalence()
    example_with_constraints()
    example_count_sampling()
