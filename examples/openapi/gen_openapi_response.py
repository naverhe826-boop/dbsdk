"""
OpenAPI 响应 Mock 数据生成示例。

演示如何使用响应数据生成器生成 Mock 响应数据。
"""

import json
from pathlib import Path

from data_builder.openapi import APITestDataManager


def main():
    """响应 Mock 生成示例"""
    print("=" * 70)
    print("OpenAPI 响应 Mock 数据生成示例")
    print("=" * 70)

    # 1. 加载 OpenAPI 文档
    print("\n1️⃣  加载 OpenAPI 文档")
    print("-" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return

    manager = APITestDataManager(openapi_document=api_doc_path)
    
    summary = manager.summary()
    print(f"✅ 文档加载成功")
    print(f"   OpenAPI 版本: {summary['openapi_version']}")
    print(f"   端点总数: {summary['total_endpoints']}")

    # 2. 配置响应生成器
    print("\n2️⃣  配置响应生成器")
    print("-" * 70)
    
    response_config = {
        "include_headers": True,      # 生成响应头
        "count": 1,                   # 每个响应生成 1 条数据
    }
    
    manager.configure_response_generator(response_config)
    print(f"✅ 响应生成器配置完成")
    print(f"   包含响应头: {response_config['include_headers']}")

    # 3. 为单个端点生成所有响应
    print("\n3️⃣  为单个端点生成所有响应")
    print("-" * 70)
    
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        print(f"\n端点: {endpoint.operation_id}")
        print(f"  路径: {endpoint.path}")
        print(f"  方法: {endpoint.method.value.upper()}")
        
        # 查看端点定义的响应
        if endpoint.responses:
            print(f"\n  定义了 {len(endpoint.responses)} 个响应：")
            for resp in endpoint.responses:
                print(f"    - {resp.status_code}: {resp.description or '无描述'}")
        
        # 生成所有响应
        responses = manager.generate_response_for_endpoint(endpoint.operation_id)
        
        print(f"\n✅ 生成了 {len(responses)} 个响应数据：")
        for i, resp in enumerate(responses, 1):
            print(f"\n  响应 {i}:")
            print(f"    状态码: {resp.status_code}")
            print(f"    来自示例: {resp.metadata.get('from_example', False)}")
            
            if resp.response_body:
                body_str = json.dumps(resp.response_body, ensure_ascii=False)
                if len(body_str) > 100:
                    body_str = body_str[:100] + "..."
                print(f"    响应体: {body_str}")
            
            if resp.response_headers:
                print(f"    响应头: {list(resp.response_headers.keys())}")

    # 4. 生成指定状态码的响应
    print("\n4️⃣  生成指定状态码的响应")
    print("-" * 70)
    
    if endpoints:
        # 只生成成功响应（2xx）
        success_responses = manager.generate_response_for_endpoint(
            endpoint.operation_id,
            status_codes=["200", "201", "202"]  # 只生成这些状态码
        )
        
        print(f"✅ 生成了 {len(success_responses)} 个成功响应")
        for resp in success_responses:
            print(f"  - {resp.status_code}")

    # 5. 批量生成响应
    print("\n5️⃣  批量生成响应")
    print("-" * 70)
    
    # 为特定标签的端点生成响应
    all_tags = set()
    for ep in endpoints:
        all_tags.update(ep.tags)
    
    if all_tags:
        target_tag = sorted(list(all_tags))[0]
        print(f"\n为标签 '{target_tag}' 的端点生成响应...")
        
        result = manager.generate_response_for_tags([target_tag])
        
        print(f"✅ 为 {len(result)} 个端点生成了响应")
        
        # 展示前 3 个端点的生成结果
        for i, (op_id, responses) in enumerate(list(result.items())[:3], 1):
            print(f"  {i}. {op_id}: {len(responses)} 个响应")

    # 6. 保存响应数据
    print("\n6️⃣  保存响应数据")
    print("-" * 70)
    
    output_file = Path(__file__).parent / "mock_responses.json"
    manager.save_generated_data(output_file, include_responses=True)
    
    print(f"✅ 响应数据已保存到: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size} 字节")

    # 7. 使用独立响应生成器
    print("\n7️⃣  使用独立响应生成器")
    print("-" * 70)
    
    from data_builder.openapi import ResponseDataGenerator
    
    # 创建独立的响应生成器
    response_gen = ResponseDataGenerator(
        include_headers=True,
        count=2,
        ref_resolver=manager.parser,
    )
    
    if endpoints:
        # 直接为端点生成响应
        responses = response_gen.generate_for_endpoint(endpoints[0])
        print(f"✅ 独立生成器生成了 {len(responses)} 个响应")

    # 8. 部分示例补全演示（新功能）
    print("\n8️⃣  部分示例补全演示")
    print("-" * 70)
    
    # 创建一个包含部分示例的 OpenAPI 文档
    partial_example_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Partial Example API", "version": "1.0.0"},
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "getUserWithPartialExample",
                    "summary": "获取用户信息（部分示例）",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string", "format": "email"},
                                            "status": {
                                                "type": "string",
                                                "enum": ["active", "inactive"]
                                            },
                                            "created_at": {"type": "string"}
                                        },
                                        "required": ["id", "name", "email", "status"]
                                    },
                                    "example": {
                                        "id": 1001,
                                        "name": "张三"
                                        # 缺少 email, status, created_at 字段
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # 使用部分示例生成响应
    partial_manager = APITestDataManager(openapi_document=partial_example_doc)
    partial_manager.configure_response_generator({
        "include_headers": False,
        "count": 1,
    })
    
    partial_responses = partial_manager.generate_response_for_endpoint("getUserWithPartialExample")
    
    if partial_responses:
        resp = partial_responses[0]
        print(f"\n✅ 生成的响应数据：")
        print(f"   状态码: {resp.status_code}")
        print(f"   来自示例: {resp.metadata.get('from_example', False)}")
        
        if resp.response_body:
            print(f"\n   响应体内容（部分示例时，合并生成策略）：")
            body = resp.response_body
            print(f"     - id: {body.get('id')} (使用示例值)")
            print(f"     - name: {body.get('name')} (使用示例值)")
            print(f"     - email: {body.get('email', '未生成')} (按 format: email 生成，缺失示例值)")
            print(f"     - status: {body.get('status', '未生成')} (从 enum 随机选择，缺失示例值)")
            print(f"     - created_at: {body.get('created_at', '未生成')} (可选字段，缺失示例值)")
            
            print(f"\n   合并规则：")
            print(f"     1. 有 example 的字段 → 使用示例值")
            print(f"     2. 缺失字段 → 按 schema 约束生成")
            print(f"     3. enum 无示例值 → 从枚举随机选择")
            print(f"     4. 有 field_policies 显式指定 → 策略优先（示例值无效）")
            
            # 验证必需字段都已补全
            if all(key in body for key in ["id", "name", "email", "status"]):
                print(f"\n   ✅ 所有必需字段已补全！")
            else:
                print(f"\n   ⚠️  部分必需字段缺失")

    # 9. 字段策略优先于示例值演示
    print("\n9️⃣  字段策略优先于示例值演示")
    print("-" * 70)
    
    # 创建一个包含示例，但指定字段策略的文档
    policy_override_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Policy Override API", "version": "1.0.0"},
        "paths": {
            "/products/{id}": {
                "get": {
                    "operationId": "getProductWithPolicyOverride",
                    "summary": "获取产品信息（字段策略优先）",
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "price": {"type": "number", "minimum": 0},
                                            "stock": {"type": "integer", "minimum": 0},
                                            "category": {"type": "string"}  # 添加一个额外字段，让示例不完整
                                        },
                                        "required": ["id", "name", "price", "stock", "category"]
                                    },
                                    "example": {
                                        "id": 2001,
                                        "name": "示例产品",
                                        "price": 99.99,
                                        "stock": 50  # 示例值，但会被策略覆盖
                                        # 缺少 category 字段，示例不完整
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # 使用字段策略生成响应（price 字段策略覆盖示例值）
    policy_manager = APITestDataManager(openapi_document=policy_override_doc)
    policy_manager.configure_response_generator({
        "include_headers": False,
        "count": 1,
        "field_policies": [
            {
                "path": "price",
                "strategy": {
                    "type": "fixed",
                    "value": 199.99  # 显式策略值，覆盖示例值 99.99
                }
            },
            {
                "path": "stock", 
                "strategy": {
                    "type": "range",
                    "min_val": 100,
                    "max_val": 1000
                }
            }
        ]
    })
    
    policy_responses = policy_manager.generate_response_for_endpoint("getProductWithPolicyOverride")
    
    if policy_responses:
        resp = policy_responses[0]
        print(f"\n✅ 生成的响应数据（字段策略优先）：")
        print(f"   状态码: {resp.status_code}")
        
        if resp.response_body:
            body = resp.response_body
            print(f"\n   响应体内容：")
            print(f"     - id: {body.get('id')} (使用示例值 2001)")
            print(f"     - name: {body.get('name')} (使用示例值 '示例产品')")
            print(f"     - price: {body.get('price')} (使用策略值 199.99，覆盖示例值 99.99)")
            print(f"     - stock: {body.get('stock')} (使用策略生成的 100-1000 随机值，覆盖示例值 50)")
            
            print(f"\n   🔍 验证字段策略优先级：")
            print(f"     1. price 示例值: 99.99, 策略值: 199.99 → 实际值: {body.get('price')} (策略优先 ✓)")
            print(f"     2. stock 示例值: 50, 策略值: 100-1000 随机 → 实际值: {body.get('stock')} (策略优先 ✓)")
            print(f"     3. id 和 name 无策略 → 使用示例值 ✓")
    
    print("\n" + "=" * 70)
    print("✅ 响应 Mock 生成示例完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
