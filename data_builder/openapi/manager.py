"""
API 测试数据管理器。

提供统一的接口来管理 OpenAPI 文档解析、数据生成和配置持久化。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .request_generator import RequestDataGenerator
from .response_generator import ResponseDataGenerator
from .models import (
    GeneratedRequest,
    GeneratedResponse,
    OpenAPIDocument,
    OpenAPIEndpoint,
)
from .parser import OpenAPIParser


class APITestDataManager:
    """
    API 测试数据管理器。
    
    统一管理 OpenAPI 文档解析和测试数据生成，支持配置持久化。
    """
    
    def __init__(
        self,
        openapi_document: Optional[Union[str, Path, Dict[str, Any]]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        response_config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化管理器。
        
        :param openapi_document: OpenAPI 文档（文件路径或字典）
        :param generation_config: 请求数据生成配置
        :param response_config: 响应数据生成配置
        """
        self.parser: Optional[OpenAPIParser] = None
        self.document: Optional[OpenAPIDocument] = None
        self.generator: Optional[RequestDataGenerator] = None
        self.response_generator: Optional[ResponseDataGenerator] = None
        self.generated_data: Dict[str, List[GeneratedRequest]] = {}
        self.generated_responses: Dict[str, List[GeneratedResponse]] = {}
        
        # 加载 OpenAPI 文档
        if openapi_document:
            self.load_openapi_document(openapi_document)
        
        # 初始化请求生成器
        if generation_config:
            self.configure_generator(generation_config)
        
        # 初始化响应生成器
        if response_config:
            self.configure_response_generator(response_config)
    
    def load_openapi_document(self, document: Union[str, Path, Dict[str, Any]]) -> None:
        """
        加载 OpenAPI 文档。
        
        :param document: 文件路径（JSON/YAML）或字典
        """
        if isinstance(document, (str, Path)):
            self.parser = OpenAPIParser.from_file(document)
        elif isinstance(document, dict):
            self.parser = OpenAPIParser.from_dict(document)
        else:
            raise ValueError("document 参数必须是文件路径或字典")
        
        self.document = self.parser.parse()
    
    def configure_generator(self, config: Dict[str, Any]) -> None:
        """
        配置请求数据生成器。

        :param config: 生成器配置字典
            - generation_mode: 支持单个模式字符串或模式列表，如：
              - "boundary" 单个模式
              - ["boundary", "random"] 多模式独立生成后去重合并
        """
        self.generator = RequestDataGenerator(
            generation_mode=config.get("generation_mode", "boundary"),
            include_optional=config.get("include_optional", True),
            count=config.get("count", 5),
            field_policies=config.get("field_policies", []),
            content_type=config.get("content_type", "application/json"),
            ref_resolver=self.parser,  # 传递 parser 用于解析 $ref 引用
        )
    
    def configure_response_generator(self, config: Dict[str, Any]) -> None:
        """
        配置响应数据生成器。

        :param config: 生成器配置字典
            - include_headers: 是否生成响应头（默认 True）
            - count: 每个响应生成的数据数量（默认 1）
            - field_policies: 特定字段的策略配置（优先级最高）
            - content_type: 响应体的 content-type（默认 "application/json"）
        """
        self.response_generator = ResponseDataGenerator(
            include_headers=config.get("include_headers", True),
            count=config.get("count", 1),
            field_policies=config.get("field_policies", []),
            content_type=config.get("content_type", "application/json"),
            ref_resolver=self.parser,  # 传递 parser 用于解析 $ref 引用
        )
    
    def get_all_endpoints(self) -> List[OpenAPIEndpoint]:
        """
        获取所有 API 端点。
        
        :return: OpenAPIEndpoint 列表
        """
        if not self.document:
            raise ValueError("未加载 OpenAPI 文档")
        return self.document.get_all_endpoints()
    
    def get_endpoints_by_tag(self, tag: str) -> List[OpenAPIEndpoint]:
        """
        根据标签获取端点。
        
        :param tag: 标签名称
        :return: OpenAPIEndpoint 列表
        """
        if not self.document:
            raise ValueError("未加载 OpenAPI 文档")
        return self.document.get_endpoints_by_tag(tag)
    
    def get_endpoint_by_operation_id(self, operation_id: str) -> Optional[OpenAPIEndpoint]:
        """
        根据 operationId 获取端点。
        
        :param operation_id: 操作 ID
        :return: OpenAPIEndpoint 实例，如果不存在则返回 None
        """
        if not self.document:
            raise ValueError("未加载 OpenAPI 文档")
        return self.document.get_endpoint_by_operation_id(operation_id)
    
    def get_endpoint_by_path_and_method(
        self, 
        path: str, 
        method: str
    ) -> Optional[OpenAPIEndpoint]:
        """
        根据路径和方法获取端点。
        
        :param path: API 路径（如 "/users/{id}"）
        :param method: HTTP 方法（如 "GET", "POST"）
        :return: OpenAPIEndpoint 实例，如果不存在则返回 None
        """
        if not self.document:
            raise ValueError("未加载 OpenAPI 文档")
        return self.document.get_endpoint_by_path_and_method(path, method)
    
    def get_endpoints_by_path_pattern(self, pattern: str) -> List[OpenAPIEndpoint]:
        """
        根据路径模式获取端点（支持通配符）。
        
        :param pattern: 路径模式（如 "/users/*", "*/chart_management/*"）
        :return: OpenAPIEndpoint 列表
        """
        import fnmatch
        
        endpoints = self.get_all_endpoints()
        matched = []
        
        for endpoint in endpoints:
            if fnmatch.fnmatch(endpoint.path, pattern):
                matched.append(endpoint)
        
        return matched
    
    def generate_for_endpoint(
        self,
        operation_id: str,
        count: Optional[int] = None,
    ) -> List[GeneratedRequest]:
        """
        为单个端点生成测试数据。
        
        :param operation_id: 操作 ID
        :param count: 覆盖默认生成数量
        :return: GeneratedRequest 列表
        """
        if not self.generator:
            raise ValueError("未配置数据生成器")
        
        endpoint = self.get_endpoint_by_operation_id(operation_id)
        if not endpoint:
            raise ValueError(f"未找到 operationId: {operation_id}")
        
        requests = self.generator.generate_for_endpoint(endpoint, count)
        
        # 存储到 generated_data 便于后续保存
        self.generated_data[operation_id] = requests
        
        return requests
    
    def generate_for_path_method(
        self,
        path: str,
        method: str,
        count: Optional[int] = None,
    ) -> List[GeneratedRequest]:
        """
        根据路径和方法为端点生成测试数据。
        
        :param path: API 路径（如 "/users/{id}"）
        :param method: HTTP 方法（如 "GET", "POST"）
        :param count: 覆盖默认生成数量
        :return: GeneratedRequest 列表
        """
        if not self.generator:
            raise ValueError("未配置数据生成器")
        
        endpoint = self.get_endpoint_by_path_and_method(path, method)
        if not endpoint:
            raise ValueError(f"未找到端点: {method.upper()} {path}")
        
        requests = self.generator.generate_for_endpoint(endpoint, count)
        
        # 存储到 generated_data 便于后续保存
        self.generated_data[endpoint.operation_id] = requests
        
        return requests
    
    def generate_for_tags(
        self,
        tags: List[str],
        count_per_endpoint: Optional[int] = None,
    ) -> Dict[str, List[GeneratedRequest]]:
        """
        为指定标签的所有端点生成测试数据。
        
        :param tags: 标签列表
        :param count_per_endpoint: 每个端点的生成数量
        :return: {operation_id: List[GeneratedRequest]} 字典
        """
        if not self.generator:
            raise ValueError("未配置数据生成器")
        
        result = {}
        
        for tag in tags:
            endpoints = self.get_endpoints_by_tag(tag)
            for endpoint in endpoints:
                requests = self.generator.generate_for_endpoint(endpoint, count_per_endpoint)
                result[endpoint.operation_id] = requests
        
        self.generated_data.update(result)
        return result
    
    def generate_for_all(
        self,
        count_per_endpoint: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, List[GeneratedRequest]]:
        """
        为所有端点生成测试数据。
        
        :param count_per_endpoint: 每个端点的生成数量
        :param exclude_patterns: 排除的 operationId 模式列表（支持通配符）
        :return: {operation_id: List[GeneratedRequest]} 字典
        """
        if not self.generator:
            raise ValueError("未配置数据生成器")
        
        import fnmatch
        
        endpoints = self.get_all_endpoints()
        result = {}
        
        for endpoint in endpoints:
            # 检查是否在排除列表中
            if exclude_patterns:
                excluded = any(
                    fnmatch.fnmatch(endpoint.operation_id, pattern)
                    for pattern in exclude_patterns
                )
                if excluded:
                    continue
            
            requests = self.generator.generate_for_endpoint(endpoint, count_per_endpoint)
            result[endpoint.operation_id] = requests
        
        self.generated_data.update(result)
        return result
    
    # ========== 响应数据生成方法 ==========
    
    def generate_response_for_endpoint(
        self,
        operation_id: str,
        status_codes: Optional[List[str]] = None,
        count: Optional[int] = None,
    ) -> List[GeneratedResponse]:
        """
        为单个端点生成响应数据（Mock）。
        
        :param operation_id: 操作 ID
        :param status_codes: 指定生成的状态码列表（如 ["200", "400"]），为 None 则生成所有定义的响应
        :param count: 覆盖默认生成数量
        :return: GeneratedResponse 列表
        """
        if not self.response_generator:
            # 自动创建默认配置的响应生成器
            self.configure_response_generator({})
        
        endpoint = self.get_endpoint_by_operation_id(operation_id)
        if not endpoint:
            raise ValueError(f"未找到 operationId: {operation_id}")
        
        responses = self.response_generator.generate_for_endpoint(endpoint, status_codes, count)
        
        # 存储到 generated_responses 便于后续保存（替换模式，避免累加）
        self.generated_responses[operation_id] = responses
        
        return responses
    
    def generate_response_for_path_method(
        self,
        path: str,
        method: str,
        status_codes: Optional[List[str]] = None,
        count: Optional[int] = None,
    ) -> List[GeneratedResponse]:
        """
        根据路径和方法为端点生成响应数据（Mock）。
        
        :param path: API 路径（如 "/users/{id}"）
        :param method: HTTP 方法（如 "GET", "POST"）
        :param status_codes: 指定生成的状态码列表
        :param count: 覆盖默认生成数量
        :return: GeneratedResponse 列表
        """
        if not self.response_generator:
            self.configure_response_generator({})
        
        endpoint = self.get_endpoint_by_path_and_method(path, method)
        if not endpoint:
            raise ValueError(f"未找到端点: {method.upper()} {path}")
        
        responses = self.response_generator.generate_for_endpoint(endpoint, status_codes, count)
        
        # 存储到 generated_responses 便于后续保存（替换模式，避免累加）
        self.generated_responses[endpoint.operation_id] = responses
        
        return responses
    
    def generate_response_for_tags(
        self,
        tags: List[str],
        status_codes: Optional[List[str]] = None,
        count_per_endpoint: Optional[int] = None,
    ) -> Dict[str, List[GeneratedResponse]]:
        """
        为指定标签的所有端点生成响应数据（Mock）。
        
        :param tags: 标签列表
        :param status_codes: 指定生成的状态码列表
        :param count_per_endpoint: 每个端点的生成数量
        :return: {operation_id: List[GeneratedResponse]} 字典
        """
        if not self.response_generator:
            self.configure_response_generator({})
        
        result = {}
        
        for tag in tags:
            endpoints = self.get_endpoints_by_tag(tag)
            for endpoint in endpoints:
                responses = self.response_generator.generate_for_endpoint(
                    endpoint, status_codes, count_per_endpoint
                )
                result[endpoint.operation_id] = responses
        
        self.generated_responses.update(result)
        return result
    
    def generate_response_for_all(
        self,
        status_codes: Optional[List[str]] = None,
        count_per_endpoint: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, List[GeneratedResponse]]:
        """
        为所有端点生成响应数据（Mock）。
        
        :param status_codes: 指定生成的状态码列表
        :param count_per_endpoint: 每个端点的生成数量
        :param exclude_patterns: 排除的 operationId 模式列表（支持通配符）
        :return: {operation_id: List[GeneratedResponse]} 字典
        """
        if not self.response_generator:
            self.configure_response_generator({})
        
        import fnmatch
        
        endpoints = self.get_all_endpoints()
        result = {}
        
        for endpoint in endpoints:
            # 检查是否在排除列表中
            if exclude_patterns:
                excluded = any(
                    fnmatch.fnmatch(endpoint.operation_id, pattern)
                    for pattern in exclude_patterns
                )
                if excluded:
                    continue
            
            responses = self.response_generator.generate_for_endpoint(
                endpoint, status_codes, count_per_endpoint
            )
            result[endpoint.operation_id] = responses
        
        self.generated_responses.update(result)
        return result
    
    def get_generated_responses(
        self,
        operation_id: str,
    ) -> Optional[List[GeneratedResponse]]:
        """
        获取已生成的响应数据。
        
        :param operation_id: 操作 ID
        :return: GeneratedResponse 列表，如果不存在则返回 None
        """
        return self.generated_responses.get(operation_id)
    
    def get_response_by_index(
        self,
        operation_id: str,
        index: int,
    ) -> Optional[GeneratedResponse]:
        """
        根据索引获取单个响应。
        
        :param operation_id: 操作 ID
        :param index: 响应索引
        :return: GeneratedResponse 实例，如果不存在则返回 None
        """
        responses = self.get_generated_responses(operation_id)
        if responses and 0 <= index < len(responses):
            return responses[index]
        return None
    
    def get_generated_requests(
        self,
        operation_id: str,
    ) -> Optional[List[GeneratedRequest]]:
        """
        获取已生成的测试数据。
        
        :param operation_id: 操作 ID
        :return: GeneratedRequest 列表，如果不存在则返回 None
        """
        return self.generated_data.get(operation_id)
    
    def get_request_by_index(
        self,
        operation_id: str,
        index: int,
    ) -> Optional[GeneratedRequest]:
        """
        根据索引获取单个请求。
        
        :param operation_id: 操作 ID
        :param index: 请求索引
        :return: GeneratedRequest 实例，如果不存在则返回 None
        """
        requests = self.get_generated_requests(operation_id)
        if requests and 0 <= index < len(requests):
            return requests[index]
        return None
    
    def save_generated_data(
        self,
        output_path: Union[str, Path],
        format: str = "json",
        pretty: bool = True,
        include_responses: bool = False,
    ) -> None:
        """
        保存生成的测试数据到文件。
        
        :param output_path: 输出文件路径
        :param format: 输出格式（"json" 或 "yaml"）
        :param pretty: 是否美化输出（仅 JSON）
        :param include_responses: 是否包含响应数据（如果为 True，使用嵌套格式）
        """
        output_path = Path(output_path)
        
        # 转换为可序列化的字典
        if include_responses:
            # 新格式：包含请求和响应的嵌套结构
            data = {
                "requests": {
                    operation_id: [req.to_dict() for req in requests]
                    for operation_id, requests in self.generated_data.items()
                },
                "responses": {
                    operation_id: [resp.to_dict() for resp in responses]
                    for operation_id, responses in self.generated_responses.items()
                }
            }
        else:
            # 保持原有格式：直接返回操作ID到请求数据的映射
            data = {
                operation_id: [req.to_dict() for req in requests]
                for operation_id, requests in self.generated_data.items()
            }
        
        if format == "yaml":
            try:
                import yaml
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            except ImportError:
                raise ImportError("需要安装 PyYAML 库：pip install pyyaml")
        else:
            # 默认为 JSON 格式
            with open(output_path, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False)
    
    def load_generated_data(self, input_path: Union[str, Path]) -> None:
        """
        从文件加载已生成的测试数据。
        
        :param input_path: 输入文件路径
        """
        input_path = Path(input_path)
        
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 转换为 GeneratedRequest 对象
        self.generated_data = {
            operation_id: [
                GeneratedRequest(**req_dict)
                for req_dict in requests_dict
            ]
            for operation_id, requests_dict in data.items()
        }
    
    def save_config(
        self,
        output_path: Union[str, Path],
        openapi_path: Optional[str] = None,
    ) -> None:
        """
        保存配置到文件（用于后续重复使用）。
        
        :param output_path: 输出文件路径
        :param openapi_path: OpenAPI 文档路径（如果需要保存）
        """
        output_path = Path(output_path)
        
        # 获取 generation_mode（可能是单个模式或列表）
        if self.generator:
            generation_modes = self.generator.generation_modes
            # 转为小写保存
            if len(generation_modes) == 1:
                generation_mode = generation_modes[0].lower()
            else:
                generation_mode = [m.lower() for m in generation_modes]
        else:
            generation_mode = "boundary"
        
        config = {
            "openapi_path": openapi_path,
            "generation_config": {
                "generation_mode": generation_mode,
                "include_optional": self.generator.include_optional if self.generator else True,
                "count": self.generator.count if self.generator else 5,
                "field_policies": self.generator.field_policies if self.generator else [],
                "content_type": self.generator.content_type if self.generator else "application/json",
            },
        }
        
        # 如果配置了响应生成器，也保存配置
        if self.response_generator:
            config["response_config"] = {
                "include_headers": self.response_generator.include_headers,
                "count": self.response_generator.count,
                "field_policies": self.response_generator.field_policies,
                "content_type": self.response_generator.content_type,
            }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_config(
        cls,
        config_path: Union[str, Path],
        openapi_document: Optional[Union[str, Path, Dict[str, Any]]] = None,
    ) -> "APITestDataManager":
        """
        从配置文件创建管理器实例。
        
        :param config_path: 配置文件路径
        :param openapi_document: OpenAPI 文档（覆盖配置文件中的路径）
        :return: APITestDataManager 实例
        """
        config_path = Path(config_path)
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 确定 OpenAPI 文档来源
        if not openapi_document:
            openapi_path = config.get("openapi_path")
            if openapi_path:
                openapi_document = openapi_path
        
        return cls(
            openapi_document=openapi_document,
            generation_config=config.get("generation_config"),
            response_config=config.get("response_config"),
        )
    
    def clear_generated_data(self, clear_requests: bool = True, clear_responses: bool = True) -> None:
        """
        清空已生成的测试数据。
        
        :param clear_requests: 是否清空请求数据
        :param clear_responses: 是否清空响应数据
        """
        if clear_requests:
            self.generated_data.clear()
        if clear_responses:
            self.generated_responses.clear()

    def summary(self) -> Dict[str, Any]:
        """
        获取管理器的摘要信息。
        
        :return: 摘要信息字典
        """
        endpoints = self.get_all_endpoints() if self.document else []
        
        return {
            "openapi_version": self.document.openapi_version if self.document else None,
            "total_endpoints": len(endpoints),
            "total_generated_apis": len(self.generated_data),
            "total_generated_requests": sum(len(reqs) for reqs in self.generated_data.values()),
            "total_generated_response_apis": len(self.generated_responses),
            "total_generated_responses": sum(len(resps) for resps in self.generated_responses.values()),
            "generation_modes": self.generator.generation_modes if self.generator else [],
            "response_generator_configured": self.response_generator is not None,
        }
