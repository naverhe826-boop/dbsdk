"""
请求数据生成器。

基于 data_builder 的数据生成能力，为 OpenAPI 端点生成测试请求数据。
"""

from typing import Any, Dict, List, Optional, Union

from .. import (
    BuilderConfig,
    CombinationMode,
    CombinationSpec,
    DataBuilder,
    FieldPolicy,
)
from .converter import SchemaConverter
from .models import (
    GeneratedRequest,
    HttpMethod,
    OpenAPIEndpoint,
    ParameterLocation,
)


class RequestDataGenerator:
    """
    请求数据生成器。
    
    为 OpenAPI 端点生成测试请求数据，支持多种生成模式（随机、边界值、等价类等）。
    """
    
    def __init__(
        self,
        generation_mode: Union[str, List[str]] = "boundary",
        include_optional: bool = True,
        count: int = 5,
        field_policies: Optional[List[Dict[str, Any]]] = None,
        content_type: str = "application/json",
        ref_resolver: Optional[Any] = None,
    ):
        """
        初始化生成器。

        :param generation_mode: 生成模式，支持单个模式或模式列表。
            单个模式："random", "boundary", "equivalence", "cartesian", "pairwise", "invalid"
            模式列表：["boundary", "random"] - 多种模式独立生成后去重合并
        :param include_optional: 是否包含可选字段
        :param count: 每个端点生成的数据数量（random 模式下）
        :param field_policies: 特定字段的策略配置（覆盖自动推导）
        :param content_type: 请求体的 content-type
        :param ref_resolver: OpenAPI 解析器实例，用于解析 $ref 引用
        """
        # 统一转换为列表形式
        if isinstance(generation_mode, str):
            self.generation_modes = [generation_mode.upper()]
        else:
            self.generation_modes = [m.upper() for m in generation_mode]
        
        # 保留单个模式的属性用于兼容
        self.generation_mode = self.generation_modes[0] if len(self.generation_modes) == 1 else "multiple"
        
        self.include_optional = include_optional
        self.count = count
        self.field_policies = field_policies or []
        self.content_type = content_type
        self.ref_resolver = ref_resolver
    
    def generate_for_endpoint(
        self,
        endpoint: OpenAPIEndpoint,
        count: Optional[int] = None,
    ) -> List[GeneratedRequest]:
        """
        为单个端点生成请求数据。
        
        支持多模式生成：为每种模式独立生成 count 条数据，然后去重合并。
        
        :param endpoint: OpenAPIEndpoint 实例
        :param count: 覆盖默认的生成数量（每种模式都会生成这个数量）
        :return: GeneratedRequest 列表（已去重）
        """
        count = count or self.count
        
        # 为每种模式独立生成数据
        all_requests = []
        for mode in self.generation_modes:
            requests = self._generate_for_single_mode(endpoint, mode, count)
            all_requests.extend(requests)
        
        # 去重合并
        return self._deduplicate_requests(all_requests)
    
    def _generate_for_single_mode(
        self,
        endpoint: OpenAPIEndpoint,
        mode: str,
        count: int,
    ) -> List[GeneratedRequest]:
        """
        为单个模式生成请求数据。
        
        :param endpoint: OpenAPIEndpoint 实例
        :param mode: 单个生成模式（大写）
        :param count: 生成数量
        :return: GeneratedRequest 列表
        """
        # 提取各种参数的 schema
        (
            path_params_schema,
            query_params_schema,
            header_params_schema,
            request_body_schema,
        ) = SchemaConverter.create_combined_schema_for_endpoint(
            endpoint,
            include_query_params=True,
            include_path_params=True,
            include_header_params=True,
            include_request_body=True,
            include_optional_fields=self.include_optional,
            content_type=self.content_type,
            ref_resolver=self.ref_resolver,
        )
        
        # 为每种参数生成数据
        path_params_list = self._generate_params_data(
            path_params_schema,
            count,
            f"{endpoint.operation_id}_path",
            mode,
        )
        
        query_params_list = self._generate_params_data(
            query_params_schema,
            count,
            f"{endpoint.operation_id}_query",
            mode,
        )
        
        header_params_list = self._generate_params_data(
            header_params_schema,
            count,
            f"{endpoint.operation_id}_header",
            mode,
        )
        
        request_body_list = self._generate_request_body_data(
            request_body_schema,
            count,
            f"{endpoint.operation_id}_body",
            mode,
        )
        
        # 合并生成完整的请求数据
        requests = []
        
        # 计算各个参数类型的数量
        counts = [
            len(path_params_list) if path_params_list else 1,
            len(query_params_list) if query_params_list else 1,
            len(header_params_list) if header_params_list else 1,
            len(request_body_list) if request_body_list else 1,
        ]
        
        # 检测数量不一致，发出警告
        non_one_counts = [c for c in counts if c != 1]
        if len(set(non_one_counts)) > 1:
            import warnings
            warnings.warn(
                f"参数数量不一致（path={counts[0]}, query={counts[1]}, "
                f"header={counts[2]}, body={counts[3]}），将循环使用参数生成 {max(counts)} 条数据",
                UserWarning,
                stacklevel=3,
            )
        
        # 使用最大数量，参数循环使用
        max_count = max(counts)
        
        for i in range(max_count):
            # 获取各个部分的参数（循环使用）
            path_params = path_params_list[i % len(path_params_list)] if path_params_list else {}
            query_params = query_params_list[i % len(query_params_list)] if query_params_list else {}
            header_params = header_params_list[i % len(header_params_list)] if header_params_list else {}
            request_body = request_body_list[i % len(request_body_list)] if request_body_list else None
            
            # 创建 GeneratedRequest
            request = GeneratedRequest(
                operation_id=endpoint.operation_id,
                path=endpoint.path,
                method=endpoint.method,
                path_params=path_params,
                query_params=query_params,
                header_params=header_params,
                request_body=request_body,
                metadata={
                    "generation_mode": mode.lower(),  # 标记该数据的来源模式
                    "endpoint_summary": endpoint.summary,
                    "tags": endpoint.tags,
                },
            )
            requests.append(request)
        
        return requests
    
    def _deduplicate_requests(
        self,
        requests: List[GeneratedRequest],
    ) -> List[GeneratedRequest]:
        """
        对生成的请求数据进行去重。
        
        基于请求的实际内容（path_params, query_params, header_params, request_body）去重，
        保留第一个出现的请求（metadata 中保留了该数据的来源模式）。
        
        :param requests: 待去重的请求列表
        :return: 去重后的请求列表
        """
        seen = set()
        unique = []
        
        for req in requests:
            key = req.content_key()
            if key not in seen:
                seen.add(key)
                unique.append(req)
        
        return unique
    
    def _generate_params_data(
        self,
        schema: Dict[str, Any],
        count: int,
        context: str,
        mode: str,
    ) -> List[Dict[str, Any]]:
        """
        生成参数数据。
        
        :param schema: 参数的 JSON Schema
        :param count: 生成数量
        :param context: 上下文标识（用于日志）
        :param mode: 生成模式
        :return: 参数字典列表
        """
        if not schema or not schema.get("properties"):
            return [{}]
        
        # 构建 DataBuilder 配置
        config = self._build_builder_config(schema, count, context, mode)
        
        # 创建 DataBuilder 并生成数据
        builder = DataBuilder(schema, config)
        
        try:
            data = builder.build(count=count)
            return data
        except Exception as e:
            # 如果生成失败，返回空字典列表
            print(f"生成 {context} 数据失败：{e}")
            return [{}] * count
    
    def _generate_request_body_data(
        self,
        schema: Optional[Dict[str, Any]],
        count: int,
        context: str,
        mode: str,
    ) -> List[Any]:
        """
        生成请求体数据。
        
        :param schema: 请求体的 JSON Schema
        :param count: 生成数量
        :param context: 上下文标识
        :param mode: 生成模式
        :return: 请求体数据列表
        """
        if not schema:
            return [None]
        
        # 构建 DataBuilder 配置
        config = self._build_builder_config(schema, count, context, mode)
        
        # 创建 DataBuilder 并生成数据
        builder = DataBuilder(schema, config)
        
        try:
            data = builder.build(count=count)
            return data
        except Exception as e:
            print(f"生成 {context} 数据失败：{e}")
            return [None] * count
    
    def _build_builder_config(
        self,
        schema: Dict[str, Any],
        count: int,
        context: str,
        mode: str,
    ) -> BuilderConfig:
        """
        构建 DataBuilder 配置。
        
        根据生成模式和 schema 约束，自动构建合适的策略配置。
        
        :param schema: JSON Schema
        :param count: 生成数量
        :param context: 上下文标识
        :param mode: 生成模式（单个模式）
        :return: BuilderConfig 实例
        """
        policies = []
        
        # 应用用户自定义策略（覆盖自动推导）
        for policy_config in self.field_policies:
            policies.append(FieldPolicy(
                path=policy_config["path"],
                strategy=self._create_strategy_from_config(policy_config["strategy"]),
            ))
        
        # 构建组合配置
        combinations = []
        
        if mode != "RANDOM":
            # 检测约束字段
            enum_fields = SchemaConverter.detect_enum_fields(schema)
            boundary_fields = SchemaConverter.detect_boundary_fields(schema)
            pattern_fields = SchemaConverter.detect_pattern_fields(schema)
            
            # 根据生成模式添加组合配置
            if mode == "BOUNDARY":
                # 边界值模式：针对有边界约束的字段
                if boundary_fields or enum_fields:
                    combinations.append(CombinationSpec(
                        mode=CombinationMode.BOUNDARY,
                        fields=boundary_fields + enum_fields,
                    ))
            
            elif mode == "EQUIVALENCE":
                # 等价类模式：针对有约束的字段
                constrained_fields = list(set(enum_fields + boundary_fields + pattern_fields))
                if constrained_fields:
                    combinations.append(CombinationSpec(
                        mode=CombinationMode.EQUIVALENCE,
                        fields=constrained_fields,
                    ))
            
            elif mode == "CARTESIAN":
                # 笛卡尔积模式：所有字段穷举
                properties = schema.get("properties", {})
                all_fields = list(properties.keys())
                if all_fields:
                    combinations.append(CombinationSpec(
                        mode=CombinationMode.CARTESIAN,
                        fields=all_fields,
                    ))
            
            elif mode == "PAIRWISE":
                # 成对组合模式：两两组合
                properties = schema.get("properties", {})
                all_fields = list(properties.keys())
                if all_fields:
                    combinations.append(CombinationSpec(
                        mode=CombinationMode.PAIRWISE,
                        fields=all_fields,
                    ))
            
            elif mode == "INVALID":
                # 非法值模式：生成不符合约束的数据
                properties = schema.get("properties", {})
                all_fields = list(properties.keys())
                if all_fields:
                    combinations.append(CombinationSpec(
                        mode=CombinationMode.INVALID,
                        fields=all_fields,
                    ))
        
        return BuilderConfig(
            policies=policies,
            count=count,
            combinations=combinations,
        )
    
    def _create_strategy_from_config(self, strategy_config: Dict[str, Any]) -> Any:
        """
        从配置创建策略实例。
        
        :param strategy_config: 策略配置字典
        :return: Strategy 实例
        """
        from .. import (
            EnumStrategy,
            FixedStrategy,
            RandomStringStrategy,
            RangeStrategy,
        )
        
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
        count_per_endpoint: Optional[int] = None,
    ) -> Dict[str, List[GeneratedRequest]]:
        """
        为多个端点批量生成请求数据。
        
        :param endpoints: OpenAPIEndpoint 列表
        :param count_per_endpoint: 每个端点的生成数量
        :return: {operation_id: List[GeneratedRequest]} 字典
        """
        result = {}
        
        for endpoint in endpoints:
            requests = self.generate_for_endpoint(endpoint, count_per_endpoint)
            result[endpoint.operation_id] = requests
        
        return result
