"""
OpenAPI 测试数据生成示例。

演示如何使用 openapi 模块解析 OpenAPI 文档并生成测试数据。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data_builder.openapi import (
    APITestDataManager,
    OpenAPIParser,
    RequestDataGenerator,
)


def example_basic_usage():
    """基本使用示例：解析文档并生成数据"""
    print("=" * 60)
    print("1. 基本使用：解析文档并生成数据")
    print("=" * 60)
    
    # 加载 OpenAPI 文档
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    # 创建管理器
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "boundary",
            "include_optional": True,
            "count": 3,
        }
    )
    
    # 获取摘要信息
    summary = manager.summary()
    print(f"\nOpenAPI 版本: {summary['openapi_version']}")
    print(f"总端点数: {summary['total_endpoints']}")
    
    # 为特定端点生成数据
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        print(f"\n为端点生成数据: {endpoint.operation_id}")
        print(f"  路径: {endpoint.path}")
        print(f"  方法: {endpoint.method.value}")
        
        requests = manager.generate_for_endpoint(endpoint.operation_id, count=2)
        
        for i, req in enumerate(requests):
            print(f"\n  请求 {i+1}:")
            print(f"    URL: {req.get_url('https://api.example.com')}")
            if req.path_params:
                print(f"    路径参数: {req.path_params}")
            if req.query_params:
                print(f"    查询参数: {req.query_params}")
            if req.request_body:
                print(f"    请求体: {json.dumps(req.request_body, ensure_ascii=False)[:100]}...")


def example_filter_endpoints():
    """端点筛选示例"""
    print("\n" + "=" * 60)
    print("2. 端点筛选：按标签和路径筛选")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(openapi_document=api_doc_path)
    
    # 按标签筛选
    endpoints = manager.get_all_endpoints()
    tags = set()
    for ep in endpoints:
        tags.update(ep.tags)
    
    print(f"\n可用标签: {', '.join(sorted(tags))}")
    
    # 按路径模式筛选
    chart_endpoints = manager.get_endpoints_by_path_pattern("*/chart_management/*")
    print(f"\n图表管理相关端点数: {len(chart_endpoints)}")
    for ep in chart_endpoints[:3]:
        print(f"  - {ep.operation_id} ({ep.method.value.upper()} {ep.path})")


def example_different_modes():
    """不同生成模式示例"""
    print("\n" + "=" * 60)
    print("3. 不同生成模式：边界值、等价类、笛卡尔积")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    # 边界值模式
    print("\n边界值模式（BOUNDARY）：")
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "boundary",
            "count": 5,
        }
    )
    
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        requests = manager.generate_for_endpoint(endpoint.operation_id, count=3)
        print(f"  生成 {len(requests)} 个请求")
        for i, req in enumerate(requests[:2]):
            print(f"    请求 {i+1}: {req.get_url()}")
    
    # 等价类模式
    print("\n等价类模式（EQUIVALENCE）：")
    manager.configure_generator({
        "generation_mode": "equivalence",
        "count": 5,
    })
    
    if endpoints:
        requests = manager.generate_for_endpoint(endpoints[0].operation_id, count=3)
        print(f"  生成 {len(requests)} 个请求")


def example_custom_field_policy():
    """自定义字段策略示例"""
    print("\n" + "=" * 60)
    print("4. 自定义字段策略：覆盖自动推导")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    # 配置自定义策略
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 3,
            "field_policies": [
                {
                    "path": "owner_id",
                    "strategy": {"type": "fixed", "value": "test-owner-123"}
                },
            ]
        }
    )
    
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        requests = manager.generate_for_endpoint(endpoint.operation_id)
        
        print(f"\n为端点生成数据: {endpoint.operation_id}")
        for i, req in enumerate(requests):
            if "owner_id" in req.query_params:
                print(f"  请求 {i+1} - owner_id: {req.query_params['owner_id']}")


def example_save_and_load():
    """保存和加载数据示例"""
    print("\n" + "=" * 60)
    print("5. 保存和加载：持久化测试数据")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 2,
        }
    )
    
    # 生成数据
    endpoints = manager.get_all_endpoints()[:2]
    for ep in endpoints:
        manager.generate_for_endpoint(ep.operation_id)
    
    # 保存数据
    output_path = Path(__file__).parent / "generated_test_data.json"
    manager.save_generated_data(output_path)
    print(f"\n已保存测试数据到: {output_path}")
    
    # 保存配置
    config_path = Path(__file__).parent / "test_config.json"
    manager.save_config(config_path, openapi_path=str(api_doc_path))
    print(f"已保存配置到: {config_path}")
    
    # 从配置加载
    new_manager = APITestDataManager.from_config(config_path)
    print(f"\n从配置加载的管理器:")
    print(f"  端点数: {new_manager.summary()['total_endpoints']}")
    
    # 清理临时文件
    # if output_path.exists():
    #     output_path.unlink()
    # if config_path.exists():
    #     config_path.unlink()


def example_batch_generation():
    """批量生成示例"""
    print("\n" + "=" * 60)
    print("6. 批量生成：为多个端点生成数据")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 2,
        }
    )
    
    # 为特定标签的端点生成数据
    endpoints = manager.get_all_endpoints()
    if endpoints:
        tags = list(set(ep.tags[0] for ep in endpoints if ep.tags))[:1]
        
        if tags:
            result = manager.generate_for_tags(tags, count_per_endpoint=1)
            print(f"\n为标签 '{tags[0]}' 生成了 {len(result)} 个端点的数据")
            
            for op_id, requests in list(result.items())[:2]:
                print(f"  {op_id}: {len(requests)} 个请求")


def example_generate_by_path_method():
    """按路径和方法生成数据示例"""
    print("\n" + "=" * 60)
    print("7. 按路径和方法生成：指定 endpoint 的 path 和 method")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 3,
        }
    )
    
    # 列出一些可用端点
    endpoints = manager.get_all_endpoints()
    if endpoints:
        # 取第一个端点作为示例
        sample_ep = endpoints[0]
        print(f"\n示例端点信息:")
        print(f"  operationId: {sample_ep.operation_id}")
        print(f"  path: {sample_ep.path}")
        print(f"  method: {sample_ep.method.value.upper()}")
        
        # 方式1: 按 operationId 生成（原有方式）
        print(f"\n方式1: 按 operationId 生成")
        requests1 = manager.generate_for_endpoint(sample_ep.operation_id, count=2)
        print(f"  生成 {len(requests1)} 个请求")
        
        # 方式2: 按 path + method 生成（新增方式）
        print(f"\n方式2: 按 path + method 生成")
        requests2 = manager.generate_for_path_method(
            path=sample_ep.path,
            method=sample_ep.method.value,
            count=2
        )
        print(f"  生成 {len(requests2)} 个请求")
        
        # 显示生成的请求
        for i, req in enumerate(requests2[:1]):
            print(f"\n  示例请求 {i+1}:")
            print(f"    URL: {req.get_url('https://api.example.com')}")
            print(f"    Method: {req.method.value.upper()}")
        
        # 演示获取端点
        print(f"\n演示 get_endpoint_by_path_and_method:")
        ep = manager.get_endpoint_by_path_and_method(sample_ep.path, sample_ep.method.value)
        if ep:
            print(f"  找到端点: {ep.operation_id}")
            print(f"  描述: {ep.summary or '无'}")


def example_multiple_modes():
    """多模式生成示例：同时使用多种生成策略"""
    print("\n" + "=" * 60)
    print("8. 多模式生成：同时使用多种生成策略")
    print("=" * 60)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"示例文档不存在：{api_doc_path}")
        return
    
    # 遍历所有支持的生成模式
    all_modes = ["random", "boundary", "equivalence", "cartesian", "pairwise", "orthogonal", "invalid"]
    
    # 使用多模式生成：边界值 + 随机 + 等价类 + 笛卡尔积 + 对偶 + 正交 + 无效值
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": all_modes,  # 支持列表
            "count": 2,  # 每种模式生成 2 条
        }
    )
    
    print("\n配置信息:")
    print(f"  生成模式: {manager.generator.generation_modes}")
    print(f"  每种模式生成数量: {manager.generator.count}")
    
    # 为端点生成数据
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        print(f"\n为端点生成数据: {endpoint.operation_id}")
        
        requests = manager.generate_for_endpoint(endpoint.operation_id)
        
        print(f"  总生成数量（去重后）: {len(requests)}")
        
        # 显示每条数据的来源模式
        mode_counts = {}
        for req in requests:
            mode = req.metadata.get("generation_mode", "unknown")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        print(f"  各模式数据分布:")
        for mode, count in mode_counts.items():
            print(f"    - {mode}: {count} 条")
        
        # 显示前几条数据示例
        print(f"\n  前 {len(requests)} 条数据示例:")
        for i, req in enumerate(requests):
            mode = req.metadata.get("generation_mode", "unknown")
            print(f"    请求 {i+1} (模式: {mode}):")
            if req.query_params:
                print(f"      查询参数: {req.query_params}")


if __name__ == "__main__":
    example_basic_usage()
    example_filter_endpoints()
    example_different_modes()
    example_custom_field_policy()
    example_save_and_load()
    example_batch_generation()
    example_generate_by_path_method()
    example_multiple_modes()
