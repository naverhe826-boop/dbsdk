"""
OpenAPI 模块 field_policies 策略使用示例。

展示如何在 OpenAPI 测试数据生成中使用各种策略类型。
"""

import json

from data_builder.openapi import APITestDataManager


def example_enum_strategy():
    """示例：使用 enum 策略覆盖字段"""
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "status": {"type": "string"},
                                        "role": {"type": "string"}
                                    },
                                    "required": ["name", "status"]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }
    
    manager = APITestDataManager(
        openapi_document=openapi_doc,
        generation_config={
            "generation_mode": "random",
            "count": 5,
            "field_policies": [
                # 使用 enum 策略限制 status 字段值
                {
                    "path": "status",
                    "strategy": {
                        "type": "enum",
                        "values": ["active", "inactive", "pending"]
                    }
                },
                # 使用 enum 策略限制 role 字段值
                {
                    "path": "role",
                    "strategy": {
                        "type": "enum",
                        "values": ["admin", "user", "guest"]
                    }
                }
            ]
        }
    )
    
    requests = manager.generate_for_endpoint("createUser")
    
    print("=== enum 策略示例 ===")
    print(f"生成了 {len(requests)} 条请求数据\n")
    
    for i, req in enumerate(requests[:3], 1):
        print(f"请求 {i}:")
        print(json.dumps(req.request_body, ensure_ascii=False, indent=2))
        print()


def example_range_strategy():
    """示例：使用 range 策略生成数值"""
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Product API", "version": "1.0.0"},
        "paths": {
            "/products": {
                "post": {
                    "operationId": "createProduct",
                    "summary": "Create a product",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "price": {"type": "number"},
                                        "quantity": {"type": "integer"},
                                        "discount": {"type": "number"}
                                    },
                                    "required": ["name", "price", "quantity"]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }
    
    manager = APITestDataManager(
        openapi_document=openapi_doc,
        generation_config={
            "generation_mode": "random",
            "count": 5,
            "field_policies": [
                # 使用 range 策略限制 price 范围
                {
                    "path": "price",
                    "strategy": {
                        "type": "range",
                        "min_val": 10.0,
                        "max_val": 1000.0,
                        "is_float": True,
                        "precision": 2
                    }
                },
                # 使用 range 策略限制 quantity 范围
                {
                    "path": "quantity",
                    "strategy": {
                        "type": "range",
                        "min_val": 1,
                        "max_val": 100
                    }
                },
                # 使用 range 策略限制 discount 范围
                {
                    "path": "discount",
                    "strategy": {
                        "type": "range",
                        "min_val": 0.0,
                        "max_val": 0.5,
                        "is_float": True,
                        "precision": 2
                    }
                }
            ]
        }
    )
    
    requests = manager.generate_for_endpoint("createProduct")
    
    print("=== range 策略示例 ===")
    print(f"生成了 {len(requests)} 条请求数据\n")
    
    for i, req in enumerate(requests[:3], 1):
        print(f"请求 {i}:")
        print(json.dumps(req.request_body, ensure_ascii=False, indent=2))
        print()


def example_random_string_strategy():
    """示例：使用 random_string 策略生成字符串"""
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Order API", "version": "1.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrder",
                    "summary": "Create an order",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "order_id": {"type": "string"},
                                        "customer_name": {"type": "string"},
                                        "product_code": {"type": "string"}
                                    },
                                    "required": ["order_id", "customer_name"]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }
    
    manager = APITestDataManager(
        openapi_document=openapi_doc,
        generation_config={
            "generation_mode": "random",
            "count": 5,
            "field_policies": [
                # 使用 random_string 策略生成固定长度的订单 ID
                {
                    "path": "order_id",
                    "strategy": {
                        "type": "random_string",
                        "length": 10
                    }
                },
                # 使用 random_string 策略生成固定长度的产品代码
                {
                    "path": "product_code",
                    "strategy": {
                        "type": "random_string",
                        "length": 8
                    }
                }
            ]
        }
    )
    
    requests = manager.generate_for_endpoint("createOrder")
    
    print("=== random_string 策略示例 ===")
    print(f"生成了 {len(requests)} 条请求数据\n")
    
    for i, req in enumerate(requests[:3], 1):
        print(f"请求 {i}:")
        print(json.dumps(req.request_body, ensure_ascii=False, indent=2))
        print()


def example_mixed_strategies():
    """示例：混合使用多种策略"""
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Task API", "version": "1.0.0"},
        "paths": {
            "/tasks": {
                "post": {
                    "operationId": "createTask",
                    "summary": "Create a task",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "task_id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "priority": {"type": "integer"},
                                        "status": {"type": "string"},
                                        "assignee": {"type": "string"}
                                    },
                                    "required": ["task_id", "title", "priority", "status"]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }
    
    manager = APITestDataManager(
        openapi_document=openapi_doc,
        generation_config={
            "generation_mode": "random",
            "count": 5,
            "field_policies": [
                # task_id: 固定长度的随机字符串
                {
                    "path": "task_id",
                    "strategy": {
                        "type": "random_string",
                        "length": 12
                    }
                },
                # priority: 整数范围
                {
                    "path": "priority",
                    "strategy": {
                        "type": "range",
                        "min_val": 1,
                        "max_val": 5
                    }
                },
                # status: 枚举值
                {
                    "path": "status",
                    "strategy": {
                        "type": "enum",
                        "values": ["todo", "in_progress", "done", "cancelled"]
                    }
                }
            ]
        }
    )
    
    requests = manager.generate_for_endpoint("createTask")
    
    print("=== 混合策略示例 ===")
    print(f"生成了 {len(requests)} 条请求数据\n")
    
    for i, req in enumerate(requests[:3], 1):
        print(f"请求 {i}:")
        print(json.dumps(req.request_body, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    example_enum_strategy()
    example_range_strategy()
    example_random_string_strategy()
    example_mixed_strategies()
