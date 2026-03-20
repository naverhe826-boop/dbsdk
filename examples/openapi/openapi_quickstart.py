"""
OpenAPI 数据生成器快速入门示例。

演示如何快速上手使用 OpenAPI 数据生成器。
"""

import json
from pathlib import Path

from data_builder.openapi import APITestDataManager


def main():
    """快速入门示例"""
    print("=" * 70)
    print("OpenAPI 数据生成器 - 快速入门")
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

    # 2. 探索 API 端点
    print("\n2️⃣  探索 API 端点")
    print("-" * 70)
    
    endpoints = manager.get_all_endpoints()
    print(f"✅ 获取到 {len(endpoints)} 个端点")
    
    # 展示前 5 个端点
    print("\n前 5 个端点：")
    for i, ep in enumerate(endpoints[:5], 1):
        tags_str = f"[{', '.join(ep.tags)}]" if ep.tags else "[无标签]"
        print(f"  {i}. {ep.method.value.upper():6} {ep.path:50} {tags_str}")
        if ep.summary:
            print(f"     描述: {ep.summary}")

    # 3. 配置数据生成策略
    print("\n3️⃣  配置数据生成策略")
    print("-" * 70)
    
    config = {
        "generation_mode": "boundary",  # 边界值模式（适合测试）
        "include_optional": True,       # 包含可选字段
        "count": 3,                     # 每个端点生成 3 组数据
    }
    
    manager.configure_generator(config)
    print(f"✅ 生成策略配置完成")
    print(f"   模式: {config['generation_mode']}")
    print(f"   数据组数: {config['count']}")

    # 4. 为单个端点生成数据
    print("\n4️⃣  为单个端点生成测试数据")
    print("-" * 70)
    
    if endpoints:
        endpoint = endpoints[0]
        print(f"\n端点: {endpoint.operation_id}")
        print(f"  路径: {endpoint.path}")
        print(f"  方法: {endpoint.method.value.upper()}")
        
        if endpoint.summary:
            print(f"  描述: {endpoint.summary}")
        
        # 生成数据
        requests = manager.generate_for_endpoint(endpoint.operation_id, count=3)
        
        print(f"\n✅ 生成了 {len(requests)} 组测试数据：")
        for i, req in enumerate(requests, 1):
            print(f"\n  测试数据 {i}:")
            print(f"    URL: {req.get_url('https://api.example.com')}")
            
            if req.path_params:
                print(f"    路径参数: {req.path_params}")
            
            if req.query_params:
                print(f"    查询参数: {req.query_params}")
            
            if req.header_params:
                print(f"    请求头: {list(req.header_params.keys())}")
            
            if req.request_body:
                body_str = json.dumps(req.request_body, ensure_ascii=False)
                if len(body_str) > 100:
                    body_str = body_str[:100] + "..."
                print(f"    请求体: {body_str}")

    # 5. 批量生成数据
    print("\n5️⃣  批量生成数据")
    print("-" * 70)
    
    # 为特定标签的端点生成数据
    all_tags = set()
    for ep in endpoints:
        all_tags.update(ep.tags)
    
    if all_tags:
        target_tag = sorted(list(all_tags))[0]
        print(f"\n为标签 '{target_tag}' 的端点生成数据...")
        
        result = manager.generate_for_tags([target_tag], count_per_endpoint=2)
        
        print(f"✅ 为 {len(result)} 个端点生成了数据")
        
        # 展示前 3 个端点的生成结果
        for i, (op_id, requests) in enumerate(list(result.items())[:3], 1):
            print(f"  {i}. {op_id}: {len(requests)} 组数据")

    # 6. 按路径模式筛选端点
    print("\n6️⃣  按路径模式筛选端点")
    print("-" * 70)
    
    pattern = "*/chart_management/*"
    matched_endpoints = manager.get_endpoints_by_path_pattern(pattern)
    
    print(f"✅ 匹配模式 '{pattern}' 的端点: {len(matched_endpoints)} 个")
    for ep in matched_endpoints[:3]:
        print(f"  - {ep.method.value.upper()} {ep.path}")

    # 7. 持久化数据
    print("\n7️⃣  持久化测试数据")
    print("-" * 70)
    
    output_file = Path(__file__).parent / "quickstart_test_data.json"
    manager.save_generated_data(output_file)
    
    print(f"✅ 测试数据已保存到: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size} 字节")
    
    # 清理
    # if output_file.exists():
    #     output_file.unlink()

    # 8. 从配置创建管理器
    print("\n8️⃣  从配置文件创建管理器")
    print("-" * 70)
    
    config_file = Path(__file__).parent / "quickstart_config.json"
    
    # 保存配置
    manager.save_config(config_file, openapi_path=str(api_doc_path))
    print(f"✅ 配置已保存到: {config_file}")
    
    # 从配置加载
    new_manager = APITestDataManager.from_config(config_file)
    print(f"✅ 从配置加载成功")
    print(f"   端点数: {new_manager.summary()['total_endpoints']}")
    
    # 清理
    # if config_file.exists():
    #     config_file.unlink()

    print("\n" + "=" * 70)
    print("✅ 快速入门完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
