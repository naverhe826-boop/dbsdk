"""
EnumStrategy 使用示例

展示 enum 策略的各种用法，包括：
- 基础用法（从列表中随机选择）
- 带权重的枚举选择
- 通过配置创建（使用 StrategyRegistry）
- 结合 FieldPolicy 使用
- 多种类型的枚举（字符串、整数、混合类型）
"""

import json
from data_builder import DataBuilder


def example_basics():
    """基础用法示例"""
    print("=" * 60)
    print("1. 基础用法（随机选择）")
    print("=" * 60)

    # 需要直接使用策略类来测试 values()
    from data_builder.strategies.value.enum import EnumStrategy

    schema = {"type": "object", "properties": {"status": {"type": "string"}}}

    # 从预定义选项中随机选择
    strategy = EnumStrategy(choices=["pending", "processing", "completed", "failed"])
    status = strategy.generate(None)
    print(f"  生成的状态: {status}")

    # 生成多个
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "status", "strategy": {"type": "enum", "choices": ["pending", "processing", "completed", "failed"]}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    print("  生成5条数据的状态:")
    for item in data:
        print(f"    {item['status']}")


def example_with_weights():
    """带权重的枚举选择示例"""
    print("\n" + "=" * 60)
    print("2. 带权重的枚举选择")
    print("=" * 60)

    # 需要直接使用策略类来测试 weights（dict 配置暂不支持）
    from data_builder.strategies.value.enum import EnumStrategy
    from data_builder import BuilderConfig, FieldPolicy

    schema = {"type": "object", "properties": {"priority": {"type": "string"}}}

    # 高优先级出现概率低，低优先级出现概率高
    config = BuilderConfig(
        policies=[FieldPolicy("priority", EnumStrategy(
            choices=["low", "medium", "high", "critical"],
            weights=[40, 30, 20, 10]  # 权重总和不需要为1，会自动归一化
        ))]
    )
    builder = DataBuilder(schema, config)
    data = builder.build(20)
    
    # 统计各选项出现次数
    from collections import Counter
    counts = Counter(item["priority"] for item in data)
    print("  生成20条数据，优先级分布:")
    for key, count in sorted(counts.items()):
        print(f"    {key}: {count}次 ({count/20*100:.1f}%)")


def example_integer_enum():
    """整数枚举示例"""
    print("\n" + "=" * 60)
    print("3. 整数枚举")
    print("=" * 60)

    # 需要直接使用策略类来测试 weights（dict 配置暂不支持）
    from data_builder.strategies.value.enum import EnumStrategy
    from data_builder import BuilderConfig, FieldPolicy

    schema = {"type": "object", "properties": {"code": {"type": "integer"}}}

    # HTTP 状态码枚举
    config = BuilderConfig(
        policies=[FieldPolicy("code", EnumStrategy(
            choices=[200, 201, 204, 400, 401, 403, 404, 500, 502, 503],
            weights=[30, 15, 10, 10, 5, 5, 10, 5, 5, 5]
        ))]
    )
    builder = DataBuilder(schema, config)
    data = builder.build(10)
    print("  生成10个HTTP状态码:")
    for item in data:
        print(f"    {item['code']}")


def example_mixed_enum():
    """混合类型枚举示例"""
    print("\n" + "=" * 60)
    print("4. 混合类型枚举")
    print("=" * 60)

    schema = {"type": "object", "properties": {"value": {}}}

    # 混合类型：字符串和整数
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "enum", "choices": ["unknown", 0, 1, True, False, "none"]}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(10)
    print("  生成10个混合类型值:")
    for item in data:
        print(f"    {item['value']} (类型: {type(item['value']).__name__})")


def example_enum_with_registry():
    """通过配置创建枚举策略示例"""
    print("\n" + "=" * 60)
    print("5. 通过 config_from_dict 配置")
    print("=" * 60)

    # 使用 config_from_dict 创建枚举策略
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "grade", "strategy": {"type": "enum", "choices": ["A", "B", "C", "D"]}}]
    })
    strategy = config.policies[0].strategy
    
    print(f"  策略类型: {type(strategy).__name__}")
    print(f"  选项: {strategy.choices}")
    
    # 生成数据
    schema = {"type": "object", "properties": {"grade": {"type": "string"}}}
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    print("  生成5条数据:")
    for item in data:
        print(f"    {item['grade']}")


def example_enum_boundary_values():
    """枚举边界值示例"""
    print("\n" + "=" * 60)
    print("6. 边界值和等价类")
    print("=" * 60)

    # 需要直接使用策略类来测试值域接口
    from data_builder.strategies.value.enum import EnumStrategy

    strategy = EnumStrategy(choices=[1, 2, 3, 4, 5])
    
    # values() 返回所有可能的值
    print(f"  所有可能的值: {strategy.values()}")
    
    # boundary_values() 返回边界值
    print(f"  边界值: {strategy.boundary_values()}")
    
    # equivalence_classes() 返回等价类
    print(f"  等价类: {strategy.equivalence_classes()}")


def example_enum_invalid_values():
    """枚举无效值示例"""
    print("\n" + "=" * 60)
    print("7. 无效值生成")
    print("=" * 60)

    # 需要直接使用策略类来测试无效值
    from data_builder.strategies.value.enum import EnumStrategy

    # 字符串枚举的无效值
    strategy1 = EnumStrategy(choices=["red", "green", "blue"])
    print(f"  字符串枚举的无效值: {strategy1.invalid_values()}")
    
    # 整数枚举的无效值
    strategy2 = EnumStrategy(choices=[10, 20, 30])
    print(f"  整数枚举的无效值: {strategy2.invalid_values()}")


