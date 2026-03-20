"""
订单数据生成示例。

展示如何使用各种策略生成完整的订单数据结构，包括：
- 订单基本信息（ID、订单号）
- 用户信息（姓名、电话、邮箱）
- 商品列表（数组类型，每个商品有 ID、名称、价格、数量）
- 订单状态和时间戳
- 引用策略（ref）实现字段关联

包含以下示例：
- 订单生成：完整的订单数据结构
"""

from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    fixed,
    range_int,
    enum,
    seq,
    faker,
    ref,
    datetime,
)


def example_order_generation():
    """订单生成示例"""
    print("=" * 60)
    print("订单数据生成示例")
    print("=" * 60)

    # 定义用户订单 schema
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "order_no": {"type": "string"},
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "price": {"type": "number"},
                        "quantity": {"type": "integer"},
                    },
                },
                "minItems": 2,
                "maxItems": 3,
            },
            "status": {"type": "string"},
            "created_at": {"type": "string"},
            "updated_by": {"type": "integer"},
        },
    }

    # 配置字段生成策略
    config = BuilderConfig(
        policies=[
            FieldPolicy("id", seq(start=1001)),
            FieldPolicy("order_no", seq(start=1, prefix="ORD-", padding=6)),
            FieldPolicy("user.name", faker("name")),
            FieldPolicy("user.phone", faker("phone_number")),
            FieldPolicy("items[*].product_id", seq(start=100)),
            FieldPolicy("items[*].product_name", faker("word")),
            FieldPolicy("items[*].price", range_int(10, 500)),
            FieldPolicy("items[*].quantity", range_int(1, 5)),
            FieldPolicy("status", enum(["pending", "paid", "shipped", "completed"])),
            FieldPolicy("created_at", datetime()),
            FieldPolicy("updated_by", ref("id")),
        ]
    )

    builder = DataBuilder(schema, config)

    # 生成 3 条订单数据
    orders = builder.build(count=3)

    for order in orders:
        print(order)
        print("-" * 60)


def example_order_dict_config():
    """通过 dict 配置加载订单数据示例"""
    print("=" * 60)
    print("订单数据生成示例（dict 配置）")
    print("=" * 60)

    # 定义用户订单 schema
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "order_no": {"type": "string"},
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                },
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "price": {"type": "number"},
                        "quantity": {"type": "integer"},
                    },
                },
                "minItems": 2,
                "maxItems": 3,
            },
            "status": {"type": "string"},
            "created_at": {"type": "string"},
            "updated_by": {"type": "integer"},
        },
    }

    # 通过 dict 配置策略
    config_dict = {
        "policies": [
            {"path": "id", "strategy": {"type": "sequence", "start": 1001}},
            {"path": "order_no", "strategy": {"type": "sequence", "start": 1, "prefix": "ORD-", "padding": 6}},
            {"path": "user.name", "strategy": {"type": "faker", "method": "name"}},
            {"path": "user.phone", "strategy": {"type": "faker", "method": "phone_number"}},
            {"path": "user.email", "strategy": {"type": "email", "email_type": "qq"}},
            {"path": "items[*].product_id", "strategy": {"type": "sequence", "start": 100}},
            {"path": "items[*].product_name", "strategy": {"type": "faker", "method": "word"}},
            {"path": "items[*].price", "strategy": {"type": "range", "min": 10, "max": 500}},
            {"path": "items[*].quantity", "strategy": {"type": "range", "min": 1, "max": 5}},
            {"path": "status", "strategy": {"type": "enum", "values": ["pending", "paid", "shipped", "completed"]}},
            {"path": "created_at", "strategy": {"type": "datetime"}},
            {"path": "updated_by", "strategy": {"type": "ref", "ref_path": "id"}},
        ],
    }

    config = BuilderConfig.from_dict(config_dict)

    builder = DataBuilder(schema, config)

    # 生成 3 条订单数据
    orders = builder.build(count=3)

    for order in orders:
        print(order)
        print("-" * 60)


if __name__ == "__main__":
    example_order_generation()
    print()
    example_order_dict_config()
