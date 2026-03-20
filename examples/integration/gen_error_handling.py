"""
错误处理和异常捕获示例

展示 DataBuilder 的异常处理方式。
"""
import json
from data_builder import DataBuilder
from data_builder.exceptions import StrategyError, FieldPathError


def example_schema_error():
    """Schema 相关错误"""
    print("=" * 50)
    print("Schema 错误处理")
    print("=" * 50)

    # 场景1: 循环引用导致错误
    print("\n1. 循环引用错误:")
    schema_with_cycle = {
        "definitions": {
            "A": {"$ref": "#/definitions/B"},
            "B": {"$ref": "#/definitions/A"}
        },
        "type": "object",
        "properties": {
            "data": {"$ref": "#/definitions/A"}
        }
    }

    try:
        builder = DataBuilder(schema_with_cycle)
        result = builder.build()
        print(f"生成成功: {result}")
    except Exception as e:
        print(f"捕获异常: {type(e).__name__}: {e}")

    # 场景2: 不支持的 format
    print("\n2. 无效 format 处理:")
    schema_invalid_format = {
        "type": "object",
        "properties": {
            "value": {"type": "string", "format": "unsupported-format"}
        }
    }

    try:
        builder = DataBuilder(schema_invalid_format)
        result = builder.build()
        print(f"生成成功: {result}")
    except Exception as e:
        print(f"捕获异常: {type(e).__name__}: {e}")


def example_strategy_error():
    """策略相关错误"""
    print("\n" + "=" * 50)
    print("策略错误处理")
    print("=" * 50)

    # 场景1: 空枚举
    print("\n1. 空枚举错误:")
    from data_builder import FieldPolicy, EnumStrategy

    try:
        strategy = EnumStrategy([])
        from data_builder import StrategyContext
        ctx = StrategyContext(field_path="test", field_schema={}, root_data={})
        result = strategy.generate(ctx)
        print(f"生成成功: {result}")
    except StrategyError as e:
        print(f"捕获 StrategyError: {e}")
    except Exception as e:
        print(f"捕获其他异常: {type(e).__name__}: {e}")

    # 场景2: ref 引用不存在路径
    print("\n2. ref 引用错误:")
    from data_builder import FieldPolicy, seq, ref

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        }
    }

    try:
        result = DataBuilder(
            schema,
            config=DataBuilder.config_from_dict({
                "policies": [
                    {"path": "id", "strategy": {"type": "sequence", "start": 1}},
                    {"path": "missing_ref", "strategy": {"type": "ref", "ref": "nonexistent"}}
                ]
            })
        ).build()
        print(f"生成成功: {result}")
    except FieldPathError as e:
        print(f"捕获 FieldPathError: {e}")
    except Exception as e:
        print(f"捕获其他异常: {type(e).__name__}: {e}")


def example_config_error():
    """配置相关错误"""
    print("\n" + "=" * 50)
    print("配置错误处理")
    print("=" * 50)

    # 场景1: 无效的 JSON Schema type
    print("\n1. 无效 JSON Schema type:")
    schema_invalid_type = {
        "type": "object",
        "properties": {
            "value": {"type": "invalid_type"}
        }
    }

    try:
        builder = DataBuilder(schema_invalid_type)
        result = builder.build(count=3)
        print(f"生成成功: {result}")
    except Exception as e:
        print(f"捕获异常: {type(e).__name__}: {e}")

    # 场景2: 空 schema
    print("\n2. 空 schema:")
    empty_schema = {}

    try:
        builder = DataBuilder(empty_schema)
        result = builder.build(count=3)
        print(f"生成成功: {result}")
    except Exception as e:
        print(f"捕获异常: {type(e).__name__}: {e}")


def example_graceful_degradation():
    """优雅降级处理"""
    print("\n" + "=" * 50)
    print("优雅降级处理")
    print("=" * 50)

    # 场景: 部分字段生成失败时，其他字段仍能生成
    print("\n部分字段错误时的优雅降级:")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"}
        }
    }

    builder = DataBuilder(schema)
    result = builder.build(count=5)
    print(f"生成结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_with_validation():
    """带验证的错误处理示例"""
    print("\n" + "=" * 50)
    print("带验证的错误处理示例")
    print("=" * 50)

    def safe_build(schema, count=1):
        """安全的构建函数"""
        try:
            builder = DataBuilder(schema)
            return builder.build(count=count)
        except StrategyError as e:
            print(f"策略错误: {e}")
            return None
        except FieldPathError as e:
            print(f"字段路径错误: {e}")
            return None
        except Exception as e:
            print(f"未知错误: {type(e).__name__}: {e}")
            return None

    # 测试不同的 schema
    schemas = [
        {"type": "object", "properties": {"id": {"type": "integer"}}},
        {"type": "object", "properties": {"invalid": {"type": "invalid"}}},
    ]

    for i, schema in enumerate(schemas, 1):
        print(f"\n测试 schema {i}:")
        result = safe_build(schema)
        if result:
            print(f"  成功: {result}")


if __name__ == "__main__":
    example_schema_error()
    example_strategy_error()
    example_config_error()
    example_graceful_degradation()
    example_with_validation()
