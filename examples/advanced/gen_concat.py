"""
ConcatStrategy 使用示例

展示 concat 策略的各种用法，包括：
- 基础用法：多个策略值按顺序连接
- separators：自定义分隔符
- 字典配置：使用配置字典形式定义子策略
- 与其他策略组合：如 enum + random_string
- values() 方法：获取所有可枚举的组合值
"""

import json
from data_builder import DataBuilder


def generate_git_short_commit_id(ctx):
    """生成 git commit id 前8位（十六进制）"""
    import secrets
    return secrets.token_hex(4)  # 4字节 = 8位十六进制字符


def example_basics():
    """基础用法示例"""
    print("=" * 60)
    print("1. 基础用法：多个策略值按顺序连接")
    print("=" * 60)

    # 使用 ConcatStrategy 直接创建
    # 连接：前缀 + 随机字符串
    schema = {"type": "object", "properties": {"code": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "code", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["PRE", "DEV", "TEST"]},
                    {"type": "random_string", "length": 4, "charset": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
                ],
                "separators": ["-"]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"  {item['code']}")

    # 不使用分隔符
    print("\n  不使用分隔符:")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "code", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["User", "Order", "Product"]},
                    {"type": "random_string", "length": 3, "charset": "0123456789"},
                ]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  {item['code']}")


def example_separators():
    """分隔符示例"""
    print("\n" + "=" * 60)
    print("2. 分隔符用法")
    print("=" * 60)

    # 单个分隔符复用于所有连接位置
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "name", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "faker", "method": "first_name"},
                    {"type": "faker", "method": "last_name"},
                    {"type": "faker", "method": "last_name"},
                ],
                "separators": [" "]  # 空格分隔所有部分
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  单个分隔符: {item['name']}")

    # 多个分隔符
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "name", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "faker", "method": "first_name"},
                    {"type": "faker", "method": "last_name"},
                    {"type": "faker", "method": "last_name"},
                ],
                "separators": [" (", ") "]  # 不同位置使用不同分隔符
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  多个分隔符: {item['name']}")


def example_dict_config():
    """字典配置示例"""
    print("\n" + "=" * 60)
    print("3. 字典配置形式")
    print("=" * 60)

    # 使用字典配置定义子策略（需要通过 Registry）
    schema = {"type": "object", "properties": {"id": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "id", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["US", "CN", "JP"]},
                    {"type": "random_string", "length": 3, "charset": "0123456789"},
                ],
                "separators": ["-"]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    for item in data:
        print(f"  字典配置: {item['id']}")


def example_values():
    """values() 方法示例：获取所有可枚举的组合值"""
    print("\n" + "=" * 60)
    print("4. values() 方法：获取所有可枚举的组合值")
    print("=" * 60)

    # 需要直接使用策略类来测试 values()
    from data_builder.strategies.value.advanced.concat import ConcatStrategy
    from data_builder.strategies.value.enum import EnumStrategy
    from data_builder.strategies.value.string import RandomStringStrategy

    # 创建可枚举的 ConcatStrategy
    concat = ConcatStrategy(
        strategies=[
            EnumStrategy(choices=["A", "B"]),
            EnumStrategy(choices=["1", "2", "3"]),
        ],
        separators=["-"]
    )

    values = concat.values()
    print(f"  所有组合值: {values}")
    print(f"  组合数量: {len(values)}")

    # 混合可枚举和不可枚举的子策略
    print("\n  混合不可枚举策略:")
    concat2 = ConcatStrategy(
        strategies=[
            EnumStrategy(choices=["P1", "P2"]),
            RandomStringStrategy(length=3, charset="ABC"),  # 可枚举: 3^3=27
        ]
    )
    values2 = concat2.values()
    print(f"  所有组合值: {values2}")
    print(f"  组合数量: {len(values2)}")

    # 包含不可枚举策略（如 faker）
    print("\n  包含不可枚举策略:")
    from data_builder.strategies.value.external import FakerStrategy
    concat3 = ConcatStrategy(
        strategies=[
            FakerStrategy(method="name"),
            EnumStrategy(choices=["-V1", "-V2"]),
        ]
    )
    values3 = concat3.values()
    print(f"  values() 返回: {values3} (因为 faker 不可枚举)")


