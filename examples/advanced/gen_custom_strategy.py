#!/usr/bin/env python3
"""
自定义策略扩展示例

展示如何创建和使用自定义策略，包括：
1. 从 Strategy 基类继承创建自定义值策略
2. 从 StructureStrategy 继承创建自定义结构策略
3. 使用 StrategyRegistry 注册自定义策略
4. 使用 callable_strategy 作为轻量级替代方案
"""

import json
import uuid
from typing import Any, List, Optional

from data_builder import DataBuilder, FieldPolicy, BuilderConfig, callable_strategy
from data_builder.strategies.basic import FixedStrategy
from data_builder.strategies.basic.base import Strategy, StrategyContext, StructureStrategy
from data_builder.strategies.value.registry import StrategyRegistry


# ============================================================
# 自定义策略类定义
# ============================================================

class UUIDv5Strategy(Strategy):
    """
    自定义 UUID v5 生成策略

    UUID v5 是基于名字空间和字符串的确定性 UUID，
    适用于生成稳定的、可重现的标识符。
    """

    def __init__(self, namespace: str = "6ba7b810-9dad-11d1-80b4-00c04fd430c8", name: str = ""):
        """
        Args:
            namespace: UUID 命名空间（默认: URL 命名空间）
            name: 名称字符串
        """
        self.namespace = namespace
        self.name = name

    def generate(self, ctx: StrategyContext) -> str:
        """生成 UUID v5"""
        import hashlib

        # 使用 name 或字段路径作为名称
        name = self.name or ctx.field_path or str(ctx.index)

        # 计算 SHA-1 哈希（UUID v5 使用 SHA-1）
        namespace_bytes = self.namespace.replace("-", "").encode()
        name_bytes = name.encode()
        hash_bytes = hashlib.sha1(namespace_bytes + name_bytes).digest()

        # 设置版本号（5）和变体（RFC 4122）
        hash_bytes = bytearray(hash_bytes)
        hash_bytes[6] = (hash_bytes[6] & 0x0F) | 0x50  # Version 5
        hash_bytes[8] = (hash_bytes[8] & 0x3F) | 0x80  # RFC 4122

        return str(uuid.UUID(bytes=bytes(hash_bytes[:16])))

    def values(self) -> Optional[List[Any]]:
        """值域：不可枚举"""
        return None

    def boundary_values(self) -> Optional[List[Any]]:
        """边界值：返回特殊 UUID"""
        return ["6ba7b810-9dad-11d1-80b4-00c04fd430c8"]


class CreditCardStrategy(Strategy):
    """
    自定义信用卡号生成策略

    生成符合 Luhn 算法校验的信用卡号。
    """

    CARDS = {
        "visa": ["4"],
        "mastercard": ["51", "52", "53", "54", "55"],
        "amex": ["34", "37"],
        "discover": ["6011"],
    }

    def __init__(self, card_type: str = "visa"):
        """
        Args:
            card_type: 卡片类型 (visa, mastercard, amex, discover, random)
        """
        self.card_type = card_type

    def _luhn_checksum(self, card_number: str) -> str:
        """计算 Luhn 校验位"""
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))

        return str((10 - (checksum % 10)) % 10)

    def generate(self, ctx: StrategyContext) -> str:
        """生成信用卡号"""
        import random

        # 选择卡类型
        if self.card_type == "random":
            card_type = random.choice(list(self.CARDS.keys()))
        else:
            card_type = self.card_type

        # 获取前缀
        prefixes = self.CARDS.get(card_type, ["4"])
        prefix = random.choice(prefixes)

        # 生成中间数字（根据卡类型确定长度）
        if card_type == "amex":
            middle_length = 13
        else:
            middle_length = 12

        middle = "".join([str(random.randint(0, 9)) for _ in range(middle_length)])

        # 计算校验位
        card_number = prefix + middle
        checksum = self._luhn_checksum(card_number)

        return card_number + checksum

    def values(self) -> Optional[List[Any]]:
        return None


class ConditionalArrayCountStrategy(StructureStrategy):
    """
    自定义条件数组数量策略

    根据父级字段的值动态决定数组元素数量。
    例如：当 status="active" 时生成更多元素。
    """

    def __init__(
        self,
        conditions: dict,  # {"字段路径": {">": 阈值, "值列表": [...]}}
        default_count: int = 3
    ):
        """
        Args:
            conditions: 条件映射表
            default_count: 默认数组元素数量
        """
        self.conditions = conditions
        self.default_count = default_count

    def generate(self, ctx: StrategyContext) -> int:
        """根据条件返回数组元素数量"""
        import random

        # 获取父级数据
        parent = ctx.parent_data if isinstance(ctx.parent_data, dict) else {}

        # 检查每个条件
        for field_path, condition in self.conditions.items():
            # 尝试从父级数据获取字段值
            value = parent.get(field_path.split(".")[-1])

            if value is not None:
                # 数值比较条件
                if "min" in condition and isinstance(value, (int, float)):
                    if value >= condition["min"]:
                        return condition.get("result", self.default_count)

                # 值列表条件
                if "values" in condition and value in condition["values"]:
                    return condition.get("result", self.default_count)

        return self.default_count


