"""
递归树结构生成示例

本示例展示如何使用 max_depth 参数生成递归树结构数据。

递归结构常见于：
- 组织架构树
- 评论嵌套
- 文件系统目录
- 菜单树
"""

import json
from data_builder import DataBuilder


def example_schema1():
    """
    Schema 1: 标准树结构定义
    - 根节点是完整的对象定义
    - children 通过 $ref 引用自身
    """
    schema = {
        "$defs": {
            "Node": {
                "properties": {
                    "children": {
                        "items": {"$ref": "#/$defs/Node"},
                        "type": "array"
                    },
                    "data": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "type": "object"
            }
        },
        "properties": {
            "children": {
                "items": {"$ref": "#/$defs/Node"},
                "type": "array"
            },
            "data": {"anyOf": [{"type": "string"}, {"type": "null"}]}
        },
        "required": ["data", "children"],
        "title": "Node",
        "type": "object"
    }
    
    print("=" * 60)
    print("Schema 1: 标准树结构定义")
    print("=" * 60)
    
    # 测试不同的深度（使用字典配置）
    for depth in [2, 3, 5]:
        config_dict = {"max_depth": depth}
        builder = DataBuilder(schema, DataBuilder.config_from_dict(config_dict))
        result = builder.build()
        print(f"\nmax_depth={depth}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


def example_schema2():
    """
    Schema 2: 根节点直接使用 $ref
    - 整个 schema 就是一个 $ref 引用
    - 更简洁的定义方式
    """
    schema = {
        "$defs": {
            "Node": {
                "properties": {
                    "data": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "children": {
                        "items": {"$ref": "#/$defs/Node"},
                        "type": "array"
                    }
                },
                "type": "object"
            }
        },
        "$ref": "#/$defs/Node"
    }
    
    print("\n" + "=" * 60)
    print("Schema 2: 根节点直接使用 $ref")
    print("=" * 60)
    
    # 测试不同的深度（使用字典配置）
    for depth in [2, 3, 5]:
        config_dict = {"max_depth": depth}
        builder = DataBuilder(schema, DataBuilder.config_from_dict(config_dict))
        result = builder.build()
        print(f"\nmax_depth={depth}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


def example_default_behavior():
    """
    默认行为：max_depth=None 时检测到循环引用会抛出异常
    """
    from data_builder.exceptions import SchemaError
    
    schema = {
        "$defs": {
            "Node": {
                "properties": {
                    "data": {"type": "string"},
                    "children": {
                        "items": {"$ref": "#/$defs/Node"},
                        "type": "array"
                    }
                },
                "type": "object"
            }
        },
        "$ref": "#/$defs/Node"
    }
    
    print("\n" + "=" * 60)
    print("默认行为（max_depth=None）")
    print("=" * 60)
    
    try:
        # 不传配置，默认 max_depth=None
        builder = DataBuilder(schema)
        result = builder.build()
        print("错误：应该抛出异常但没有抛出")
    except SchemaError as e:
        print(f"正确行为：检测到循环引用，抛出 SchemaError")
        print(f"错误信息: {e}")


def example_organization():
    """
    复杂的组织架构树示例
    
    展示更真实的递归结构：
    - 每个部门有多个属性（名称、类型、预算、员工数）
    - 使用策略控制字段值生成
    - 展示深度控制的实际应用
    """
    schema = {
        "$defs": {
            "Department": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["总部", "分公司", "事业部", "部门", "小组"]
                    },
                    "budget": {"type": "number"},
                    "employee_count": {"type": "integer"},
                    "manager": {"type": "string"},
                    "children": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/Department"}
                    }
                },
                "required": ["id", "name", "type", "children"]
            }
        },
        "$ref": "#/$defs/Department"
    }
    
    print("\n" + "=" * 60)
    print("复杂组织架构示例")
    print("=" * 60)
    
    # 使用字典配置策略
    config_dict = {
        "max_depth": 4,
        "policies": [
            {
                "path": "type",
                "strategy": {
                    "type": "enum",
                    "values": ["总部", "分公司", "事业部", "部门", "小组"]
                }
            },
            {
                "path": "budget",
                "strategy": {
                    "type": "range",
                    "min": 100000,
                    "max": 10000000
                }
            },
            {
                "path": "employee_count",
                "strategy": {
                    "type": "range",
                    "min": 5,
                    "max": 500
                }
            },
        ]
    }
    
    # 测试不同深度
    for depth in [2, 3, 4]:
        config_dict["max_depth"] = depth
        builder = DataBuilder(schema, DataBuilder.config_from_dict(config_dict))
        result = builder.build()
        
        print(f"\n{'─' * 40}")
        print(f"max_depth={depth} 的组织架构:")
        print(f"{'─' * 40}")
        _print_organization(result, indent=0)
    
    # 展示统计功能
    print("\n" + "=" * 60)
    print("组织架构统计（max_depth=4）")
    print("=" * 60)
    
    config_dict["max_depth"] = 4
    builder = DataBuilder(schema, DataBuilder.config_from_dict(config_dict))
    result = builder.build()
    
    stats = _collect_stats(result)
    print(f"总部门数: {stats['total_depts']}")
    print(f"总员工数: {stats['total_employees']}")
    print(f"总预算: {stats['total_budget']:,.0f} 元")
    print(f"最大层级: {stats['max_level']}")
    print(f"部门类型分布: {stats['type_distribution']}")


