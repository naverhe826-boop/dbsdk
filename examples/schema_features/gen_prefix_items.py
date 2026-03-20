"""
prefixItems 示例：演示 JSON Schema prefixItems（元组验证）的数据生成。

包含以下示例：
- 基本 prefixItems：固定位置类型（如坐标元组）
- prefixItems + items：固定头部 + 自由尾部
- prefixItems + array_count：控制元素总数
- 严格元组：prefixItems + items:false
- 多个 prefixItems 字段：混合结构
"""

import json

from data_builder import DataBuilder


def example_basic_prefix_items():
    """基本 prefixItems 示例"""
    print("=" * 60)
    print("1. 基本 prefixItems — 坐标元组 [经度, 纬度, 海拔]")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "location": {
                "type": "array",
                "prefixItems": [
                    {"type": "number", "minimum": -180, "maximum": 180},   # 经度
                    {"type": "number", "minimum": -90, "maximum": 90},     # 纬度
                    {"type": "number", "minimum": 0, "maximum": 8848},     # 海拔
                ],
                "items": False,  # 不允许额外元素
            }
        },
    }

    results = DataBuilder(schema).build(count=3)
    print("坐标元组（经度, 纬度, 海拔）：")
    for r in results:
        loc = r["location"]
        print(f"  [{loc[0]:>8.2f}, {loc[1]:>7.2f}, {loc[2]:>7.2f}]")


def example_prefix_items_with_items():
    """prefixItems + items 示例"""
    print("\n" + "=" * 60)
    print("2. prefixItems + items — 日志记录 [时间戳, 级别, ...消息]")
    print("=" * 60)

    log_schema = {
        "type": "object",
        "properties": {
            "log_entry": {
                "type": "array",
                "prefixItems": [
                    {"type": "string", "const": "2024-01-15T10:30:00"},  # 固定时间戳
                    {"type": "string", "enum": ["INFO", "WARN", "ERROR"]},  # 日志级别
                ],
                "items": {"type": "string"},  # 后续为任意消息字符串
                "minItems": 4,
                "maxItems": 4,
            }
        },
    }

    results = DataBuilder(log_schema).build(count=3)
    print("日志条目 [时间戳, 级别, 消息...]：")
    for r in results:
        entry = r["log_entry"]
        print(f"  {entry}")


def example_prefix_items_with_array_count():
    """prefixItems + array_count 示例"""
    print("\n" + "=" * 60)
    print("3. prefixItems + array_count — 控制元素总数")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "record": {
                "type": "array",
                "prefixItems": [
                    {"type": "string", "const": "HEADER"},          # 第一个固定为标记
                    {"type": "integer", "minimum": 1, "maximum": 1},  # 第二个固定为版本号
                ],
                "items": {"type": "string"},  # 后续为数据字段
            }
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "record", "strategy": {"type": "array_count", "count": 5}}
        ]
    })

    result = DataBuilder(schema, config).build()
    print(f"总长度 5：前 2 个为 prefixItems，后 3 个为普通字符串")
    print(f"  {result['record']}")
    print(f"  [0]={result['record'][0]} (HEADER)")
    print(f"  [1]={result['record'][1]} (版本号)")
    print(f"  [2:]={result['record'][2:]} (数据)")


def example_strict_tuple():
    """严格元组示例"""
    print("\n" + "=" * 60)
    print("4. 严格元组 — RGB 颜色值")
    print("=" * 60)

    rgb_schema = {
        "type": "object",
        "properties": {
            "color": {
                "type": "array",
                "prefixItems": [
                    {"type": "integer", "minimum": 0, "maximum": 255},  # R
                    {"type": "integer", "minimum": 0, "maximum": 255},  # G
                    {"type": "integer", "minimum": 0, "maximum": 255},  # B
                ],
                "items": False,
            },
            "name": {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "name", "strategy": {"type": "enum", "choices": ["红色系", "绿色系", "蓝色系", "随机色"]}},
        ]
    })

    results = DataBuilder(rgb_schema, config).build(count=5)
    print("RGB 颜色（严格 3 元素元组）：")
    for r in results:
        c = r["color"]
        print(f"  {r['name']}: rgb({c[0]}, {c[1]}, {c[2]})")


def example_mixed_structure():
    """混合结构示例"""
    print("\n" + "=" * 60)
    print("5. 混合结构 — 包含多个元组字段的测试数据")
    print("=" * 60)

    test_schema = {
        "type": "object",
        "properties": {
            "test_id": {"type": "integer"},
            "input": {
                "type": "array",
                "prefixItems": [
                    {"type": "string", "const": "GET"},               # HTTP method
                    {"type": "string", "example": "/api/users"},      # path
                    {"type": "integer", "minimum": 200, "maximum": 200},  # expected status
                ],
                "items": False,
            },
            "expected_response": {
                "type": "array",
                "prefixItems": [
                    {"type": "boolean", "const": True},               # success
                    {"type": "string"},                                # message
                ],
                "items": False,
            },
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "test_id", "strategy": {"type": "range", "min": 1, "max": 999}},
            {"path": "input", "strategy": {"type": "array_count", "count": 3}},
        ]
    })

    results = DataBuilder(test_schema, config).build(count=3)
    print("测试用例（输入元组 + 期望响应元组）：")
    for r in results:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        print("-" * 40)


if __name__ == "__main__":
    print("prefixItems 示例")
    print("=" * 60)
    example_basic_prefix_items()
    example_prefix_items_with_items()
    example_prefix_items_with_array_count()
    example_strict_tuple()
    example_mixed_structure()
