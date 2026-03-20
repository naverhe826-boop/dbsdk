"""
OpenAPI 数据模型定义。

定义 OpenAPI 3.x 规范相关的数据结构，用于表示解析后的 API 端点信息。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ParameterLocation(Enum):
    """参数位置"""
    QUERY = "query"      # URL 查询参数
    PATH = "path"        # URL 路径参数
    HEADER = "header"    # 请求头参数
    COOKIE = "cookie"    # Cookie 参数


class HttpMethod(Enum):
    """HTTP 方法"""
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"
    TRACE = "trace"


@dataclass
class OpenAPIParameter:
    """
    OpenAPI 参数模型。
    
    对应 OpenAPI 3.0 规范中的 Parameter Object。
    """
    name: str                                    # 参数名称
    location: ParameterLocation                 # 参数位置
    schema: Dict[str, Any]                      # 参数的 JSON Schema
    required: bool = False                      # 是否必需
    description: Optional[str] = None           # 参数描述
    deprecated: bool = False                    # 是否废弃
    style: Optional[str] = None                 # 参数样式（如 "form", "simple"）
    explode: Optional[bool] = None              # 是否展开数组/对象
    example: Optional[Any] = None               # 示例值
    examples: Optional[Dict[str, Any]] = None   # 示例字典
    
    def __post_init__(self):
        """后处理：将字符串转换为枚举"""
        if isinstance(self.location, str):
            self.location = ParameterLocation(self.location)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "location": self.location.value,
            "schema": self.schema,
            "required": self.required,
            "description": self.description,
            "deprecated": self.deprecated,
            "style": self.style,
            "explode": self.explode,
            "example": self.example,
            "examples": self.examples,
        }


@dataclass
class OpenAPIRequestBody:
    """
    OpenAPI 请求体模型。
    
    对应 OpenAPI 3.0 规范中的 Request Body Object。
    """
    content: Dict[str, Dict[str, Any]]          # content-type → {schema: {...}, examples: {...}}
    required: bool = False                      # 是否必需
    description: Optional[str] = None           # 请求体描述
    
    def get_schema(self, content_type: str = "application/json") -> Optional[Dict[str, Any]]:
        """
        获取指定 content-type 的 schema。
        
        :param content_type: 内容类型，如 "application/json"
        :return: JSON Schema 字典，如果不存在则返回 None
        """
        content_info = self.content.get(content_type, {})
        return content_info.get("schema")
    
    def get_example(self, content_type: str = "application/json") -> Optional[Any]:
        """
        获取指定 content-type 的示例。
        
        :param content_type: 内容类型
        :return: 示例值，如果不存在则返回 None
        """
        content_info = self.content.get(content_type, {})
        return content_info.get("example")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class OpenAPIResponseHeader:
    """
    OpenAPI 响应头模型。
    
    对应 OpenAPI 3.0 规范中的 Header Object。
    """
    name: str                                    # 响应头名称
    schema: Dict[str, Any]                      # 响应头的 JSON Schema
    description: Optional[str] = None           # 响应头描述
    required: bool = False                      # 是否必需
    deprecated: bool = False                    # 是否废弃
    example: Optional[Any] = None               # 示例值
    examples: Optional[Dict[str, Any]] = None   # 示例字典
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "schema": self.schema,
            "description": self.description,
            "required": self.required,
            "deprecated": self.deprecated,
            "example": self.example,
            "examples": self.examples,
        }


@dataclass
class OpenAPIResponse:
    """
    OpenAPI 响应模型。
    
    对应 OpenAPI 3.0 规范中的 Response Object。
    """
    status_code: str                            # 状态码（如 "200", "400", "default"）
    description: Optional[str] = None           # 响应描述
    content: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # content-type → {schema, example, examples}
    headers: List[OpenAPIResponseHeader] = field(default_factory=list)  # 响应头列表
    
    def get_schema(self, content_type: str = "application/json") -> Optional[Dict[str, Any]]:
        """
        获取指定 content-type 的 schema。
        
        :param content_type: 内容类型，如 "application/json"
        :return: JSON Schema 字典，如果不存在则返回 None
        """
        content_info = self.content.get(content_type, {})
        return content_info.get("schema")
    
    def _extract_first_example(self, examples: Any) -> Optional[Any]:
        """
        从 examples 中提取第一个示例值。
        
        :param examples: 可以是 dict、list 或其他类型
        :return: 第一个示例值，如果无法提取则返回 None
        """
        if not examples:
            return None
        
        if isinstance(examples, dict) and examples:
            # 返回第一个 example 的 value
            first_example = next(iter(examples.values()), None)
            if isinstance(first_example, dict) and "value" in first_example:
                return first_example["value"]
            return first_example
        elif isinstance(examples, list) and examples:
            return examples[0]
        
        return None
    
    def _get_example_from_schema(self, schema: Dict[str, Any]) -> Optional[Any]:
        """
        从 schema 对象中获取示例。
        
        :param schema: JSON Schema 字典
        :return: 示例值，如果不存在则返回 None
        """
        if not isinstance(schema, dict):
            return None
        
        # 1. 直接从 schema 的 example 字段获取
        example_value = schema.get("example")
        if example_value is not None:
            return example_value
        
        # 2. 从 schema 的 examples 字段获取
        if "examples" in schema:
            examples = schema["examples"]
            return self._extract_first_example(examples)
        
        return None
    
    def _get_example_from_content_info(self, content_info: Dict[str, Any]) -> Optional[Any]:
        """
        从 content_info 中获取示例。
        
        :param content_info: content 信息字典
        :return: 示例值，如果不存在则返回 None
        """
        if not isinstance(content_info, dict):
            return None
        
        # 1. 直接从 content_info 的 example 字段获取
        example_value = content_info.get("example")
        if example_value is not None:
            return example_value
        
        # 2. 从 content_info 的 examples 字段获取
        if "examples" in content_info:
            examples = content_info["examples"]
            return self._extract_first_example(examples)
        
        return None
    
    def get_example(self, content_type: str = "application/json") -> Optional[Any]:
        """
        获取指定 content-type 的示例。

        优先从解析后的 schema 对象中获取（支持 FastAPI 生成的 schema），
        其次从 content_info 中获取。

        :param content_type: 内容类型
        :return: 示例值，如果不存在则返回 None
        """
        content_info = self.content.get(content_type, {})
        schema = content_info.get("schema")

        # 优先从 schema 中获取 example（FastAPI 生成的 schema 将 example 放在 schema 对象上）
        example = self._get_example_from_schema(schema)
        if example is not None:
            return example

        # Fallback：从 content_info 中获取（OpenAPI 标准位置）
        return self._get_example_from_content_info(content_info)
    
    def _get_examples_from_schema(self, schema: Any) -> Optional[Dict[str, Any]]:
        """
        从 schema 对象中获取所有示例字典。
        
        :param schema: JSON Schema 对象
        :return: 示例字典，如果不存在则返回 None
        """
        if isinstance(schema, dict):
            examples_value = schema.get("examples")
            if examples_value is not None:
                return examples_value
        return None
    
    def get_examples(self, content_type: str = "application/json") -> Optional[Dict[str, Any]]:
        """
        获取指定 content-type 的所有示例。

        优先从解析后的 schema 对象中获取（支持 FastAPI 生成的 schema），
        其次从 content_info 中获取。

        :param content_type: 内容类型
        :return: 示例字典，如果不存在则返回 None
        """
        content_info = self.content.get(content_type, {})
        schema = content_info.get("schema")

        # 优先从 schema 中获取 examples（FastAPI 生成的 schema 将 examples 放在 schema 对象上）
        examples = self._get_examples_from_schema(schema)
        if examples is not None:
            return examples

        # Fallback：从 content_info 中获取（OpenAPI 标准位置）
        return content_info.get("examples")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status_code": self.status_code,
            "description": self.description,
            "content": self.content,
            "headers": [h.to_dict() for h in self.headers],
        }


@dataclass
class OpenAPIEndpoint:
    """
    OpenAPI 端点模型。
    
    表示一个完整的 API 端点信息，包含路径、方法、参数、请求体等。
    """
    path: str                                    # API 路径（如 "/users/{id}"）
    method: HttpMethod                          # HTTP 方法
    operation_id: str                           # 操作 ID
    summary: Optional[str] = None               # 简要描述
    description: Optional[str] = None           # 详细描述
    tags: List[str] = field(default_factory=list)  # 标签列表
    parameters: List[OpenAPIParameter] = field(default_factory=list)  # 参数列表
    request_body: Optional[OpenAPIRequestBody] = None  # 请求体
    responses: List[OpenAPIResponse] = field(default_factory=list)  # 响应列表
    deprecated: bool = False                    # 是否废弃
    
    def __post_init__(self):
        """后处理：将字符串转换为枚举"""
        if isinstance(self.method, str):
            self.method = HttpMethod(self.method.lower())
    
    def get_path_parameters(self) -> List[OpenAPIParameter]:
        """获取路径参数列表"""
        return [p for p in self.parameters if p.location == ParameterLocation.PATH]
    
    def get_query_parameters(self) -> List[OpenAPIParameter]:
        """获取查询参数列表"""
        return [p for p in self.parameters if p.location == ParameterLocation.QUERY]
    
    def get_header_parameters(self) -> List[OpenAPIParameter]:
        """获取请求头参数列表"""
        return [p for p in self.parameters if p.location == ParameterLocation.HEADER]
    
    def get_required_parameters(self) -> List[OpenAPIParameter]:
        """获取必需参数列表"""
        return [p for p in self.parameters if p.required]
    
    def get_response_by_status(self, status_code: str) -> Optional[OpenAPIResponse]:
        """
        根据状态码获取响应定义。
        
        :param status_code: HTTP 状态码（如 "200", "400"）
        :return: OpenAPIResponse 实例，如果不存在则返回 None
        """
        for response in self.responses:
            if response.status_code == status_code:
                return response
        return None
    
    def get_success_responses(self) -> List[OpenAPIResponse]:
        """获取所有成功响应（状态码 2xx）"""
        return [r for r in self.responses if r.status_code.startswith("2")]
    
    def get_error_responses(self) -> List[OpenAPIResponse]:
        """获取所有错误响应（状态码 4xx 或 5xx）"""
        return [r for r in self.responses if r.status_code.startswith("4") or r.status_code.startswith("5")]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path": self.path,
            "method": self.method.value,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_body": self.request_body.to_dict() if self.request_body else None,
            "responses": [r.to_dict() for r in self.responses],
            "deprecated": self.deprecated,
        }


@dataclass
class ResolvedSchema:
    """
    解析后的 Schema 模型。
    
    表示经过 $ref 引用解析后的完整 JSON Schema。
    """
    schema: Dict[str, Any]                      # 完整的 JSON Schema
    ref_path: Optional[str] = None              # 原始 $ref 路径（如果是从引用解析而来）
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他 schema 名称
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "schema": self.schema,
            "ref_path": self.ref_path,
            "dependencies": self.dependencies,
        }


@dataclass
class GeneratedRequest:
    """
    生成的请求数据模型。
    
    表示为某个 API 端点生成的完整请求数据，包含路径参数、查询参数、请求头和请求体。
    """
    operation_id: str                           # 对应的 operationId
    path: str                                   # API 路径
    method: HttpMethod                          # HTTP 方法
    path_params: Dict[str, Any] = field(default_factory=dict)     # 路径参数
    query_params: Dict[str, Any] = field(default_factory=dict)    # 查询参数
    header_params: Dict[str, Any] = field(default_factory=dict)   # 请求头参数
    request_body: Optional[Any] = None          # 请求体（任意类型）
    metadata: Dict[str, Any] = field(default_factory=dict)        # 元数据（如生成模式、标签等）
    
    def __post_init__(self):
        """后处理：将字符串转换为枚举"""
        if isinstance(self.method, str):
            self.method = HttpMethod(self.method.lower())
    
    def get_url(self, base_url: str = "") -> str:
        """
        构建完整的 URL。
        
        :param base_url: 基础 URL（如 "https://api.example.com"）
        :return: 完整的 URL，包含路径参数替换和查询参数
        """
        # 替换路径参数
        url_path = self.path
        for key, value in self.path_params.items():
            url_path = url_path.replace(f"{{{key}}}", str(value))
        
        # 添加查询参数
        if self.query_params:
            query_str = "&".join(f"{k}={v}" for k, v in self.query_params.items())
            url_path = f"{url_path}?{query_str}"
        
        # 拼接基础 URL
        return f"{base_url}{url_path}" if base_url else url_path
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "path": self.path,
            "method": self.method.value,
            "path_params": self.path_params,
            "query_params": self.query_params,
            "header_params": self.header_params,
            "request_body": self.request_body,
            "metadata": self.metadata,
        }
    
    def content_key(self) -> str:
        """
        生成用于去重的内容键。
        
        基于请求的实际内容（path_params, query_params, header_params, request_body）生成唯一键，
        忽略 metadata 字段。用于判断两个 GeneratedRequest 是否内容相同。
        
        :return: 内容键字符串
        """
        import json
        content = {
            "path": self.path,
            "method": self.method.value,
            "path_params": self.path_params,
            "query_params": self.query_params,
            "header_params": self.header_params,
            "request_body": self.request_body,
        }
        return json.dumps(content, sort_keys=True, ensure_ascii=False)


@dataclass
class GeneratedResponse:
    """
    生成的响应数据模型。
    
    表示为某个 API 端点生成的完整响应数据，包含状态码、响应体和响应头。
    """
    operation_id: str                           # 对应的 operationId
    path: str                                   # API 路径
    method: HttpMethod                          # HTTP 方法
    status_code: str                            # HTTP 状态码（如 "200", "400"）
    response_body: Optional[Any] = None         # 响应体（任意类型）
    response_headers: Dict[str, Any] = field(default_factory=dict)  # 响应头
    content_type: str = "application/json"      # 内容类型
    metadata: Dict[str, Any] = field(default_factory=dict)          # 元数据（如是否来自示例、生成模式等）
    
    def __post_init__(self):
        """后处理：将字符串转换为枚举"""
        if isinstance(self.method, str):
            self.method = HttpMethod(self.method.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "path": self.path,
            "method": self.method.value,
            "status_code": self.status_code,
            "response_body": self.response_body,
            "response_headers": self.response_headers,
            "content_type": self.content_type,
            "metadata": self.metadata,
        }
    
    def is_success(self) -> bool:
        """
        判断是否为成功响应（状态码 2xx）。
        
        :return: 是否为成功响应
        """
        return self.status_code.startswith("2")
    
    def is_error(self) -> bool:
        """
        判断是否为错误响应（状态码 4xx 或 5xx）。
        
        :return: 是否为错误响应
        """
        return self.status_code.startswith("4") or self.status_code.startswith("5")


@dataclass
class OpenAPIDocument:
    """
    OpenAPI 文档模型。
    
    表示完整的 OpenAPI 文档，包含所有端点和组件定义。
    """
    openapi_version: str                        # OpenAPI 版本（如 "3.0.2"）
    info: Dict[str, Any]                        # 文档信息
    paths: Dict[str, Dict[str, OpenAPIEndpoint]] = field(default_factory=dict)  # 路径 → {method: Endpoint}
    components: Dict[str, Any] = field(default_factory=dict)  # 组件定义
    tags: List[Dict[str, Any]] = field(default_factory=list)  # 标签定义
    
    def get_all_endpoints(self) -> List[OpenAPIEndpoint]:
        """获取所有端点列表"""
        endpoints = []
        for path_methods in self.paths.values():
            endpoints.extend(path_methods.values())
        return endpoints
    
    def get_endpoints_by_tag(self, tag: str) -> List[OpenAPIEndpoint]:
        """根据标签获取端点"""
        return [ep for ep in self.get_all_endpoints() if tag in ep.tags]
    
    def get_endpoint_by_operation_id(self, operation_id: str) -> Optional[OpenAPIEndpoint]:
        """根据 operationId 获取端点"""
        for endpoint in self.get_all_endpoints():
            if endpoint.operation_id == operation_id:
                return endpoint
        return None
    
    def get_endpoint_by_path_and_method(
        self, 
        path: str, 
        method: Union[str, HttpMethod]
    ) -> Optional[OpenAPIEndpoint]:
        """
        根据路径和方法获取端点。
        
        :param path: API 路径（如 "/users/{id}"）
        :param method: HTTP 方法（字符串或 HttpMethod 枚举）
        :return: OpenAPIEndpoint 实例，如果不存在则返回 None
        """
        # 规范化 method 为小写字符串
        if isinstance(method, HttpMethod):
            method_str = method.value
        else:
            method_str = method.lower()
        
        # 直接从 paths 字典查找
        path_methods = self.paths.get(path, {})
        return path_methods.get(method_str)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "openapi_version": self.openapi_version,
            "info": self.info,
            "paths": {
                path: {method: ep.to_dict() for method, ep in methods.items()}
                for path, methods in self.paths.items()
            },
            "components": self.components,
            "tags": self.tags,
        }