# ============================================================
# 示例函数
# ============================================================

def example_custom_uuid_strategy():
    """自定义 UUID v5 策略示例"""
    print("=" * 60)
    print("自定义 UUID v5 策略")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "device_id": {"type": "string"},
        }
    }

    builder = DataBuilder(schema, config=BuilderConfig(
        policies=[
            FieldPolicy("user_id", UUIDv5Strategy(name="user")),
            FieldPolicy("device_id", UUIDv5Strategy(name="device")),
        ]
    ))

    result = builder.build(count=3)
    print("\n生成的数据:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_custom_credit_card_strategy():
    """自定义信用卡号策略示例"""
    print("\n" + "=" * 60)
    print("自定义信用卡号策略")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "card_number": {"type": "string"},
            "card_type": {"type": "string"},
        }
    }

    builder = DataBuilder(schema, config=BuilderConfig(
        policies=[
            FieldPolicy("card_number", CreditCardStrategy(card_type="visa")),
            FieldPolicy("card_type", FixedStrategy("visa")),
        ]
    ))

    result = builder.build(count=3)
    print("\n生成的信用卡号:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_strategy_registry():
    """通过注册表创建自定义策略示例"""
    print("\n" + "=" * 60)
    print("通过注册表创建自定义策略")
    print("=" * 60)

    # 注册自定义策略
    StrategyRegistry.register("uuid_v5", UUIDv5Strategy)
    StrategyRegistry.register("credit_card", CreditCardStrategy)
    StrategyRegistry.register("conditional_array", ConditionalArrayCountStrategy)

    # 通过策略配置字典创建
    policy_config = {
        "path": "transaction_id",
        "strategy": {
            "type": "uuid_v5",
            "name": "transaction"
        }
    }

    policy = StrategyRegistry.create_from_policy_config(policy_config)
    print(f"\n创建的策略: {policy}")

    # 清理注册的策略
    for name in ["uuid_v5", "credit_card", "conditional_array"]:
        if StrategyRegistry.has(name):
            del StrategyRegistry._strategies[name]


def example_custom_structure_strategy():
    """自定义结构策略示例"""
    print("\n" + "=" * 60)
    print("自定义条件数组数量策略")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "items": {
                "type": "array",
                "items": {"type": "object"}
            }
        }
    }

    builder = DataBuilder(schema, config=BuilderConfig(
        policies=[
            FieldPolicy("status", FixedStrategy("active")),
            FieldPolicy("items", ConditionalArrayCountStrategy(
                conditions={
                    "status": {
                        "values": ["active"],
                        "result": 5  # active 状态生成 5 个元素
                    }
                },
                default_count=2
            )),
        ]
    ))

    result = builder.build(count=1)
    print("\n生成的数据 (active 状态生成 5 个元素):")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_callable_strategy():
    """使用 callable_strategy 轻量级自定义示例"""
    print("\n" + "=" * 60)
    print("callable_strategy 轻量级自定义")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "checksum": {"type": "string"},
        }
    }

    # 创建上下文感知的可调用策略
    def generate_id_with_checksum(ctx: StrategyContext) -> str:
        """生成带校验的 ID"""
        import random
        import hashlib

        # 根据索引生成基础 ID
        base_id = f"USER-{ctx.index:04d}"

        # 添加随机后缀
        random_suffix = "".join([
            random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            for _ in range(4)
        ])

        full_id = f"{base_id}-{random_suffix}"

        # 计算简单校验和
        checksum = sum(ord(c) for c in full_id) % 100

        return f"{full_id}-{checksum:02d}"

    builder = DataBuilder(schema, config=BuilderConfig(
        policies=[
            FieldPolicy("id", callable_strategy(generate_id_with_checksum)),
        ]
    ))

    result = builder.build(count=5)
    print("\n生成的带校验和的 ID:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_complex_scenario():
    """复杂场景：组合使用自定义策略"""
    print("\n" + "=" * 60)
    print("复杂场景 - 订单数据生成")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "customer_id": {"type": "string"},
            "payment_card": {"type": "string"},
            "items": {
                "type": "array",
                "items": {"type": "object"}
            }
        }
    }

    builder = DataBuilder(schema, config=BuilderConfig(
        policies=[
            # 使用自定义 UUID 策略
            FieldPolicy("order_id", UUIDv5Strategy(name="order")),
            FieldPolicy("customer_id", UUIDv5Strategy(name="customer")),
            # 使用自定义信用卡策略
            FieldPolicy("payment_card", CreditCardStrategy(card_type="mastercard")),
            # 使用自定义条件数组策略
            FieldPolicy("items", ConditionalArrayCountStrategy(
                conditions={},
                default_count=3
            )),
        ]
    ))

    result = builder.build(count=2)
    print("\n生成的订单数据:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    example_custom_uuid_strategy()
    example_custom_credit_card_strategy()
    example_strategy_registry()
    example_custom_structure_strategy()
    example_callable_strategy()
    example_complex_scenario()

    print("\n✓ 所有示例执行完成")
