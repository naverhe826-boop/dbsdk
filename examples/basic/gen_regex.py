"""
RegexStrategy 使用示例

展示 regex 策略的各种用法，包括：
- 基础用法（数字、字母、混合）
- 手机号、邮编等格式
- Cron 表达式
- 基类方法（values, boundary_values 等）
"""

import json
import re
from data_builder import DataBuilder


def example_basics():
    """基础用法示例"""
    print("=" * 60)
    print("1. 基础用法")
    print("=" * 60)

    schema = {"type": "object", "properties": {"value": {"type": "string"}}}

    # 纯数字：6位数字
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"\d{6}"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  \\d{6} (6位数字):")
    for item in data:
        print(f"    {item['value']}")

    # 大写字母：3个大写字母
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"[A-Z]{3}"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  [A-Z]{3} (3个大写字母):")
    for item in data:
        print(f"    {item['value']}")

    # 字母组合：5个字母（不区分大小写）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"[a-zA-Z]{5}"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  [a-zA-Z]{5} (5个字母):")
    for item in data:
        print(f"    {item['value']}")

    # 字母数字混合：4个字母或数字
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"[A-Za-z0-9]{4}"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  [A-Za-z0-9]{4} (4个字母或数字):")
    for item in data:
        print(f"    {item['value']}")


