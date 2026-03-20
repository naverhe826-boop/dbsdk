"""
Schema 转换器。

将 OpenAPI Schema 转换为标准 JSON Schema 格式。
"""

import copy
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    OpenAPIEndpoint,
    OpenAPIParameter,
    OpenAPIResponse,
    OpenAPIResponseHeader,
    ParameterLocation,
)


class SchemaConverter:
    """
    Schema 转换器。
    
    负责将 OpenAPI Schema 转换为标准 JSON Schema 格式，
    并处理 OpenAPI 特有字段（如 nullable、discriminator）。
    """
    
    @staticmethod
    def convert_openapi_schema_to_json_schema(
        openapi_schema: Dict[str, Any],
        convert_nullable: bool = True,
        preserve_openapi_fields: bool = False,
        ref_resolver: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        将 OpenAPI Schema 转换为 JSON Schema。
        
        OpenAPI 3.0 与 JSON Schema 的主要差异：
        1. nullable 字段 → type 数组包含 "null"
        2. discriminator 字段 → oneOf/anyOf 的鉴别器
        3. example 字段 → examples 数组
        4. externalDocs 等字段在 JSON Schema 中不存在
        
        :param openapi_schema: OpenAPI Schema 字典
        :param convert_nullable: 是否转换 nullable 字段
        :param preserve_openapi_fields: 是否保留 OpenAPI 特有字段
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: JSON Schema 字典
        """
        if not isinstance(openapi_schema, dict):
            return openapi_schema
        
        # 处理 $ref 引用
        if "$ref" in openapi_schema and ref_resolver is not None:
            ref_path = openapi_schema["$ref"]
            # 如果是循环引用（已经解析过的 $ref），跳过保留
            if not ref_path.startswith("#/components/"):
                # 已经是内联的 $ref，递归处理
                pass
            else:
                # 尝试从解析器获取完整定义
                try:
                    resolved = ref_resolver.get_schema_by_name(ref_path.split("/")[-1])
                    if resolved:
                        # 递归处理解析后的 schema
                        return SchemaConverter.convert_openapi_schema_to_json_schema(
                            resolved, convert_nullable, preserve_openapi_fields, ref_resolver
                        )
                except Exception:
                    # 解析失败，保留原样（让 DataBuilder 处理）
                    pass
        
        # 深拷贝避免修改原对象
        json_schema = copy.deepcopy(openapi_schema)
        
        # 处理 nullable 字段
        if convert_nullable and "nullable" in json_schema:
            nullable = json_schema.pop("nullable")
            if nullable:
                # 将 type 转换为数组形式，包含 "null"
                if "type" in json_schema:
                    current_type = json_schema["type"]
                    if isinstance(current_type, str):
                        json_schema["type"] = [current_type, "null"]
                    elif isinstance(current_type, list):
                        if "null" not in current_type:
                            json_schema["type"] = current_type + ["null"]
                elif "oneOf" in json_schema:
                    # oneOf 情况：添加 null 类型选项
                    json_schema["oneOf"].append({"type": "null"})
                elif "anyOf" in json_schema:
                    # anyOf 情况：添加 null 类型选项
                    json_schema["anyOf"].append({"type": "null"})
                elif "allOf" in json_schema:
                    # allOf 情况：转换为 oneOf 包装
                    # allOf 表示必须同时满足所有条件，添加 null 需要特殊处理
                    original_all_of = json_schema.pop("allOf")
                    json_schema["oneOf"] = [
                        {"allOf": original_all_of},
                        {"type": "null"}
                    ]
                else:
                    # 无 type 也无复合类型，添加 type: "null"
                    json_schema["type"] = "null"
        
        # 处理 example 字段
        if "example" in json_schema:
            example = json_schema.pop("example")
            # JSON Schema Draft 2020-12 使用 examples 数组
            if "examples" not in json_schema:
                json_schema["examples"] = []
            if isinstance(example, list):
                json_schema["examples"].extend(example)
            else:
                json_schema["examples"].append(example)
        
        # 处理 discriminator 字段（保留但不转换，因为 JSON Schema 也支持）
        # discriminator 用于多态类型，在 oneOf/anyOf 中指定鉴别字段
        
        # 移除 OpenAPI 特有字段（如果不需要保留）
        if not preserve_openapi_fields:
            openapi_specific_fields = [
                "discriminator",
                "xml",
                "externalDocs",
                "deprecated",
                "readOnly",
                "writeOnly",
            ]
            for field in openapi_specific_fields:
                # 不移除 deprecated、readOnly、writeOnly，因为它们有语义价值
                if field in ["xml", "externalDocs"]:
                    json_schema.pop(field, None)
        
        # 递归处理嵌套结构
        for key, value in json_schema.items():
            if key in ["properties", "patternProperties"]:
                # 处理对象属性
                if isinstance(value, dict):
                    json_schema[key] = {
                        prop_name: SchemaConverter.convert_openapi_schema_to_json_schema(
                            prop_schema, convert_nullable, preserve_openapi_fields, ref_resolver
                        )
                        for prop_name, prop_schema in value.items()
                    }
            elif key in ["items", "additionalProperties"]:
                # 处理数组项和额外属性
                json_schema[key] = SchemaConverter.convert_openapi_schema_to_json_schema(
                    value, convert_nullable, preserve_openapi_fields, ref_resolver
                )
            elif key in ["oneOf", "anyOf", "allOf"]:
                # 处理组合 schema
                if isinstance(value, list):
                    json_schema[key] = [
                        SchemaConverter.convert_openapi_schema_to_json_schema(
                            sub_schema, convert_nullable, preserve_openapi_fields, ref_resolver
                        )
                        for sub_schema in value
                    ]
        
        return json_schema
    
    @staticmethod
    def extract_parameters_schema(
        parameters: List[OpenAPIParameter],
        location: ParameterLocation,
        include_optional: bool = True,
        ref_resolver: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        提取参数列表的 JSON Schema。

        将参数列表转换为对象形式的 JSON Schema，
        每个参数对应一个属性。

        :param parameters: 参数列表
        :param location: 参数位置
        :param include_optional: 是否包含可选参数
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: JSON Schema 字典
        """
        # 筛选指定位置的参数
        filtered_params = [p for p in parameters if p.location == location]

        # 根据配置筛选必需/可选参数
        if not include_optional:
            filtered_params = [p for p in filtered_params if p.required]

        if not filtered_params:
            return {"type": "object", "properties": {}, "required": []}

        # 构建对象 schema
        properties = {}
        required = []

        for param in filtered_params:
            # 转换 schema
            prop_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
                param.schema, ref_resolver=ref_resolver
            )

            # 添加描述
            if param.description:
                prop_schema["description"] = param.description

            properties[param.name] = prop_schema

            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    
    @staticmethod
    def extract_request_body_schema(
        request_body_schema: Dict[str, Any],
        include_optional: bool = True,
        ref_resolver: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        提取请求体的 JSON Schema。

        :param request_body_schema: 请求体 schema
        :param include_optional: 是否包含可选字段
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: JSON Schema 字典
        """
        # 转换为 JSON Schema
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
            request_body_schema, ref_resolver=ref_resolver
        )

        # 根据 include_optional 处理 required 字段
        if not include_optional:
            # 移除 required 字段，只生成必需字段
            json_schema.pop("required", None)

        return json_schema
    
    @staticmethod
    def extract_response_schema(
        response: OpenAPIResponse,
        content_type: str = "application/json",
        ref_resolver: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        提取响应体的 JSON Schema。

        :param response: OpenAPIResponse 实例
        :param content_type: 内容类型，如 "application/json"
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: JSON Schema 字典，如果不存在则返回 None
        """
        schema = response.get_schema(content_type)
        content_example = response.get_example(content_type)
        
        # 如果既没有 schema 也没有 example，返回 None
        if not schema and content_example is None:
            return None
        
        # 如果没有 schema 但有 example，构造一个包含 examples 的 schema
        if not schema and content_example is not None:
            # 构造一个最简单的 schema，只包含 examples
            json_schema = {}
        elif schema:
            # 转换为 JSON Schema
            json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
                schema, ref_resolver=ref_resolver
            )
        else:
            json_schema = {}
        
        # 处理 content 级别的 example/examples
        # 将 content 级别的 example/examples 合并到 schema 中，交给 DataBuilder 统一处理
        if content_example is not None and json_schema is not None:
            # 将 content 级别的 example 注入到 schema 的 examples 中
            if "examples" not in json_schema:
                json_schema["examples"] = []
            if isinstance(content_example, list):
                json_schema["examples"].extend(content_example)
            else:
                json_schema["examples"].append(content_example)
        
        return json_schema
    
    @staticmethod
    def extract_response_headers_schema(
        headers: List[OpenAPIResponseHeader],
        ref_resolver: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        提取响应头的 JSON Schema。

        将响应头列表转换为对象形式的 JSON Schema，
        每个响应头对应一个属性。

        :param headers: OpenAPIResponseHeader 列表
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: JSON Schema 字典
        """
        if not headers:
            return {"type": "object", "properties": {}, "required": []}
        
        # 构建对象 schema
        properties = {}
        required = []
        
        for header in headers:
            # 转换 schema
            prop_schema = SchemaConverter.convert_openapi_schema_to_json_schema(
                header.schema, ref_resolver=ref_resolver
            )
            
            # 添加描述
            if header.description:
                prop_schema["description"] = header.description
            
            # 添加示例
            if header.example:
                prop_schema["example"] = header.example
            if header.examples:
                prop_schema["examples"] = header.examples
            
            properties[header.name] = prop_schema
            
            if header.required:
                required.append(header.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    
    @staticmethod
    def extract_required_fields(schema: Dict[str, Any]) -> Set[str]:
        """
        提取 schema 中的必需字段。
        
        :param schema: JSON Schema 字典
        :return: 必需字段名称集合
        """
        required = schema.get("required", [])
        return set(required) if isinstance(required, list) else set()
    
    @staticmethod
    def extract_optional_fields(schema: Dict[str, Any]) -> Set[str]:
        """
        提取 schema 中的可选字段。
        
        :param schema: JSON Schema 字典
        :return: 可选字段名称集合
        """
        properties = schema.get("properties", {})
        required = SchemaConverter.extract_required_fields(schema)
        
        return set(properties.keys()) - required
    
    @staticmethod
    def create_combined_schema_for_endpoint(
        endpoint: OpenAPIEndpoint,
        include_query_params: bool = True,
        include_path_params: bool = True,
        include_header_params: bool = False,
        include_request_body: bool = True,
        include_optional_fields: bool = True,
        content_type: str = "application/json",
        ref_resolver: Optional[Any] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        为端点创建组合的请求数据 schema。

        根据配置提取并转换路径参数、查询参数、请求头和请求体的 schema。

        :param endpoint: OpenAPIEndpoint 实例
        :param include_query_params: 是否包含查询参数
        :param include_path_params: 是否包含路径参数
        :param include_header_params: 是否包含请求头参数
        :param include_request_body: 是否包含请求体
        :param include_optional_fields: 是否包含可选字段
        :param content_type: 请求体的 content-type
        :param ref_resolver: 可选的 $ref 解析器（OpenAPIParser 实例）
        :return: (path_params_schema, query_params_schema, header_params_schema, request_body_schema)
        """
        # 提取路径参数 schema
        path_params_schema = {}
        if include_path_params:
            path_params_schema = SchemaConverter.extract_parameters_schema(
                endpoint.parameters,
                ParameterLocation.PATH,
                include_optional=True,  # 路径参数总是必需的
                ref_resolver=ref_resolver,
            )

        # 提取查询参数 schema
        query_params_schema = {}
        if include_query_params:
            query_params_schema = SchemaConverter.extract_parameters_schema(
                endpoint.parameters,
                ParameterLocation.QUERY,
                include_optional_fields,
                ref_resolver=ref_resolver,
            )

        # 提取请求头参数 schema
        header_params_schema = {}
        if include_header_params:
            header_params_schema = SchemaConverter.extract_parameters_schema(
                endpoint.parameters,
                ParameterLocation.HEADER,
                include_optional_fields,
                ref_resolver=ref_resolver,
            )

        # 提取请求体 schema
        request_body_schema = None
        if include_request_body and endpoint.request_body:
            raw_schema = endpoint.request_body.get_schema(content_type)
            if raw_schema:
                request_body_schema = SchemaConverter.extract_request_body_schema(
                    raw_schema, include_optional_fields, ref_resolver
                )
                
                # 处理 content 级别的 example
                # 如果 requestBody content 中有 example，注入到 schema 中
                content_example = endpoint.request_body.get_example(content_type)
                if content_example is not None and request_body_schema is not None:
                    # 将 content 级别的 example 注入到 schema 的 examples 中
                    if "examples" not in request_body_schema:
                        request_body_schema["examples"] = []
                    if isinstance(content_example, list):
                        request_body_schema["examples"].extend(content_example)
                    else:
                        request_body_schema["examples"].append(content_example)

        return (
            path_params_schema,
            query_params_schema,
            header_params_schema,
            request_body_schema,
        )
    
    @staticmethod
    def detect_enum_fields(schema: Dict[str, Any]) -> List[str]:
        """
        检测 schema 中包含 enum 约束的字段。
        
        :param schema: JSON Schema 字典
        :return: 包含 enum 约束的字段名称列表
        """
        enum_fields = []
        properties = schema.get("properties", {})
        
        for prop_name, prop_schema in properties.items():
            if "enum" in prop_schema:
                enum_fields.append(prop_name)
        
        return enum_fields
    
    @staticmethod
    def detect_boundary_fields(schema: Dict[str, Any]) -> List[str]:
        """
        检测 schema 中包含边界约束的字段。
        
        边界约束包括：
        - 数值：minimum, maximum, exclusiveMinimum, exclusiveMaximum
        - 字符串：minLength, maxLength
        - 数组：minItems, maxItems
        - 对象：minProperties, maxProperties
        
        :param schema: JSON Schema 字典
        :return: 包含边界约束的字段名称列表
        """
        boundary_fields = []
        properties = schema.get("properties", {})
        
        boundary_keywords = [
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
            "minLength", "maxLength",
            "minItems", "maxItems",
            "minProperties", "maxProperties",
        ]
        
        for prop_name, prop_schema in properties.items():
            if any(keyword in prop_schema for keyword in boundary_keywords):
                boundary_fields.append(prop_name)
        
        return boundary_fields
    
    @staticmethod
    def detect_pattern_fields(schema: Dict[str, Any]) -> List[str]:
        """
        检测 schema 中包含 pattern 约束的字段。
        
        :param schema: JSON Schema 字典
        :return: 包含 pattern 约束的字段名称列表
        """
        pattern_fields = []
        properties = schema.get("properties", {})
        
        for prop_name, prop_schema in properties.items():
            if "pattern" in prop_schema:
                pattern_fields.append(prop_name)
        
        return pattern_fields
