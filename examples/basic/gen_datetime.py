"""
DateTimeStrategy 使用示例

展示 datetime 策略的各种用法，包括：
- 基础用法
- anchor 关键字 (now/today/yesterday/week/month/year)
- offset 偏移量
- date_range / time_range
- specific_date / specific_time
- timezone 时区
"""

import json
from data_builder import DataBuilder


def example_basics():
    """基础用法示例"""
    print("=" * 60)
    print("1. 基础用法")
    print("=" * 60)

    # 默认：过去一年到当前时间
    schema = {"type": "object", "properties": {"timestamp": {"type": "string"}}}
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "timestamp", "strategy": {"type": "datetime"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  默认: {item['timestamp']}")

    # 指定日期范围
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "timestamp", "strategy": {"type": "datetime", "start": "2024-01-01", "end": "2024-12-31"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  指定范围: {item['timestamp']}")

    # 自定义格式
    formats = ["%Y-%m-%d", "%H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        config = DataBuilder.config_from_dict({
            "policies": [{"path": "date", "strategy": {"type": "datetime", "format": fmt}}]
        })
        builder = DataBuilder({"type": "object", "properties": {"date": {"type": "string"}}}, config)
        data = builder.build(1)
        print(f"  格式 {fmt}: {data[0]['date']}")


def example_anchor():
    """anchor 关键字示例"""
    print("\n" + "=" * 60)
    print("2. Anchor 关键字")
    print("=" * 60)

    anchors = ["now", "today", "yesterday", "week", "month", "year"]
    schema = {"type": "object", "properties": {"time": {"type": "string"}}}

    for anchor in anchors:
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "time", "strategy": {"type": "datetime", "anchor": anchor}},
            ]
        })
        builder = DataBuilder(schema, config)
        data = builder.build(1)
        print(f"  anchor='{anchor}': {data[0]['time']}")


def example_offset():
    """offset 偏移量示例"""
    print("\n" + "=" * 60)
    print("3. Offset 偏移量")
    print("=" * 60)

    offsets = [
        ("today", "-1d", "昨天"),
        ("today", "+1d", "明天"),
        ("now", "+2h", "2小时后"),
        ("today", "-1w", "一周前"),
        ("today", "-1M", "一个月前"),
        ("today", "+1d 2h 30m", "明天+2.5小时"),
    ]
    schema = {"type": "object", "properties": {"time": {"type": "string"}}}

    for anchor, offset, desc in offsets:
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "time", "strategy": {"type": "datetime", "anchor": anchor, "offset": offset}},
            ]
        })
        builder = DataBuilder(schema, config)
        data = builder.build(1)
        print(f"  {desc}: {data[0]['time']}")


def example_date_time_range():
    """date_range 和 time_range 示例"""
    print("\n" + "=" * 60)
    print("4. Date Range 和 Time Range")
    print("=" * 60)

    schema = {"type": "object", "properties": {"time": {"type": "string"}}}

    # date_range: 限制日期
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime", "date_range": "2024-01-01,2024-12-31"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  date_range: {item['time']}")

    # time_range: 限制时间（工作时间）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime", "time_range": "09:00:00,18:00:00"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  time_range: {item['time']}")

    # 组合: 特定日期 + 工作时间
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime",
                "date_range": "2024-03-15,2024-03-15",
                "time_range": "09:00:00,18:00:00"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  组合: {item['time']}")


def example_specific():
    """specific_date 和 specific_time 示例"""
    print("\n" + "=" * 60)
    print("5. 指定具体日期/时间")
    print("=" * 60)

    schema = {"type": "object", "properties": {"time": {"type": "string"}}}

    # 仅指定日期
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime", "specific_date": "2024-05-20"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  specific_date: {item['time']}")

    # 仅指定时间
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime", "specific_time": "12:00:00"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  specific_time: {item['time']}")

    # 同时指定日期和时间
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "time", "strategy": {"type": "datetime",
                "specific_date": "2024-05-20",
                "specific_time": "14:30:00"}},
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"  固定日期时间: {item['time']}")


