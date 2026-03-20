"""
OpenAPI 数据生成器高级用法示例。

演示如何在真实测试场景中使用数据生成器。
"""

import json
from pathlib import Path
from typing import Dict, List

from data_builder.openapi import (
    APITestDataManager,
    GeneratedRequest,
    GeneratedResponse,
    OpenAPIEndpoint,
    ResponseDataGenerator,
)


class APITestSuite:
    """API 测试套件示例"""
    
    def __init__(self, openapi_doc: Path, base_url: str = "https://api.example.com"):
        """
        初始化测试套件。
        
        :param openapi_doc: OpenAPI 文档路径
        :param base_url: API 基础 URL
        """
        self.manager = APITestDataManager(openapi_document=openapi_doc)
        self.base_url = base_url
        self.test_results: List[Dict] = []
    
    def generate_test_cases_for_endpoint(
        self,
        operation_id: str,
        test_modes: List[str] = None,
    ) -> Dict[str, List[GeneratedRequest]]:
        """
        为单个端点生成多组测试用例。
        
        :param operation_id: 操作 ID
        :param test_modes: 测试模式列表（如 ["boundary", "equivalence", "invalid"]）
        :return: 按模式分组的测试数据
        """
        test_modes = test_modes or ["boundary", "random"]
        test_data = {}
        
        for mode in test_modes:
            # 配置生成模式
            self.manager.configure_generator({
                "generation_mode": mode,
                "include_optional": True,
                "count": 3 if mode == "random" else 5,
            })
            
            # 生成数据
            requests = self.manager.generate_for_endpoint(operation_id)
            test_data[mode] = requests
        
        return test_data
    
    def run_boundary_tests(self, operation_id: str) -> Dict:
        """
        运行边界值测试。
        
        边界值测试关注：
        - 最小值/最大值
        - 空字符串/最大长度字符串
        - 数值边界
        """
        print(f"\n🔍 运行边界值测试: {operation_id}")
        print("-" * 70)
        
        self.manager.configure_generator({
            "generation_mode": "boundary",
            "include_optional": True,
            "count": 5,
        })
        
        requests = self.manager.generate_for_endpoint(operation_id)
        
        results = {
            "operation_id": operation_id,
            "test_type": "boundary",
            "total_cases": len(requests),
            "cases": [],
        }
        
        for i, req in enumerate(requests, 1):
            case = {
                "case_id": i,
                "url": req.get_url(self.base_url),
                "method": self.manager.get_endpoint_by_operation_id(operation_id).method.value,
                "data": {
                    "path_params": req.path_params,
                    "query_params": req.query_params,
                    "request_body": req.request_body,
                },
            }
            results["cases"].append(case)
            
            print(f"  用例 {i}: {req.get_url(self.base_url)}")
        
        self.test_results.append(results)
        return results
    
    def run_equivalence_tests(self, operation_id: str) -> Dict:
        """
        运行等价类测试。
        
        等价类测试关注：
        - 有效等价类
        - 无效等价类
        - 枚举值覆盖
        """
        print(f"\n🔍 运行等价类测试: {operation_id}")
        print("-" * 70)
        
        self.manager.configure_generator({
            "generation_mode": "equivalence",
            "include_optional": True,
            "count": 5,
        })
        
        requests = self.manager.generate_for_endpoint(operation_id)
        
        results = {
            "operation_id": operation_id,
            "test_type": "equivalence",
            "total_cases": len(requests),
            "cases": [],
        }
        
        for i, req in enumerate(requests, 1):
            case = {
                "case_id": i,
                "url": req.get_url(self.base_url),
                "method": self.manager.get_endpoint_by_operation_id(operation_id).method.value,
                "data": {
                    "path_params": req.path_params,
                    "query_params": req.query_params,
                    "request_body": req.request_body,
                },
            }
            results["cases"].append(case)
            
            print(f"  用例 {i}: {req.get_url(self.base_url)}")
        
        self.test_results.append(results)
        return results
    
    def run_smoke_tests(self, operation_id: str) -> Dict:
        """
        运行冒烟测试（快速验证基本功能）。
        
        只生成少量典型数据，快速验证接口可用性。
        """
        print(f"\n💨 运行冒烟测试: {operation_id}")
        print("-" * 70)
        
        self.manager.configure_generator({
            "generation_mode": "random",
            "include_optional": False,  # 只包含必需字段
            "count": 1,
        })
        
        requests = self.manager.generate_for_endpoint(operation_id)
        
        if requests:
            req = requests[0]
            results = {
                "operation_id": operation_id,
                "test_type": "smoke",
                "url": req.get_url(self.base_url),
                "method": self.manager.get_endpoint_by_operation_id(operation_id).method.value,
                "data": {
                    "path_params": req.path_params,
                    "query_params": req.query_params,
                    "request_body": req.request_body,
                },
            }
            
            print(f"  ✅ 冒烟测试用例: {req.get_url(self.base_url)}")
            self.test_results.append(results)
            return results
        
        return {}
    
    def generate_test_report(self, output_file: Path = None) -> Dict:
        """
        生成测试报告。
        
        :param output_file: 报告输出文件（可选）
        :return: 测试报告字典
        """
        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "by_type": {},
            },
            "details": self.test_results,
        }
        
        # 统计各类型测试数量
        for result in self.test_results:
            test_type = result.get("test_type", "unknown")
            report["summary"]["by_type"][test_type] = (
                report["summary"]["by_type"].get(test_type, 0) + 1
            )
        
        # 保存报告
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📊 测试报告已保存: {output_file}")
        
        return report