def example_practical():
    """实际应用示例"""
    print("\n" + "=" * 60)
    print("5. 实际应用示例")
    print("=" * 60)

    # 示例1：生成订单号
    schema = {"type": "object", "properties": {"order_no": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "order_no", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["ORD", "REF", "RET"]},
                    {"type": "random_string", "length": 8, "charset": "0123456789"},
                ],
                "separators": ["-"]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  订单号:")
    for item in data:
        print(f"    {item['order_no']}")

    # 示例2：生成用户名（名字+数字后缀）
    schema = {"type": "object", "properties": {"username": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "username", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "faker", "method": "user_name"},
                    {"type": "enum", "choices": ["", "1", "2", "3"]},
                ]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("\n  用户名:")
    for item in data:
        print(f"    {item['username']}")

    # 示例3：生成文件名（名称 + 扩展名）
    # 注意：扩展名已包含点号，不需要额外的分隔符
    schema = {"type": "object", "properties": {"filename": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "filename", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "random_string", "length": 6, "charset": "abcdefghijklmnopqrstuvwxyz"},
                    {"type": "enum", "choices": [".txt", ".pdf", ".doc", ".md"]},
                ]
                # 不需要分隔符，因为扩展名已包含点号
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("\n  文件名:")
    for item in data:
        print(f"    {item['filename']}")

    # 示例4：生成工号（姓名 + 5位数字）
    schema = {"type": "object", "properties": {"employee_id": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "employee_id", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "faker", "method": "name"},
                    {"type": "random_string", "length": 5, "charset": "0123456789"},
                ]
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("\n  工号 (姓名+5位数字):")
    for item in data:
        print(f"    {item['employee_id']}")

    # 示例5：生成git分支名（feat-xxx.1.0.0-xxx）
    # 注意：callable 策略需要直接使用 Strategy 类，dict 配置不支持函数引用
    # 这里使用简化版本演示
    schema = {"type": "object", "properties": {"branch_name": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "branch_name", "strategy": {
                "type": "concat",
                "strategies": [
                    {"type": "enum", "choices": ["feat", "fix", "refactor", "docs"]},
                    {"type": "random_string", "length": 8, "charset": "abcdefghijklmnopqrstuvwxyz"},
                    {"type": "enum", "choices": ["1.0.0"]},
                ],
                "separators": ["-", "-"]  # feat-xxx-1.0.0 格式（简化版）
            }},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("\n  Git分支名 (feat-xxx-1.0.0):")
    for item in data:
        print(f"    {item['branch_name']}")


def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("6. 错误处理示例")
    print("=" * 60)

    # 需要直接使用策略类来测试错误处理
    from data_builder.strategies.value.advanced.concat import ConcatStrategy
    from data_builder.strategies.value.enum import EnumStrategy

    # 空的 strategies 列表
    try:
        ConcatStrategy(strategies=[])
    except Exception as e:
        print(f"  空 strategies 列表: {type(e).__name__}: {e}")

    # separators 数量不匹配
    try:
        ConcatStrategy(
            strategies=[
                EnumStrategy(choices=["A"]),
                EnumStrategy(choices=["B"]),
                EnumStrategy(choices=["C"]),
            ],
            separators=["-", "-", "-", "-"]  # 3个策略只需要2个分隔符
        )
    except Exception as e:
        print(f"  separators 数量不匹配: {type(e).__name__}: {e}")

    # 非 string 类型的字段
    from data_builder.strategies.basic.base import StrategyContext
    concat = ConcatStrategy(
        strategies=[
            EnumStrategy(choices=["a"]),
        ]
    )
    try:
        ctx = StrategyContext(field_path="test", field_schema={"type": "integer"})
        concat.generate(ctx)
    except Exception as e:
        print(f"  非 string 类型字段: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basics()
    example_separators()
    example_dict_config()
    example_values()
    example_practical()
    example_error_handling()
