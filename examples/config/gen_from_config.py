"""
从配置文件加载字段策略示例。

支持格式：
- YAML 文件（.yaml, .yml）
- JSON 文件（.json）

特性：
- 策略注册表引用：通过策略类型名称引用
- 环境变量插值：${VAR_NAME} 或 ${VAR_NAME:-default}
- 自动类型推断：根据策略构造函数参数类型自动转换

包含以下示例：
- 从 YAML 文件加载
- 从 JSON 字符串加载
- 从字典加载（动态配置）
- 环境变量插值
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_builder import DataBuilder, BuilderConfig


def example_yaml_file():
    """从 YAML 文件加载示例"""
    print("=" * 60)
    print("方式1：从 YAML 文件加载")
    print("=" * 60)

    # 设置环境变量测试
    os.environ.setdefault("USER_ID_START", "5000")

    # Schema：订单
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "order_no": {"type": "string"},
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                },
            },
            "status": {"type": "string"},
            "type": {"type": "string"},
            "amount": {"type": "integer"},
            "created_at": {"type": "string"},
            "updated_by": {"type": "string"},
        },
    }

    config = BuilderConfig.from_file(os.path.join(os.path.dirname(__file__), "policy.yaml"))
    builder = DataBuilder(schema, config)
    results = builder.build()

    for r in results:
        print(f"ID: {r['id']}")
        print(f"  order_no: {r['order_no']}")
        print(f"  user.id: {r['user']['id']}")
        print(f"  user.name: {r['user']['name']}")
        print(f"  user.phone: {r['user']['phone']}")
        print(f"  status: {r['status']}")
        print(f"  amount: {r['amount']}")
        print(f"  created_at: {r['created_at']}")
        print(f"  updated_by: {r['updated_by']}")
        print("-" * 40)


def example_json_string():
    """从 JSON 字符串加载示例"""
    print("\n" + "=" * 60)
    print("方式2：从 JSON 字符串加载")
    print("=" * 60)

    json_config = json.dumps({
        "policies": [
            {
                "path": "id",
                "strategy": {
                    "type": "sequence",
                    "params": {
                        "start": 1,
                        "prefix": "TEST-"
                    }
                }
            },
            {
                "path": "name",
                "strategy": {
                    "type": "faker",
                    "method": "name"
                }
            },
            {
                "path": "status",
                "strategy": {
                    "type": "enum",
                    "values": ["active", "inactive"]
                }
            }
        ],
        "count": 2
    })

    json_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "status": {"type": "string"},
        }
    }

    config = BuilderConfig.from_dict(json.loads(json_config))
    builder = DataBuilder(json_schema, config)
    results = builder.build()

    for r in results:
        print(r)


def example_dict_config():
    """从字典加载（动态配置）示例"""
    print("\n" + "=" * 60)
    print("方式3：从字典加载（动态配置）")
    print("=" * 60)

    dict_config = {
        "policies": [
            {
                "path": "id",
                "strategy": "sequence",  # 简化写法
                "start": 100,
                "prefix": "DYN-"
            },
            {
                "path": "value",
                "strategy": {
                    "type": "range",
                    "min": 1,
                    "max": 100
                }
            }
        ]
    }

    dict_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "value": {"type": "integer"}
        }
    }

    config = BuilderConfig.from_dict(dict_config)
    builder = DataBuilder(dict_schema, config)
    results = builder.build(count=3)

    for r in results:
        print(r)


def example_env_vars():
    """环境变量插值示例"""
    print("\n" + "=" * 60)
    print("方式4：环境变量插值")
    print("=" * 60)

    # 设置环境变量
    os.environ["MY_START"] = "999"
    os.environ["MY_PREFIX"] = "ENV-"

    env_config = {
        "policies": [
            {
                "path": "id",
                "strategy": {
                    "type": "sequence",
                    "start": "${MY_START}",
                    "prefix": "${MY_PREFIX}"
                }
            }
        ]
    }

    env_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"}
        }
    }

    config = BuilderConfig.from_dict(env_config)
    builder = DataBuilder(env_schema, config)
    results = builder.build(count=2)

    print("环境变量 MY_START=999, MY_PREFIX=ENV-")
    for r in results:
        print(f"  id: {r['id']}")

    # 测试默认值
    os.environ.pop("NONEXISTENT_VAR", None)
    env_config_default = {
        "policies": [
            {
                "path": "id",
                "strategy": {
                    "type": "sequence",
                    "start": "${NONEXISTENT_VAR:-2000}",
                    "prefix": "DEFAULT-"
                }
            }
        ]
    }

    config = BuilderConfig.from_dict(env_config_default)
    builder = DataBuilder(env_schema, config)
    results = builder.build(count=1)

    print("\n不存在的环境变量，使用默认值 ${NONEXISTENT_VAR:-2000}:")
    for r in results:
        print(f"  id: {r['id']}")


if __name__ == "__main__":
    print("从配置文件加载示例")
    print("=" * 60)
    example_yaml_file()
    example_json_string()
    example_dict_config()
    example_env_vars()