def demo_test_workflow():
    """演示完整的测试工作流"""
    print("=" * 70)
    print("OpenAPI 数据生成器 - 高级用法：自动化测试工作流")
    print("=" * 70)
    
    # 加载文档
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    # 创建测试套件
    suite = APITestSuite(api_doc_path, base_url="https://api.example.com")
    
    # 获取端点
    endpoints = suite.manager.get_all_endpoints()
    if not endpoints:
        print("❌ 没有找到端点")
        return
    
    # 选择一个端点进行测试
    target_endpoint = endpoints[0]
    operation_id = target_endpoint.operation_id
    
    print(f"\n目标端点: {operation_id}")
    print(f"  路径: {target_endpoint.path}")
    print(f"  方法: {target_endpoint.method.value.upper()}")
    print(f"  描述: {target_endpoint.summary}")
    
    # 运行不同类型的测试
    suite.run_smoke_tests(operation_id)
    suite.run_boundary_tests(operation_id)
    suite.run_equivalence_tests(operation_id)
    
    # 生成测试报告
    report_file = Path(__file__).parent / "test_report.json"
    report = suite.generate_test_report(report_file)
    
    # 展示报告摘要
    print("\n" + "=" * 70)
    print("📊 测试报告摘要")
    print("=" * 70)
    print(f"总测试数: {report['summary']['total_tests']}")
    print("按类型统计:")
    for test_type, count in report["summary"]["by_type"].items():
        print(f"  - {test_type}: {count}")
    
    # 清理
    # if report_file.exists():
    #     report_file.unlink()


def demo_custom_field_policy():
    """演示自定义字段策略"""
    print("\n" + "=" * 70)
    print("高级用法：自定义字段策略")
    print("=" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    # 配置自定义字段策略
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 3,
            "field_policies": [
                # 固定 owner_id 为测试值
                {
                    "path": "owner_id",
                    "strategy": {"type": "fixed", "value": "test-user-001"}
                },
                # owner_type 使用枚举值
                {
                    "path": "owner_type",
                    "strategy": {
                        "type": "enum",
                        "values": ["user", "account", "ip"]
                    }
                },
            ]
        }
    )
    
    # 生成数据
    endpoints = manager.get_all_endpoints()
    if endpoints:
        endpoint = endpoints[0]
        requests = manager.generate_for_endpoint(endpoint.operation_id)
        
        print(f"\n为端点 '{endpoint.operation_id}' 生成的数据：")
        for i, req in enumerate(requests, 1):
            print(f"\n用例 {i}:")
            print(f"  owner_id: {req.query_params.get('owner_id', 'N/A')}")
            print(f"  owner_type: {req.query_params.get('owner_type', 'N/A')}")