def example_timezone():
    """timezone 时区示例"""
    print("\n" + "=" * 60)
    print("6. 时区支持")
    print("=" * 60)

    schema = {"type": "object", "properties": {"time": {"type": "string"}}}

    timezones = [
        ("UTC", "UTC"),
        ("Asia/Shanghai", "中国"),
        ("America/New_York", "纽约"),
        ("+08:00", "UTC+8"),
    ]

    for tz, desc in timezones:
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "time", "strategy": {"type": "datetime",
                    "anchor": "now",
                    "timezone": tz,
                    "format": "%Y-%m-%d %H:%M:%S"}},
            ]
        })
        builder = DataBuilder(schema, config)
        data = builder.build(1)
        print(f"  {desc} ({tz}): {data[0]['time']}")


def example_complete():
    """完整配置示例"""
    print("\n" + "=" * 60)
    print("7. 完整配置示例 - 订单数据")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "created_at": {"type": "string"},      # 下单时间
            "paid_at": {"type": "string"},         # 支付时间
            "shipped_at": {"type": "string"},      # 发货时间
            "delivered_at": {"type": "string"},    # 签收时间
            "expire_at": {"type": "string"},       # 过期时间
        }
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "order_id", "strategy": {"type": "sequence",
                "prefix": "ORD",
                "start": 1}},
            # 下单时间：今天
            {"path": "created_at", "strategy": {"type": "datetime",
                "anchor": "today",
                "timezone": "Asia/Shanghai",
                "format": "%Y-%m-%d %H:%M:%S"}},
            # 支付时间：下单后1-24小时内
            {"path": "paid_at", "strategy": {"type": "datetime",
                "anchor": "today",
                "offset": "+1h",
                "timezone": "Asia/Shanghai",
                "format": "%Y-%m-%d %H:%M:%S"}},
            # 发货时间：支付后1-3天
            {"path": "shipped_at", "strategy": {"type": "datetime",
                "anchor": "today",
                "offset": "+1d",
                "timezone": "Asia/Shanghai",
                "format": "%Y-%m-%d %H:%M:%S"}},
            # 签收时间：发货后3-7天
            {"path": "delivered_at", "strategy": {"type": "datetime",
                "anchor": "today",
                "offset": "+3d",
                "timezone": "Asia/Shanghai",
                "format": "%Y-%m-%d %H:%M:%S"}},
            # 过期时间：30天后
            {"path": "expire_at", "strategy": {"type": "datetime",
                "anchor": "now",
                "offset": "+30d",
                "timezone": "Asia/Shanghai",
                "format": "%Y-%m-%d %H:%M:%S"}},
        ]
    })

    builder = DataBuilder(schema, config)
    data = builder.build(2)
    for i, item in enumerate(data, 1):
        print(f"\n  订单 {i}:")
        for key, value in item.items():
            print(f"    {key}: {value}")


def example_from_config():
    """从配置字典加载示例"""
    print("\n" + "=" * 60)
    print("8. 从配置字典加载")
    print("=" * 60)

    config_dict = {
        "policies": [
            {"path": "created_at", "strategy": {"type": "datetime", "anchor": "today"}},
            {"path": "updated_at", "strategy": {"type": "datetime", "anchor": "now"}},
            {"path": "deleted_at", "strategy": {"type": "datetime", "anchor": "yesterday"}},
            {"path": "event_date", "strategy": {"type": "datetime", "date_range": "2024-01-01,2024-12-31"}},
            {"path": "appointment", "strategy": {"type": "datetime", "date_range": "2024-03-01,2024-03-31", "time_range": "09:00:00,18:00:00"}},
            {"path": "utc_time", "strategy": {"type": "datetime", "anchor": "now", "timezone": "UTC"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    schema = {
        "type": "object",
        "properties": {
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "deleted_at": {"type": "string"},
            "event_date": {"type": "string"},
            "appointment": {"type": "string"},
            "utc_time": {"type": "string"},
        }
    }

    builder = DataBuilder(schema, config)
    data = builder.build(2)

    for i, item in enumerate(data, 1):
        print(f"\n  数据 {i}:")
        for key, value in item.items():
            print(f"    {key}: {value}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DateTimeStrategy 使用示例")
    print("=" * 60)

    example_basics()
    example_anchor()
    example_offset()
    example_date_time_range()
    example_specific()
    example_timezone()
    example_complete()
    example_from_config()

    print("\n" + "=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)
