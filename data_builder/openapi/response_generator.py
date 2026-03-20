"""
响应数据生成器。

基于 data_builder 的数据生成能力，为 OpenAPI 端点生成 Mock 响应数据。
"""

from typing import Any, Dict, List, Optional, Union

from .. import (
    BuilderConfig,
    CombinationMode,
    CombinationSpec,
    DataBuilder,
    FieldPolicy,
    FixedStrategy,
    RangeStrategy,
    EnumStrategy,
    RandomStringStrategy,
)
from .converter import SchemaConverter
from .models import (
    GeneratedResponse,
    HttpMethod,
    OpenAPIEndpoint,
    OpenAPIResponse,
)


class ResponseDataGenerator:
    """
    响应数据生成器。
    
    为 OpenAPI 端点生成 Mock 响应数据，支持多状态码和响应头生成。
    
    数据生成优先级：field_policies 指定策略 > schema 自动生成（DataBuilder 自动处理 examples）
    """
    
    def __init__(
        self,
        include_headers: bool = True,
        count: int = 1,
        field_policies: Optional[List[Dict[str, Any]]] = None,
        content_type: str = "application/json",
        ref_resolver: Optional[Any] = None,
    ):
        """
        初始化生成器。

        :param include_headers: 是否生成响应头
        :param count: 每个响应生成的数据数量
        :param field_policies: 特定字段的策略配置（优先级最高）
        :param content_type: 响应体的 content-type
        :param ref_resolver: OpenAPI 解析器实例，用于解析 $ref 引用
        """
        self.include_headers = include_headers
        self.count = count
        self.field_policies = field_policies or []
        self.content_type = content_type
        self.ref_resolver = ref_resolver
    
    def generate_for_endpoint(
        self,
        endpoint: OpenAPIEndpoint,
        status_codes: Optional[List[str]] = None,
        count: Optional[int] = None,
    ) -> List[GeneratedResponse]:
        """
        为单个端点生成响应数据。
        
        :param endpoint: OpenAPIEndpoint 实例
        :param status_codes: 指定生成的状态码列表（如 ["200", "400"]），为 None 则生成所有定义的响应
        :param count: 覆盖默认的生成数量
        :return: GeneratedResponse 列表
        """
        count = count or self.count
        
        # 确定要生成的响应
        if status_codes:
            responses = [
                r for r in endpoint.responses 
                if r.status_code in status_codes
            ]
        else:
            responses = endpoint.responses
        
        # 为每个响应生成数据
        all_responses = []
        for response in responses:
            generated = self._generate_for_single_response(
                endpoint, response, count
            )
            all_responses.extend(generated)
        
        return all_responses
    
    def _generate_for_single_response(
        self,
        endpoint: OpenAPIEndpoint,
        response: OpenAPIResponse,
        count: int,
    ) -> List[GeneratedResponse]:
        """
        为单个响应定义生成数据。
        
        :param endpoint: OpenAPIEndpoint 实例
        :param response: OpenAPIResponse 实例
        :param count: 生成数量
        :return: GeneratedResponse 列表
        
        数据生成优先级：
        1. field_policies 指定策略（优先级最高）
        2. schema 自动生成（DataBuilder 自动处理 examples）
        
        特殊处理：
        - 对象类型的 examples：由 DataBuilder 自动处理
        - 非对象类型的 examples：直接使用（DataBuilder 不处理非对象 examples）
        """
        # 提取示例（用于特殊处理非对象类型）
        example = response.get_example(self.content_type)
        
        # 提取响应体 schema（已包含 content 级别的 example/examples）
        response_schema = SchemaConverter.extract_response_schema(
            response, self.content_type, self.ref_resolver
        )
        
        # 提取响应头 schema
        headers_schema = None
        if self.include_headers and response.headers:
            headers_schema = SchemaConverter.extract_response_headers_schema(
                response.headers, self.ref_resolver
            )
        
        # 生成响应体数据
        # 特殊处理：区分不同类型的示例
        if example is not None:
            if isinstance(example, list):
                # 数组示例：直接使用
                body_data_list = [example] * count
                has_examples = True
            elif isinstance(example, dict):
                # 对象示例：交给 DataBuilder 处理（会自动处理 schema 中的 examples）
                if response_schema:
                    # 将示例合并到 schema 中
                    if "examples" not in response_schema:
                        response_schema["examples"] = [example]
                    body_data_list = self._generate_schema_data(
                        response_schema, count, f"{endpoint.operation_id}_response_body"
                    )
                    has_examples = True
                else:
                    # 无 schema，直接使用示例
                    body_data_list = [example] * count
                    has_examples = True
            elif isinstance(example, (str, int, float, bool)):
                # 原始类型示例：检查 schema 类型是否匹配
                if response_schema:
                    schema_type = response_schema.get("type")
                    # 类型匹配则直接使用，否则按 schema 生成
                    if schema_type and self._is_type_compatible(example, schema_type):
                        body_data_list = [example] * count
                        has_examples = True
                    else:
                        # 类型不匹配，移除 schema 中的 examples 后按 schema 生成
                        # 避免不兼容的示例被 DataBuilder 使用
                        schema_without_examples = {k: v for k, v in response_schema.items() if k != "examples"}
                        body_data_list = self._generate_schema_data(
                            schema_without_examples, count, f"{endpoint.operation_id}_response_body"
                        )
                        has_examples = False
                else:
                    # 无 schema，直接使用示例
                    body_data_list = [example] * count
                    has_examples = True
            else:
                # 其他类型（如 None），按 schema 生成
                if response_schema:
                    body_data_list = self._generate_schema_data(
                        response_schema, count, f"{endpoint.operation_id}_response_body"
                    )
                    has_examples = "examples" in response_schema
                else:
                    body_data_list = [None] * count
                    has_examples = False
        elif response_schema:
            # 无示例：统一使用 schema 生成
            body_data_list = self._generate_schema_data(
                response_schema, count, f"{endpoint.operation_id}_response_body"
            )
            has_examples = "examples" in response_schema
        else:
            body_data_list = [None] * count
            has_examples = False
        
        # 生成响应头
        if headers_schema:
            headers_data_list = self._generate_schema_data(
                headers_schema, count, f"{endpoint.operation_id}_response_headers"
            )
        else:
            headers_data_list = [{}] * count
        
        # 构建响应数据
        generated_responses = []
        for i in range(count):
            body_data = body_data_list[i] if i < len(body_data_list) else None
            headers_data = headers_data_list[i] if i < len(headers_data_list) else {}
            
            generated = GeneratedResponse(
                operation_id=endpoint.operation_id,
                path=endpoint.path,
                method=endpoint.method,
                status_code=response.status_code,
                response_body=body_data,
                response_headers=headers_data,
                content_type=self.content_type,
                metadata={
                    "from_example": has_examples,
                    "endpoint_summary": endpoint.summary,
                    "tags": endpoint.tags,
                },
            )
            generated_responses.append(generated)
        
        return generated_responses
    
    def _generate_schema_data(
        self,
        schema: Dict[str, Any],
        count: int,
        context: str,
    ) -> List[Any]:
        """
        基于 schema 生成数据。
        
        :param schema: JSON Schema
        :param count: 生成数量
        :param context: 上下文标识（用于日志）
        :return: 数据列表
        """
        # 构建 DataBuilder 配置
        config = self._build_builder_config(schema, count, context)
        
        # 创建 DataBuilder 并生成数据
        builder = DataBuilder(schema, config)
        
        try:
            data = builder.build(count=count)
            return data
        except Exception as e:
            # 如果生成失败，返回默认值
            print(f"生成 {context} 数据失败：{e}")
            return [None] * count
    
    def _is_type_compatible(self, example: Any, schema_type: str) -> bool:
        """
        检查示例值类型与 schema 类型是否兼容。
        
        :param example: 示例值
        :param schema_type: schema 类型
        :return: 是否兼容
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected_type = type_mapping.get(schema_type)
        if expected_type is None:
            # 未知类型，认为兼容
            return True
        
        # 特殊处理：integer 类型也接受 bool（Python 中 bool 是 int 的子类）
        if schema_type == "integer" and isinstance(example, bool):
            return False
        
        # 特殊处理：number 类型包含 integer
        if schema_type == "number" and isinstance(example, int) and not isinstance(example, bool):
            return True
        
        return isinstance(example, expected_type)
    
    def _build_builder_config(
        self,
        schema: Dict[str, Any],
        count: int,
        context: str,
    ) -> BuilderConfig:
        """
        构建 DataBuilder 配置。
        
        :param schema: JSON Schema
        :param count: 生成数量
        :param context: 上下文标识
        :return: BuilderConfig 实例
        """
        policies = []
        
        # 应用用户自定义策略（覆盖自动推导）
        for policy_config in self.field_policies:
            policies.append(FieldPolicy(
                path=policy_config["path"],
                strategy=self._create_strategy_from_config(policy_config["strategy"]),
            ))
        
        return BuilderConfig(
            policies=policies,
            count=count,
        )
    
    def _create_strategy_from_config(self, strategy_config: Dict[str, Any]) -> Any:
        """
        从配置创建策略实例。
        
        :param strategy_config: 策略配置字典
        :return: Strategy 实例
        """
        strategy_type = strategy_config.get("type", "fixed")
        
        if strategy_type == "fixed":
            value = strategy_config.get("value")
            return FixedStrategy(value=value)
        
        elif strategy_type == "range":
            # RangeStrategy: {"type": "range", "min_val": 0, "max_val": 100}
            min_val = strategy_config.get("min_val") or strategy_config.get("min") or 0
            max_val = strategy_config.get("max_val") or strategy_config.get("max") or 100
            is_float = strategy_config.get("is_float", False)
            precision = strategy_config.get("precision", 2)
            return RangeStrategy(
                min_val=min_val, 
                max_val=max_val, 
                is_float=is_float, 
                precision=precision
            )
        
        elif strategy_type == "enum":
            # EnumStrategy: {"type": "enum", "values": ["a", "b", "c"]}
            values = strategy_config.get("values", [])
            return EnumStrategy(choices=values)
        
        elif strategy_type == "random_string":
            # RandomStringStrategy: {"type": "random_string", "length": 10}
            length = strategy_config.get("length", 8)
            return RandomStringStrategy(length=length)
        
        else:
            # 不支持的类型，使用默认值或固定值
            value = strategy_config.get("value")
            return FixedStrategy(value=value)
    
    def generate_for_document(
        self,
        endpoints: List[OpenAPIEndpoint],
        status_codes: Optional[List[str]] = None,
        count_per_endpoint: Optional[int] = None,
    ) -> Dict[str, List[GeneratedResponse]]:
        """
        为多个端点批量生成响应数据。
        
        :param endpoints: OpenAPIEndpoint 列表
        :param status_codes: 指定生成的状态码列表
        :param count_per_endpoint: 每个端点的生成数量
        :return: {operation_id: List[GeneratedResponse]} 字典
        """
        result = {}
        
        for endpoint in endpoints:
            responses = self.generate_for_endpoint(endpoint, status_codes, count_per_endpoint)
            result[endpoint.operation_id] = responses
        
        return result