def example_real_world_scenario():
    """真实场景示例：订单状态和支付方式"""
    print("\n" + "=" * 60)
    print("8. 真实场景：订单系统")
    print("=" * 60)

    # 需要直接使用策略类来测试 weights（dict 配置暂不支持）
    from data_builder.strategies.value.enum import EnumStrategy
    from data_builder import BuilderConfig, FieldPolicy

    schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "status": {"type": "string"},
            "payment_method": {"type": "string"},
            "priority": {"type": "string"}
        }
    }

    config = BuilderConfig(policies=[
        # 订单状态：已支付、待发货、发货中、已收货、已完成
        FieldPolicy("status", EnumStrategy(
            choices=["paid", "pending_ship", "shipped", "delivered", "completed"],
            weights=[15, 20, 15, 20, 30]
        )),
        # 支付方式：微信、支付宝、银行卡、积分抵扣
        FieldPolicy("payment_method", EnumStrategy(
            choices=["wechat", "alipay", "bank_card", "points"],
            weights=[40, 40, 15, 5]
        )),
        # 优先级
        FieldPolicy("priority", EnumStrategy(
            choices=["low", "normal", "high", "urgent"],
            weights=[10, 60, 20, 10]
        ))
    ])
    
    builder = DataBuilder(schema, config)
    data = builder.build(10)
    
    print("  生成10条订单数据:")
    for item in data:
        print(f"    订单ID: {item['order_id']}, 状态: {item['status']}, "
              f"支付方式: {item['payment_method']}, 优先级: {item['priority']}")


def example_enum_with_password():
    """枚举与密码策略组合示例"""
    print("\n" + "=" * 60)
    print("9. 枚举 + 密码策略组合")
    print("=" * 60)

    # 场景1：直接使用 enum 预定义密码列表
    print("  场景1：enum 作为预定义密码列表")
    schema = {"type": "object", "properties": {"admin_password": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "admin_password", "strategy": {
                "type": "enum",
                "choices": ["Admin@123", "Super@Pass", "Root#2024", "Secure!Token"]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(4)
    for item in data:
        print(f"    {item['admin_password']}")

    # 场景2：使用 concat 组合 enum（用户类型）+ password（动态生成密码）
    print("\n  场景2：concat 组合 enum + password（用户类型+动态密码）")
    schema = {"type": "object", "properties": {"credential": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "credential", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["admin", "user", "guest", "manager"]},
                    {"type": "password", "length": 10, "use_special": True}
                ],
                "separators": ["-"]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"    {item['credential']}")


def example_enum_with_email():
    """枚举与邮箱策略组合示例"""
    print("\n" + "=" * 60)
    print("10. 枚举 + 邮箱策略组合")
    print("=" * 60)

    # 场景1：直接使用 enum 预定义邮箱列表
    print("  场景1：enum 作为预定义邮箱列表")
    schema = {"type": "object", "properties": {"contact_email": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "contact_email", "strategy": {
                "type": "enum",
                "choices": [
                    "admin@company.com",
                    "support@company.com",
                    "sales@company.com",
                    "tech@company.com"
                ]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(4)
    for item in data:
        print(f"    {item['contact_email']}")

    # 场景2：使用 concat 组合 enum（部门）+ email（动态生成邮箱）
    print("\n  场景2：concat 组合 enum + email（部门前缀+动态邮箱）")
    schema = {"type": "object", "properties": {"dept_email": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "dept_email", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["hr", "it", "finance", "marketing"]},
                    {"type": "email", "email_type": "custom", "domains": ["company.com"]}
                ],
                "separators": ["."]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"    {item['dept_email']}")

    # 场景3：直接使用 email 策略生成随机类型邮箱
    print("\n  场景3：直接使用 email 策略生成随机邮箱")
    schema = {"type": "object", "properties": {"email": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "random"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"    随机类型邮箱: {item['email']}")


def example_enum_with_faker():
    """枚举与 Faker 策略组合示例"""
    print("\n" + "=" * 60)
    print("11. 枚举 + Faker 策略组合")
    print("=" * 60)

    # 场景：使用 concat 组合 enum（标题）+ faker（姓名）
    print("  场景：concat 组合 enum（职位）+ faker（姓名）")
    schema = {"type": "object", "properties": {"full_name": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "full_name", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["Mr.", "Ms.", "Mrs.", "Dr."]},
                    {"type": "faker", "method": "first_name"},
                    {"type": "faker", "method": "last_name"}
                ],
                "separators": [" ", " "]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"    {item['full_name']}")


def example_enum_with_datetime():
    """枚举与 DateTime 策略组合示例"""
    print("\n" + "=" * 60)
    print("12. 枚举 + DateTime 策略组合")
    print("=" * 60)

    # 场景：使用 concat 组合 enum（状态）+ datetime（时间戳）
    print("  场景：concat 组合 enum（订单状态）+ datetime（时间）")
    schema = {"type": "object", "properties": {"record": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "record", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["created", "updated", "deleted", "processed"]},
                    {"type": "datetime", "format": "%Y-%m-%d %H:%M:%S"}
                ],
                "separators": [" ["]
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"    {item['record']}")


if __name__ == "__main__":
    example_basics()
    example_with_weights()
    example_integer_enum()
    example_mixed_enum()
    example_enum_with_registry()
    example_enum_boundary_values()
    example_enum_invalid_values()
    example_real_world_scenario()
    example_enum_with_password()
    example_enum_with_email()
    example_enum_with_faker()
    example_enum_with_datetime()
