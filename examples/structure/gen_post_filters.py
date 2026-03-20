"""
后置过滤器示例：演示 limit/deduplicate/constraint_filter/tag_rows 在 DataBuilder 中的使用。

包含以下示例：
- example_limit：限制结果数量
- example_deduplicate：按指定字段去重
- example_constraint_filter：条件过滤
- example_tag_rows：为每行添加标记
- example_combined_filters：组合使用多个过滤器
"""

import json

from data_builder import DataBuilder


def example_limit():
    """limit 示例 - 限制结果数量"""
    print("=" * 60)
    print("1. limit — 限制结果数量")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            {"path": "name", "strategy": {"type": "faker", "method": "name"}},
        ],
        "post_filters": [
            {"type": "limit", "max_count": 3}
        ]
    })

    results = DataBuilder(schema, config).build(count=10)
    print(f"生成 10 条数据，但 post_filters limit(3) 限制只输出 3 条：")
    print(f"实际结果数量: {len(results)}")
    for r in results:
        print(f"  {r}")


def example_deduplicate():
    """deduplicate 示例 - 按指定字段去重"""
    print("\n" + "=" * 60)
    print("2. deduplicate — 按指定字段去重")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "name": {"type": "string"},
        },
    }

    # 多次生成相同 category 的数据，然后按 category 去重
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "category", "strategy": {"type": "enum", "values": ["A", "B", "C"]}},
            {"path": "name", "strategy": {"type": "faker", "method": "name"}},
        ],
        "post_filters": [
            {"type": "deduplicate", "key_fields": ["category"]}
        ]
    })

    results = DataBuilder(schema, config).build(count=20)
    print(f"生成 20 条数据，按 category 去重后保留 {len(results)} 条：")
    print(f"去重后的 categories: {[r['category'] for r in results]}")
    for r in results:
        print(f"  {r}")


def example_constraint_filter():
    """constraint_filter 示例 - 条件过滤"""
    print("\n" + "=" * 60)
    print("3. constraint_filter — 条件过滤")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "status": {"type": "string"},
            "score": {"type": "integer"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            {"path": "status", "strategy": {"type": "enum", "values": ["active", "inactive", "pending"]}},
            {"path": "score", "strategy": {"type": "range", "min": 0, "max": 100}},
        ],
        "post_filters": [
            # 过滤条件：只保留 status=active 且 score>=60 的记录
            {"type": "constraint_filter", "predicate": "lambda row: row.get('status') == 'active' and row.get('score', 0) >= 60"}
        ]
    })

    results = DataBuilder(schema, config).build(count=20)
    print(f"生成 20 条数据，filter 过滤后保留 {len(results)} 条（status=active 且 score>=60）：")
    for r in results:
        print(f"  {r}")


def example_tag_rows():
    """tag_rows 示例 - 为每行添加标记"""
    print("\n" + "=" * 60)
    print("4. tag_rows — 为每行添加标记")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
        },
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            {"path": "name", "strategy": {"type": "faker", "method": "name"}},
        ],
        "post_filters": [
            {"type": "tag_rows", "tag_field": "source", "tag_value": "generated"}
        ]
    })

    results = DataBuilder(schema, config).build(count=3)
    print("为每条记录添加 source=generated 标记：")
    for r in results:
        print(f"  {r}")


def example_combined_filters():
    """combined_filters 示例 - 组合使用多个过滤器"""
    print("\n" + "=" * 60)
    print("5. combined_filters — 组合使用多个过滤器")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "status": {"type": "string"},
            "name": {"type": "string"},
        },
    }

    # 组合使用多个过滤器：
    # 1. 先按 category 去重
    # 2. 过滤 status=active
    # 3. 限制最多 5 条
    # 4. 添加标记
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "category", "strategy": {"type": "enum", "values": ["A", "B", "C", "D", "E"]}},
            {"path": "status", "strategy": {"type": "enum", "values": ["active", "inactive"]}},
            {"path": "name", "strategy": {"type": "faker", "method": "name"}},
        ],
        "post_filters": [
            {"type": "deduplicate", "key_fields": ["category"]},
            {"type": "constraint_filter", "predicate": "lambda row: row.get('status') == 'active'"},
            {"type": "limit", "max_count": 5},
            {"type": "tag_rows", "tag_field": "batch", "tag_value": "filtered"}
        ]
    })

    results = DataBuilder(schema, config).build(count=50)
    print(f"生成 50 条数据，组合过滤后保留 {len(results)} 条：")
    print("过滤流程：deduplicate(category) -> constraint(status=active) -> limit(5) -> tag_rows")
    for r in results:
        print(f"  {r}")


if __name__ == "__main__":
    example_limit()
    example_deduplicate()
    example_constraint_filter()
    example_tag_rows()
    example_combined_filters()
