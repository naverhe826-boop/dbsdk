"""
PasswordStrategy 使用示例

展示 password 策略的各种用法，包括：
- 基础用法（默认参数）
- 自定义长度和字符类型
- 通过配置创建（使用 StrategyRegistry）
- 结合 FieldPolicy 使用
"""

import json
from data_builder import DataBuilder


def example_basics():
    """基础用法示例"""
    print("=" * 60)
    print("1. 基础用法（默认参数）")
    print("=" * 60)

    # 需要直接使用策略类来测试
    from data_builder.strategies.value.string.password import PasswordStrategy

    schema = {"type": "object", "properties": {"password": {"type": "string"}}}

    # 默认：12位，包含数字、大写字母、小写字母、特殊字符
    strategy = PasswordStrategy()
    password = strategy.generate(None)
    print(f"  默认密码（12位，含所有字符类型）: {password}")

    # 生成多个
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "password", "strategy": {"type": "password"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  生成3个密码:")
    for item in data:
        print(f"    {item['password']}")


def example_custom_length():
    """自定义长度和字符类型示例"""
    print("\n" + "=" * 60)
    print("2. 自定义长度和字符类型")
    print("=" * 60)

    schema = {"type": "object", "properties": {"password": {"type": "string"}}}

    # 16位密码，仅包含数字和大写字母
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "password", "strategy": {"type": "password", "length": 16, "use_digits": True, "use_uppercase": True, "use_lowercase": False, "use_special": False}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  16位，仅数字和大写字母:")
    for item in data:
        print(f"    {item['password']}")

    # 8位密码，仅小写字母（简单密码）
    config2 = DataBuilder.config_from_dict({
        "policies": [
            {"path": "password", "strategy": {"type": "password", "length": 8, "use_digits": False, "use_uppercase": False, "use_lowercase": True, "use_special": False}}
        ]
    })
    builder2 = DataBuilder(schema, config2)
    data2 = builder2.build(3)
    print("  8位，仅小写字母:")
    for item in data2:
        print(f"    {item['password']}")

    # 仅特殊字符（用于测试）
    config3 = DataBuilder.config_from_dict({
        "policies": [
            {"path": "password", "strategy": {"type": "password", "length": 12, "use_special": True, "use_digits": False, "use_uppercase": False, "use_lowercase": False}}
        ]
    })
    builder3 = DataBuilder(schema, config3)
    data3 = builder3.build(3)
    print("  12位，仅特殊字符:")
    for item in data3:
        print(f"    {item['password']}")


def example_custom_special_chars():
    """自定义特殊字符示例"""
    print("\n" + "=" * 60)
    print("3. 自定义特殊字符")
    print("=" * 60)

    schema = {"type": "object", "properties": {"password": {"type": "string"}}}

    # 仅使用 !#$% 四个特殊字符
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "password", "strategy": {"type": "password", "length": 12, "use_digits": False, "use_uppercase": False, "use_lowercase": False, "use_special": True, "special_chars": "!#$%"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  自定义特殊字符 (!#$%):")
    for item in data:
        print(f"    {item['password']}")


def example_via_registry():
    """通过配置创建示例（使用 config_from_dict）"""
    print("\n" + "=" * 60)
    print("4. 通过配置创建（使用 config_from_dict）")
    print("=" * 60)

    # 通过字典配置创建策略
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "password", "strategy": {"type": "password", "length": 12}}]
    })
    strategy = config.policies[0].strategy
    password = strategy.generate(None)
    print(f"  12位密码: {password}")

    # 通过字典配置创建策略（仅数字和大写）
    config2 = DataBuilder.config_from_dict({
        "policies": [{"path": "password", "strategy": {"type": "password", "length": 16, "use_special": False}}]
    })
    strategy2 = config2.policies[0].strategy
    password2 = strategy2.generate(None)
    print(f"  16位（无特殊字符）: {password2}")

    # 边界值测试
    config_min = DataBuilder.config_from_dict({
        "policies": [{"path": "password", "strategy": {"type": "password", "length": 8}}]
    })
    strategy_min = config_min.policies[0].strategy
    print(f"  最小长度 8 位: {strategy_min.generate(None)}")

    config_max = DataBuilder.config_from_dict({
        "policies": [{"path": "password", "strategy": {"type": "password", "length": 32}}]
    })
    strategy_max = config_max.policies[0].strategy
    print(f"  最大长度 32 位: {strategy_max.generate(None)}")


def example_with_field_policy():
    """结合 FieldPolicy 使用示例"""
    print("\n" + "=" * 60)
    print("5. 结合 FieldPolicy 使用")
    print("=" * 60)

    from data_builder import BuilderConfig, FieldPolicy
    from data_builder.strategies.value.string.password import PasswordStrategy
    from data_builder.strategies.basic.fixed import FixedStrategy

    # 完整用户数据示例，包含多种密码策略
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
            "pin": {"type": "string"},
            "secure_token": {"type": "string"}
        }
    }

    # 复杂策略配置
    policies = [
        FieldPolicy("username", FixedStrategy("zhangsan")),  # 固定用户名
        FieldPolicy("password", PasswordStrategy(length=16)),  # 16位强密码
        FieldPolicy("pin", PasswordStrategy(length=8, use_digits=True, use_uppercase=False,
                                             use_lowercase=False, use_special=False)),  # 8位数字 PIN
        FieldPolicy("secure_token", PasswordStrategy(length=32, use_special=True))  # 32位安全令牌
    ]

    config = BuilderConfig(policies=policies)
    builder = DataBuilder(schema, config)
    data = builder.build(3)

    print("  生成3条用户数据:")
    for item in data:
        print(f"    用户名: {item['username']}")
        print(f"    密码: {item['password']}")
        print(f"    PIN: {item['pin']}")
        print(f"    令牌: {item['secure_token']}")
        print()


def example_boundary_values():
    """边界值方法示例"""
    print("\n" + "=" * 60)
    print("6. 边界值和等价类方法")
    print("=" * 60)

    # 需要直接使用策略类来测试
    from data_builder.strategies.value.string.password import PasswordStrategy

    strategy = PasswordStrategy()

    # boundary_values: 返回最小/最大边界
    boundaries = strategy.boundary_values()
    print(f"  边界值: {[len(b) for b in boundaries]}")
    print(f"    最小边界 (8位): {boundaries[0]}")
    print(f"    最大边界 (32位): {boundaries[1]}")

    # equivalence_classes: 按字符类型组合分类
    classes = strategy.equivalence_classes()
    print(f"  等价类数量: {len(classes)}")
    for i, cls in enumerate(classes):
        print(f"    类别 {i+1}: {cls[0][:20]}...")


def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("7. 错误处理")
    print("=" * 60)

    # 需要直接使用策略类来测试错误处理
    from data_builder.strategies.value.string.password import PasswordStrategy
    from data_builder.exceptions import StrategyError

    # 长度太短
    try:
        PasswordStrategy(length=7)
    except StrategyError as e:
        print(f"  长度太短 (7): {e}")

    # 长度太长
    try:
        PasswordStrategy(length=33)
    except StrategyError as e:
        print(f"  长度太长 (33): {e}")

    # 所有字符类型关闭
    try:
        PasswordStrategy(
            length=12,
            use_digits=False,
            use_uppercase=False,
            use_lowercase=False,
            use_special=False
        )
    except StrategyError as e:
        print(f"  所有字符类型关闭: {e}")


if __name__ == "__main__":
    example_basics()
    example_custom_length()
    example_custom_special_chars()
    example_via_registry()
    example_with_field_policy()
    example_boundary_values()
    example_error_handling()