def example_formats():
    """格式示例"""
    print("\n" + "=" * 60)
    print("2. 常见格式")
    print("=" * 60)

    schema = {"type": "object", "properties": {"value": {"type": "string"}}}

    # 手机号格式：xxx-xxxx
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"^\d{3}-\d{4}$"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  手机号格式 (\\d{3}-\\d{4}):")
    for item in data:
        print(f"    {item['value']}")

    # 中国邮编：6位数字
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"^\d{6}$"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  邮编 (\\d{6}):")
    for item in data:
        print(f"    {item['value']}")

    # 有限字符集：只包含 a,b,c 的2字符
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "value", "strategy": {"type": "regex", "pattern": r"[abc]{2}"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  有限字符集 ([abc]{2}):")
    for item in data:
        print(f"    {item['value']}")


def example_cron():
    """Cron 表达式示例"""
    print("\n" + "=" * 60)
    print("3. Cron 表达式")
    print("=" * 60)

    # 单个 cron 表达式生成
    print("  单个表达式:")
    schema = {"type": "object", "properties": {"cron": {"type": "string"}}}

    cron_patterns = [
        (r"\* \* \* \* \*", "每分钟"),
        (r"0 \* \* \* \*", "每小时整点"),
        (r"0 0 \* \* \*", "每天午夜"),
        (r"0 0 \* \* 0", "每周日午夜"),
        (r"0 0 1 \* \*", "每月1日午夜"),
    ]

    for pattern, desc in cron_patterns:
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "cron", "strategy": {"type": "regex", "pattern": pattern}}
            ]
        })
        builder = DataBuilder(schema, config)
        data = builder.build(1)
        print(f"    {desc} ({pattern}): {data[0]['cron']}")

    # 批量生成 cron 数据
    print("\n  批量生成 cron 数据 (工作日定时任务):")
    schema = {
        "type": "object",
        "properties": {
            "minute": {"type": "string"},
            "hour": {"type": "string"},
            "day": {"type": "string"},
            "month": {"type": "string"},
            "weekday": {"type": "string"},
        }
    }

    # 字段正则说明:
    # minute: 0-59 分
    # hour: 0-23 时
    # day: 1-31 日
    # month: 1-12 月
    # weekday: 0-6 星期 (0=周日)
    
    # 分钟: [0-5]?\d 匹配 0-59
    minute_pattern = r"[0-5]?\d"
    # 小时: [01]?\d|2[0-3] 匹配 0-23
    hour_pattern = r"[01]?\d|2[0-3]"
    # 日期: [1-9]|[12]\d|3[01] 匹配 1-31
    day_pattern = r"[1-9]|[12]\d|3[01]"
    # 月份: 0?[1-9]|1[0-2] 匹配 1-12
    month_pattern = r"0?[1-9]|1[0-2]"
    # 星期: [0-6] 匹配 0-6
    weekday_pattern = r"[0-6]"

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "minute", "strategy": {"type": "regex", "pattern": minute_pattern}},
            {"path": "hour", "strategy": {"type": "regex", "pattern": hour_pattern}},
            {"path": "day", "strategy": {"type": "regex", "pattern": day_pattern}},
            {"path": "month", "strategy": {"type": "regex", "pattern": month_pattern}},
            {"path": "weekday", "strategy": {"type": "regex", "pattern": weekday_pattern}},
        ]
    })

    builder = DataBuilder(schema, config)
    data = builder.build(5)

    for i, item in enumerate(data, 1):
        cron_expr = f"{item['minute']} {item['hour']} {item['day']} {item['month']} {item['weekday']}"
        print(f"    任务{i}: {cron_expr}")

    # 完整 cron 表达式示例
    print("\n  生成完整的 cron 表达式字符串:")
    # 使用更精确的范围限制
    full_cron_pattern = r"([0-5]?\d)\s+([01]?\d|2[0-3])\s+([1-9]|[12]\d|3[01])\s+(0?[1-9]|1[0-2])\s+[0-6]"

    schema = {"type": "object", "properties": {"schedule": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "schedule", "strategy": {"type": "regex", "pattern": full_cron_pattern}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)

    for item in data:
        print(f"    {item['schedule']}")


def example_base_methods():
    """基类方法示例"""
    print("\n" + "=" * 60)
    print("4. 基类方法")
    print("=" * 60)

    # 需要直接使用策略类来测试
    from data_builder.strategies.value.string.regex import RegexStrategy

    # values: 可枚举正则
    print("  values(): 可枚举正则返回所有值")
    s = RegexStrategy(pattern=r"[a-c]{2}")
    vals = s.values()
    print(f"    [a-c]{{2}} 的所有值 ({len(vals)}个): {vals}")

    # values: 不可枚举（超过10000），返回None
    print("  values(): 不可枚举时返回 None")
    s = RegexStrategy(pattern=r"\d{5}")
    vals = s.values()
    print(f"    \\d{{5}} 的值: {vals}")

    # values: 无限匹配，返回None
    s = RegexStrategy(pattern=r"\d+")
    vals = s.values()
    print(f"    \\d+ 的值: {vals}")

    # boundary_values: 可枚举正则返回边界值
    print("  boundary_values(): 可枚举正则返回边界值")
    s = RegexStrategy(pattern=r"\d{2}")
    bounds = s.boundary_values()
    print(f"    \\d{{2}} 的边界值: {bounds}")

    # boundary_values: 不可枚举时返回None
    s = RegexStrategy(pattern=r"\d{5}")
    bounds = s.boundary_values()
    print(f"    \\d{{5}} 的边界值: {bounds}")

    # equivalence_classes: 每个值是一个单独的等价类
    print("  equivalence_classes(): 返回等价类")
    s = RegexStrategy(pattern=r"[ab]{2}")
    classes = s.equivalence_classes()
    print(f"    [ab]{{2}} 的等价类: {classes}")

    # invalid_values: 返回无效值
    print("  invalid_values(): 返回无效值测试用例")
    s = RegexStrategy(pattern=r"\d{3}")
    invalid = s.invalid_values()
    print(f"    \\d{{3}} 的无效值: {invalid}")


def example_with_databuilder():
    """与 DataBuilder 集成示例"""
    print("\n" + "=" * 60)
    print("5. 与 DataBuilder 集成")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "phone": {"type": "string"},
            "postal_code": {"type": "string"},
            "order_no": {"type": "string"},
        }
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "user_id", "strategy": {"type": "regex", "pattern": r"U\d{6}"}},
            {"path": "phone", "strategy": {"type": "regex", "pattern": r"1\d{2}-\d{4}"}},
            {"path": "postal_code", "strategy": {"type": "regex", "pattern": r"\d{6}"}},
            {"path": "order_no", "strategy": {"type": "regex", "pattern": r"ORD-[A-Z]{3}\d{4}"}},
        ]
    })

    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  生成数据:")
    for item in data:
        print(f"    {json.dumps(item, ensure_ascii=False)}")


if __name__ == "__main__":
    example_basics()
    example_formats()
    example_cron()
    example_base_methods()
    example_with_databuilder()