def demo_batch_testing():
    """演示批量测试"""
    print("\n" + "=" * 70)
    print("高级用法：批量测试多个端点")
    print("=" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 2,
        }
    )
    
    # 获取特定标签的端点
    all_tags = set()
    for ep in manager.get_all_endpoints():
        all_tags.update(ep.tags)
    
    if all_tags:
        target_tag = sorted(list(all_tags))[0]
        print(f"\n为标签 '{target_tag}' 的端点批量生成测试数据...")
        
        result = manager.generate_for_tags([target_tag], count_per_endpoint=2)
        
        print(f"\n✅ 批量生成完成，共 {len(result)} 个端点")
        
        # 统计信息
        total_cases = sum(len(reqs) for reqs in result.values())
        print(f"📊 总测试用例数: {total_cases}")


def demo_mock_response_generation():
    """演示响应 Mock 生成的高级用法"""
    print("\n" + "=" * 70)
    print("高级用法：响应 Mock 数据生成")
    print("=" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    # 配置响应生成器
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        response_config={
            "include_headers": True,  # 包含响应头
            "count": 2,               # 每个响应生成 2 条数据
        }
    )
    
    # 获取端点
    endpoints = manager.get_all_endpoints()
    if not endpoints:
        print("❌ 没有找到端点")
        return
    
    target_endpoint = endpoints[0]
    operation_id = target_endpoint.operation_id
    
    print(f"\n目标端点: {operation_id}")
    print(f"  路径: {target_endpoint.path}")
    print(f"  方法: {target_endpoint.method.value.upper()}")
    
    # 1. 生成所有响应
    print("\n1️⃣  生成所有响应：")
    responses = manager.generate_response_for_endpoint(operation_id)
    print(f"   ✅ 生成了 {len(responses)} 个响应")
    for resp in responses:
        print(f"      - {resp.status_code}: {resp.metadata.get('response_description', '无描述')}")
        print(f"        来源示例: {resp.metadata.get('from_example', False)}")
    
    # 2. 只生成成功响应
    print("\n2️⃣  只生成成功响应：")
    success_responses = manager.generate_response_for_endpoint(
        operation_id,
        status_codes=["200", "201", "202"]
    )
    print(f"   ✅ 生成了 {len(success_responses)} 个成功响应")
    
    # 3. 生成错误响应
    print("\n3️⃣  生成错误响应：")
    error_responses = manager.generate_response_for_endpoint(
        operation_id,
        status_codes=["400", "401", "403", "404", "500"]
    )
    print(f"   ✅ 生成了 {len(error_responses)} 个错误响应")
    for resp in error_responses:
        print(f"      - {resp.status_code}: {resp.metadata.get('response_description', '无描述')}")
    
    # 4. 使用独立响应生成器
    print("\n4️⃣  使用独立响应生成器：")
    response_gen = ResponseDataGenerator(
        include_headers=True,
        count=1,
        ref_resolver=manager.parser,
    )
    
    responses = response_gen.generate_for_endpoint(target_endpoint)
    print(f"   ✅ 独立生成器生成了 {len(responses)} 个响应")
    for resp in responses:
        print(f"      - {resp.status_code}")
        if resp.response_headers:
            print(f"        响应头字段数: {len(resp.response_headers)}")


