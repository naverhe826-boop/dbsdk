"""
联合类型（Union Type）和 Nullable 关键字示例

演示如何使用 union_type_priority 配置和 nullable 关键字生成测试数据。
"""

from data_builder import DataBuilder


def example_union_type_priority():
    """示例 1：联合类型优先级配置"""
    print("=" * 60)
    print("示例 1：联合类型优先级配置")
    print("=" * 60)
    
    schema = {
        "type": ["string", "integer", "number"],
        "string": {"minLength": 5, "maxLength": 10}
    }
    
    # 不配置优先级，随机选择
    builder1 = DataBuilder(schema)
    results1 = [builder1.build() for _ in range(5)]
    print(f"无优先级：{results1}")
    print(f"类型：{[type(r).__name__ for r in results1]}")
    print()
    
    # 配置优先级，优先选择 string
    builder2 = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict(
            {"union_type_priority": ["string", "integer", "number"]}
        )
    )
    results2 = [builder2.build() for _ in range(5)]
    print(f"优先级 [string, integer, number]：{results2}")
    print(f"类型：{[type(r).__name__ for r in results2]}")
    print()


def example_nullable_keyword():
    """示例 2：nullable 关键字处理"""
    print("=" * 60)
    print("示例 2：nullable 关键字处理")
    print("=" * 60)
    
    schema = {
        "type": "string",
        "nullable": True,
        "minLength": 3
    }
    
    # null_probability 为 0，不生成 null
    builder1 = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict(
            {"null_probability": 0.0}
        )
    )
    results1 = [builder1.build() for _ in range(5)]
    print(f"null_probability=0.0：{results1}")
    print()
    
    # null_probability 为 0.5，可能生成 null
    builder2 = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict(
            {"null_probability": 0.5}
        )
    )
    results2 = [builder2.build() for _ in range(10)]
    print(f"null_probability=0.5：{results2}")
    print(f"包含 null：{sum(1 for r in results2 if r is None)}")
    print()


def example_union_type_with_null():
    """示例 3：联合类型包含 null"""
    print("=" * 60)
    print("示例 3：联合类型包含 null")
    print("=" * 60)
    
    schema = {
        "type": ["string", "null"],
        "minLength": 3
    }
    
    # 无 null 概率，不生成 null
    builder1 = DataBuilder(schema)
    results1 = [builder1.build() for _ in range(5)]
    print(f"无 null_probability：{results1}")
    print()
    
    # 设置 null 概率
    builder2 = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict(
            {"null_probability": 0.3}
        )
    )
    results2 = [builder2.build() for _ in range(10)]
    print(f"null_probability=0.3：{results2}")
    print(f"包含 null：{sum(1 for r in results2 if r is None)}")
    print()


def example_nested_union_type():
    """示例 4：嵌套对象中的联合类型"""
    print("=" * 60)
    print("示例 4：嵌套对象中的联合类型")
    print("=" * 60)
    
    schema = {
        "type": "object",
        "properties": {
            "field1": {
                "type": ["string", "integer"]
            },
            "field2": {
                "type": ["number", "boolean"]
            }
        }
    }
    
    # 配置优先级
    builder = DataBuilder(
        schema,
        config=DataBuilder.config_from_dict(
            {"union_type_priority": ["string", "number"]}
        )
    )
    
    results = [builder.build() for _ in range(3)]
    for i, result in enumerate(results, 1):
        print(f"数据 {i}：")
        print(f"  field1 ({type(result['field1']).__name__}): {result['field1']}")
        print(f"  field2 ({type(result['field2']).__name__}): {result['field2']}")
    print()


def example_type_inference():
    """示例 5：从 enum/const 推导类型"""
    print("=" * 60)
    print("示例 5：从 enum/const 推导类型")
    print("=" * 60)
    
    # 从 enum 推导类型
    schema1 = {
        "enum": [1, 2, 3, 4, 5],
        "not": {"enum": [1, 2, 3]}
    }
    
    builder1 = DataBuilder({"type": "object", "properties": {"v": schema1}})
    result1 = builder1.build()
    print(f"从 enum 推导：{result1}")
    print(f"类型：{type(result1['v']).__name__}")
    print()
    
    # 从 const 推导类型
    schema2 = {
        "const": "example_value"
    }
    
    builder2 = DataBuilder(schema2)
    result2 = builder2.build()
    print(f"从 const 推导：{result2}")
    print(f"类型：{type(result2).__name__}")
    print()


if __name__ == "__main__":
    example_union_type_priority()
    example_nullable_keyword()
    example_union_type_with_null()
    example_nested_union_type()
    example_type_inference()
    
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
