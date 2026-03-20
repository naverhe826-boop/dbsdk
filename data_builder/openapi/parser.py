"""
OpenAPI 文档解析器。

负责解析 OpenAPI 3.x 文档，提取 API 端点信息，并解析 $ref 引用。
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .models import (
    HttpMethod,
    OpenAPIDocument,
    OpenAPIEndpoint,
    OpenAPIParameter,
    OpenAPIRequestBody,
    OpenAPIResponse,
    OpenAPIResponseHeader,
    ParameterLocation,
)


class OpenAPIParser:
    """
    OpenAPI 文档解析器。
    
    支持解析 OpenAPI 3.x 规范文档，提取端点信息并解析 $ref 引用。
    """
    
    def __init__(self, document: Dict[str, Any]):
        """
        初始化解析器。
        
        :param document: OpenAPI 文档字典
        """
        self.document = document
        self.openapi_version = document.get("openapi", "3.0.0")
        self.info = document.get("info", {})
        self.paths = document.get("paths", {})
        self.components = document.get("components", {})
        self.tags = document.get("tags", [])
        
        # 缓存已解析的 $ref
        self._ref_cache: Dict[str, Any] = {}
        
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "OpenAPIParser":
        """
        从文件创建解析器。
        
        :param file_path: OpenAPI 文档文件路径（JSON 或 YAML）
        :return: OpenAPIParser 实例
        """
        file_path = Path(file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 根据文件扩展名判断格式
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            try:
                import yaml
                document = yaml.safe_load(content)
            except ImportError:
                raise ImportError("需要安装 PyYAML 库来解析 YAML 文件：pip install pyyaml")
        else:
            # 默认为 JSON 格式
            document = json.loads(content)
        
        return cls(document)
    
    @classmethod
    def from_dict(cls, document: Dict[str, Any]) -> "OpenAPIParser":
        """
        从字典创建解析器。
        
        :param document: OpenAPI 文档字典
        :return: OpenAPIParser 实例
        """
        return cls(document)
    
    def parse(self) -> OpenAPIDocument:
        """
        解析 OpenAPI 文档。
        
        :return: OpenAPIDocument 实例
        """
        parsed_paths = {}
        
        for path, path_item in self.paths.items():
            parsed_paths[path] = self._parse_path_item(path, path_item)
        
        return OpenAPIDocument(
            openapi_version=self.openapi_version,
            info=self.info,
            paths=parsed_paths,
            components=self.components,
            tags=self.tags,
        )
    
    def _parse_path_item(self, path: str, path_item: Dict[str, Any]) -> Dict[str, OpenAPIEndpoint]:
        """
        解析路径项。
        
        :param path: API 路径
        :param path_item: 路径项字典
        :return: {method: OpenAPIEndpoint} 字典
        """
        endpoints = {}
        
        # OpenAPI 3.0 支持的 HTTP 方法
        http_methods = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]
        
        for method_str in http_methods:
            if method_str not in path_item:
                continue
            
            operation = path_item[method_str]
            endpoint = self._parse_operation(path, method_str, operation, path_item)
            endpoints[method_str] = endpoint
        
        return endpoints
    
    def _parse_operation(
        self, 
        path: str, 
        method: str, 
        operation: Dict[str, Any],
        path_item: Dict[str, Any]
    ) -> OpenAPIEndpoint:
        """
        解析操作（Operation）。
        
        :param path: API 路径
        :param method: HTTP 方法
        :param operation: 操作字典
        :param path_item: 父级路径项（包含共享参数）
        :return: OpenAPIEndpoint 实例
        """
        # 提取基本信息
        operation_id = operation.get("operationId", f"{method}_{path}")
        summary = operation.get("summary")
        description = operation.get("description")
        tags = operation.get("tags", [])
        deprecated = operation.get("deprecated", False)
        responses_raw = operation.get("responses", {})
        
        # 解析参数（合并路径级和操作级参数）
        parameters = self._parse_parameters(operation, path_item)
        
        # 解析请求体
        request_body = self._parse_request_body(operation)
        
        # 解析响应
        responses = self._parse_responses(responses_raw)
        
        return OpenAPIEndpoint(
            path=path,
            method=HttpMethod(method.lower()),
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            deprecated=deprecated,
        )
    
    def _parse_parameters(
        self, 
        operation: Dict[str, Any], 
        path_item: Dict[str, Any]
    ) -> List[OpenAPIParameter]:
        """
        解析参数列表。
        
        参数可能定义在两个地方：
        1. 路径项级别（共享参数）
        2. 操作级别（特定参数）
        
        :param operation: 操作字典
        :param path_item: 路径项字典
        :return: OpenAPIParameter 列表
        """
        # 收集所有参数（先路径级，后操作级）
        all_params = []
        
        # 路径级参数
        if "parameters" in path_item:
            all_params.extend(path_item["parameters"])
        
        # 操作级参数（可能覆盖路径级参数）
        if "parameters" in operation:
            all_params.extend(operation["parameters"])
        
        # 解析参数，去重（同名、同位置的参数只保留后者）
        seen = set()
        parameters = []
        
        for param in reversed(all_params):  # 反向遍历，后者优先
            # 处理 $ref 引用
            param = self._resolve_ref(param)
            
            name = param.get("name")
            location = param.get("in")
            
            # 构建唯一标识
            key = f"{name}:{location}"
            
            if key not in seen:
                seen.add(key)
                parameters.insert(0, self._create_parameter(param))
        
        return parameters
    
    def _create_parameter(self, param: Dict[str, Any]) -> OpenAPIParameter:
        """
        创建 OpenAPIParameter 实例。
        
        :param param: 参数字典
        :return: OpenAPIParameter 实例
        """
        # 解析 schema（可能包含 $ref）
        schema = param.get("schema", {})
        schema = self._resolve_ref(schema)
        
        return OpenAPIParameter(
            name=param.get("name", ""),
            location=ParameterLocation(param.get("in", "query")),
            schema=schema,
            required=param.get("required", False),
            description=param.get("description"),
            deprecated=param.get("deprecated", False),
            style=param.get("style"),
            explode=param.get("explode"),
            example=param.get("example"),
            examples=param.get("examples"),
        )
    
    def _parse_request_body(self, operation: Dict[str, Any]) -> Optional[OpenAPIRequestBody]:
        """
        解析请求体。
        
        :param operation: 操作字典
        :return: OpenAPIRequestBody 实例，如果不存在则返回 None
        """
        if "requestBody" not in operation:
            return None
        
        request_body = operation["requestBody"]
        request_body = self._resolve_ref(request_body)
        
        # 提取 content
        content = request_body.get("content", {})
        
        # 解析每个 content-type 的 schema
        parsed_content = {}
        for content_type, content_info in content.items():
            content_info = self._resolve_ref(content_info)
            
            parsed_content[content_type] = {
                "schema": self._resolve_ref(content_info.get("schema", {})),
                "example": content_info.get("example"),
                "examples": content_info.get("examples"),
            }
        
        return OpenAPIRequestBody(
            content=parsed_content,
            required=request_body.get("required", False),
            description=request_body.get("description"),
        )
    
    def _parse_responses(self, responses_raw: Dict[str, Any]) -> List[OpenAPIResponse]:
        """
        解析响应定义。
        
        :param responses_raw: 响应定义字典（{status_code: response_object}）
        :return: OpenAPIResponse 列表
        """
        responses = []
        
        for status_code, response_obj in responses_raw.items():
            # 处理 $ref 引用
            response_obj = self._resolve_ref(response_obj)
            
            # 解析单个响应
            response = self._parse_single_response(status_code, response_obj)
            responses.append(response)
        
        return responses
    
    def _parse_single_response(
        self, 
        status_code: str, 
        response_obj: Dict[str, Any]
    ) -> OpenAPIResponse:
        """
        解析单个响应定义。
        
        :param status_code: HTTP 状态码
        :param response_obj: 响应对象字典
        :return: OpenAPIResponse 实例
        """
        description = response_obj.get("description")
        
        # 解析 content
        content_raw = response_obj.get("content", {})
        parsed_content = {}
        
        for content_type, content_info in content_raw.items():
            content_info = self._resolve_ref(content_info)
            
            parsed_content[content_type] = {
                "schema": self._resolve_ref(content_info.get("schema", {})),
                "example": content_info.get("example"),
                "examples": content_info.get("examples"),
            }
        
        # 解析 headers
        headers_raw = response_obj.get("headers", {})
        headers = self._parse_response_headers(headers_raw)
        
        return OpenAPIResponse(
            status_code=status_code,
            description=description,
            content=parsed_content,
            headers=headers,
        )
    
    def _parse_response_headers(
        self, 
        headers_raw: Dict[str, Any]
    ) -> List[OpenAPIResponseHeader]:
        """
        解析响应头定义。
        
        :param headers_raw: 响应头字典（{header_name: header_object}）
        :return: OpenAPIResponseHeader 列表
        """
        headers = []
        
        for header_name, header_obj in headers_raw.items():
            # 处理 $ref 引用
            header_obj = self._resolve_ref(header_obj)
            
            # 提取 schema
            schema = header_obj.get("schema", {})
            schema = self._resolve_ref(schema)
            
            header = OpenAPIResponseHeader(
                name=header_name,
                schema=schema,
                description=header_obj.get("description"),
                required=header_obj.get("required", False),
                deprecated=header_obj.get("deprecated", False),
                example=header_obj.get("example"),
                examples=header_obj.get("examples"),
            )
            headers.append(header)
        
        return headers
    
    def _resolve_ref(self, obj: Any, visited: Optional[Set[str]] = None, depth: int = 0) -> Any:
        """
        递归解析 $ref 引用。
        
        支持的引用格式：
        - "#/components/schemas/User"
        - "#/parameters/userId"
        - "#/paths/~1users~1{id}/get/parameters/0"
        
        :param obj: 待解析的对象
        :param visited: 已访问的引用路径集合（用于检测循环引用）
        :param depth: 当前递归深度（用于防止无限递归）
        :return: 解析后的对象
        """
        if visited is None:
            visited = set()
        
        # 最大深度限制：防止无限递归
        MAX_DEPTH = 20
        if depth >= MAX_DEPTH:
            # 达到最大深度时返回一个占位符 schema，避免无限递归
            return {"type": "object", "properties": {}, "description": "Maximum recursion depth reached"}
        
        # 非字典对象直接返回
        if not isinstance(obj, dict):
            return obj
        
        # 如果包含 $ref，解析引用
        if "$ref" in obj:
            ref_path = obj["$ref"]
            
            # 检查循环引用
            if ref_path in visited:
                # 循环引用是合法的（递归结构）
                # 当深度较大时返回占位符，否则保留 $ref 引用
                if depth >= 10:  # 较浅的深度限制用于循环引用
                    # 返回一个合理的占位符 schema
                    return {"type": "object", "properties": {}, "description": f"Circular reference to {ref_path}"}
                else:
                    # 保留 $ref 引用，让递归结构保持完整
                    return {"$ref": ref_path}
            
            # 检查缓存
            if ref_path in self._ref_cache:
                return self._ref_cache[ref_path]
            
            # 解析引用路径
            resolved = self._resolve_ref_path(ref_path)
            
            # 缓存结果（先缓存未解析的引用，避免无限递归）
            self._ref_cache[ref_path] = resolved
            
            # 递归解析（合并 $ref 和其他属性）
            visited_copy = visited.copy()
            visited_copy.add(ref_path)
            
            resolved = self._resolve_ref(resolved, visited_copy, depth + 1)
            
            # 更新缓存
            self._ref_cache[ref_path] = resolved
            
            # 合并 $ref 和其他属性（OpenAPI 3.1 支持）
            result = dict(resolved)
            for key, value in obj.items():
                if key != "$ref":
                    result[key] = value
            
            return result
        
        # 递归解析字典的值
        return {key: self._resolve_ref(value, visited) for key, value in obj.items()}
    
    def _resolve_ref_path(self, ref_path: str) -> Any:
        """
        解析 $ref 路径。
        
        :param ref_path: 引用路径（如 "#/components/schemas/User"）
        :return: 引用对象
        """
        # 仅支持内部引用（以 #/ 开头）
        if not ref_path.startswith("#/"):
            raise ValueError(f"不支持的引用格式：{ref_path}（仅支持内部引用 #/...）")
        
        # 移除 #/ 前缀
        path_parts = ref_path[2:].split("/")
        
        # 处理路径中的转义字符（如 ~1 表示 /，~0 表示 ~）
        path_parts = [
            part.replace("~1", "/").replace("~0", "~")
            for part in path_parts
        ]
        
        # 在文档中查找引用
        current = self.document
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"无法解析引用路径：{ref_path}（在 '{part}' 处失败）")
        
        return current
    
    def get_schema_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取组件 schema。
        
        :param name: schema 名称
        :return: schema 字典，如果不存在则返回 None
        """
        schemas = self.components.get("schemas", {})
        return schemas.get(name)
    
    def get_parameter_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取组件参数。
        
        :param name: 参数名称
        :return: 参数字典，如果不存在则返回 None
        """
        parameters = self.components.get("parameters", {})
        return parameters.get(name)