def demo_mock_response_for_test_scenarios():
    """演示在测试场景中使用响应 Mock"""
    print("\n" + "=" * 70)
    print("高级用法：测试场景中的响应 Mock")
    print("=" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    # 创建管理器
    manager = APITestDataManager(openapi_document=api_doc_path)
    
    # 配置响应生成器
    manager.configure_response_generator({
        "include_headers": False,
        "count": 1,
    })
    
    # 为特定标签的端点生成响应
    endpoints = manager.get_all_endpoints()
    if endpoints:
        # 获取所有标签
        all_tags = set()
        for ep in endpoints:
            all_tags.update(ep.tags)
        
        if all_tags:
            target_tag = sorted(list(all_tags))[0]
            print(f"\n为标签 '{target_tag}' 的端点生成 Mock 响应...")
            
            # 批量生成响应
            responses_dict = manager.generate_response_for_tags([target_tag])
            
            print(f"✅ 为 {len(responses_dict)} 个端点生成了响应")
            
            # 统计响应类型
            success_count = 0
            error_count = 0
            for op_id, responses in responses_dict.items():
                for resp in responses:
                    if resp.is_success():
                        success_count += 1
                    elif resp.is_error():
                        error_count += 1
            
            print(f"📊 响应统计:")
            print(f"   - 成功响应: {success_count}")
            print(f"   - 错误响应: {error_count}")
            
            # 保存响应数据
            output_file = Path(__file__).parent / "mock_responses_test.json"
            manager.save_generated_data(output_file, include_responses=True)
            print(f"\n💾 Mock 响应已保存: {output_file}")


def demo_request_response_pair():
    """演示请求-响应对生成（完整的 API 测试场景）"""
    print("\n" + "=" * 70)
    print("高级用法：请求-响应对生成")
    print("=" * 70)
    
    api_doc_path = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"
    
    if not api_doc_path.exists():
        print(f"❌ 文档不存在：{api_doc_path}")
        return
    
    manager = APITestDataManager(
        openapi_document=api_doc_path,
        generation_config={
            "generation_mode": "random",
            "count": 2,
        },
        response_config={
            "include_headers": True,
            "count": 1,
        }
    )
    
    # 获取端点
    endpoints = manager.get_all_endpoints()
    if not endpoints:
        print("❌ 没有找到端点")
        return
    
    target_endpoint = endpoints[0]
    operation_id = target_endpoint.operation_id
    
    print(f"\n端点: {operation_id}")
    print(f"  路径: {target_endpoint.path}")
    print(f"  方法: {target_endpoint.method.value.upper()}")
    
    # 生成请求
    print("\n📤 生成请求：")
    requests = manager.generate_for_endpoint(operation_id)
    print(f"   ✅ 生成了 {len(requests)} 个请求")
    
    # 生成响应
    print("\n📥 生成响应：")
    responses = manager.generate_response_for_endpoint(operation_id)
    print(f"   ✅ 生成了 {len(responses)} 个响应")
    
    # 生成请求-响应对
    print("\n🔄 请求-响应对：")
    test_pairs = []
    
    for req in requests:
        for resp in responses:
            pair = {
                "request": {
                    "method": req.method.value,
                    "url": req.get_url("https://api.example.com"),
                    "path_params": req.path_params,
                    "query_params": req.query_params,
                    "headers": req.header_params,
                    "body": req.request_body,
                },
                "response": {
                    "status_code": resp.status_code,
                    "description": resp.metadata.get('response_description', ''),
                    "headers": resp.response_headers,
                    "body": resp.response_body,
                }
            }
            test_pairs.append(pair)
            print(f"\n   测试对 {len(test_pairs)}:")
            print(f"      请求: {req.method.value.upper()} {req.get_url('https://api.example.com')}")
            print(f"      响应: {resp.status_code}")
    
    # 保存测试对
    output_file = Path(__file__).parent / "test_pairs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "operation_id": operation_id,
            "endpoint": {
                "path": target_endpoint.path,
                "method": target_endpoint.method.value,
                "summary": target_endpoint.summary,
            },
            "test_pairs": test_pairs,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试对已保存: {output_file}")


if __name__ == "__main__":
    demo_test_workflow()
    demo_custom_field_policy()
    demo_batch_testing()
    demo_mock_response_generation()
    demo_mock_response_for_test_scenarios()
    demo_request_response_pair()