def _print_organization(dept: dict, indent: int):
    """递归打印组织架构"""
    prefix = "  " * indent
    dept_type = dept.get("type") or "未知"
    name = dept.get("name") or "未命名"
    employees = dept.get("employee_count") or 0
    budget = dept.get("budget") or 0
    
    # 根据类型使用不同的显示符号
    symbols = {
        "总部": "🏢",
        "分公司": "🏛️",
        "事业部": "📋",
        "部门": "👥",
        "小组": "👤"
    }
    symbol = symbols.get(dept_type, "📁")
    
    print(f"{prefix}{symbol} {name} ({dept_type})")
    if employees > 0:
        print(f"{prefix}   👥 员工: {employees}人")
    if budget > 0:
        print(f"{prefix}   💰 预算: {budget:,.0f}元")
    
    children = dept.get("children") or []
    for child in children:
        _print_organization(child, indent + 1)


def _collect_stats(dept: dict, level: int = 1) -> dict:
    """递归收集组织架构统计信息"""
    stats = {
        "total_depts": 1,
        "total_employees": dept.get("employee_count") or 0,
        "total_budget": dept.get("budget") or 0,
        "max_level": level,
        "type_distribution": {dept.get("type") or "未知": 1}
    }
    
    for child in dept.get("children") or []:
        child_stats = _collect_stats(child, level + 1)
        stats["total_depts"] += child_stats["total_depts"]
        stats["total_employees"] += child_stats["total_employees"]
        stats["total_budget"] += child_stats["total_budget"]
        stats["max_level"] = max(stats["max_level"], child_stats["max_level"])
        
        # 合并类型分布
        for dept_type, count in child_stats["type_distribution"].items():
            stats["type_distribution"][dept_type] = \
                stats["type_distribution"].get(dept_type, 0) + count
    
    return stats


def example_from_dict():
    """
    通过字典配置创建（最简洁的方式）
    """
    schema = {
        "$defs": {
            "Category": {
                "properties": {
                    "name": {"type": "string"},
                    "subcategories": {
                        "items": {"$ref": "#/$defs/Category"},
                        "type": "array"
                    }
                },
                "type": "object"
            }
        },
        "$ref": "#/$defs/Category"
    }
    
    print("\n" + "=" * 60)
    print("通过字典配置创建")
    print("=" * 60)
    
    config_dict = {
        "max_depth": 3
    }
    
    builder = DataBuilder(schema, DataBuilder.config_from_dict(config_dict))
    result = builder.build()
    
    print(f"\nmax_depth={config_dict['max_depth']}:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    example_schema1()
    example_schema2()
    example_default_behavior()
    example_from_dict()
    example_organization()
