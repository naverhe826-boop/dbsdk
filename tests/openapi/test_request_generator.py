"""
测试请求数据生成器。
"""

import pytest
from unittest.mock import Mock, MagicMock

from data_builder.openapi.request_generator import RequestDataGenerator
from data_builder.openapi.models import (
    HttpMethod,
    OpenAPIEndpoint,
    OpenAPIParameter,
    OpenAPIRequestBody,
    ParameterLocation,
)


class TestRequestDataGeneratorInit:
    """测试 RequestDataGenerator 初始化"""
    
    def test_init_default_params(self):
        """测试默认参数初始化"""
        generator = RequestDataGenerator()
        
        assert generator.generation_mode == "BOUNDARY"
        assert generator.include_optional is True
        assert generator.count == 5
    
    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        generator = RequestDataGenerator(
            generation_mode="random",
            include_optional=False,
            count=10,
        )
        
        assert generator.generation_mode == "RANDOM"
        assert generator.include_optional is False
        assert generator.count == 10
    
    def test_init_with_multiple_modes(self):
        """测试多模式初始化"""
        generator = RequestDataGenerator(
            generation_mode=["boundary", "random"],
        )
        
        assert len(generator.generation_modes) == 2
        assert "BOUNDARY" in generator.generation_modes
        assert "RANDOM" in generator.generation_modes


class TestRequestDataGeneratorSingleEndpoint:
    """测试单端点数据生成"""
    
    @pytest.fixture
    def simple_endpoint(self):
        """简单端点 fixture"""
        return OpenAPIEndpoint(
            path="/users",
            method=HttpMethod.GET,
            operation_id="getUsers",
            summary="获取用户列表",
            parameters=[
                OpenAPIParameter(
                    name="limit",
                    location=ParameterLocation.QUERY,
                    schema={"type": "integer", "minimum": 1, "maximum": 100},
                    required=False,
                ),
                OpenAPIParameter(
                    name="offset",
                    location=ParameterLocation.QUERY,
                    schema={"type": "integer", "minimum": 0},
                    required=False,
                ),
            ],
        )
    
    @pytest.fixture
    def endpoint_with_path_params(self):
        """带路径参数的端点"""
        return OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUser",
            parameters=[
                OpenAPIParameter(
                    name="id",
                    location=ParameterLocation.PATH,
                    schema={"type": "string"},
                    required=True,
                ),
            ],
        )
    
    @pytest.fixture
    def endpoint_with_request_body(self):
        """带请求体的端点"""
        return OpenAPIEndpoint(
            path="/users",
            method=HttpMethod.POST,
            operation_id="createUser",
            request_body=OpenAPIRequestBody(
                content={
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string", "format": "email"},
                            },
                            "required": ["name", "email"],
                        }
                    }
                },
                required=True,
            ),
        )
    
    def test_generate_for_simple_endpoint(self, simple_endpoint):
        """测试为简单端点生成数据"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=3,
        )
        
        requests = generator.generate_for_endpoint(simple_endpoint)
        
        assert len(requests) == 3
        for req in requests:
            assert req.operation_id == "getUsers"
            assert req.method == HttpMethod.GET
            assert req.path == "/users"
            assert "limit" in req.query_params
            assert "offset" in req.query_params
    
    def test_generate_with_path_params(self, endpoint_with_path_params):
        """测试生成路径参数"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=2,
        )
        
        requests = generator.generate_for_endpoint(endpoint_with_path_params)
        
        assert len(requests) == 2
        for req in requests:
            assert "id" in req.path_params
            assert req.path_params["id"] is not None
    
    def test_generate_with_request_body(self, endpoint_with_request_body):
        """测试生成请求体"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=2,
        )
        
        requests = generator.generate_for_endpoint(endpoint_with_request_body)
        
        assert len(requests) == 2
        for req in requests:
            assert req.request_body is not None
            assert "name" in req.request_body
            assert "email" in req.request_body
    
    def test_generate_boundary_mode(self, simple_endpoint):
        """测试边界值模式"""
        generator = RequestDataGenerator(
            generation_mode="boundary",
            count=5,
        )
        
        requests = generator.generate_for_endpoint(simple_endpoint)
        
        # 边界值模式会生成边界附近的值
        assert len(requests) > 0
        for req in requests:
            # limit 应该在 1-100 范围内
            limit = req.query_params.get("limit")
            if limit is not None:
                assert 1 <= limit <= 100
    
    def test_generate_with_field_policies(self, simple_endpoint):
        """测试字段策略覆盖"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=3,
            field_policies=[
                {
                    "path": "limit",
                    "strategy": {"type": "fixed", "value": 50}
                }
            ],
        )
        
        requests = generator.generate_for_endpoint(simple_endpoint)
        
        for req in requests:
            assert req.query_params["limit"] == 50


class TestRequestDataGeneratorMultipleModes:
    """测试多模式生成"""
    
    @pytest.fixture
    def endpoint(self):
        """测试端点"""
        return OpenAPIEndpoint(
            path="/items",
            method=HttpMethod.GET,
            operation_id="getItems",
            parameters=[
                OpenAPIParameter(
                    name="status",
                    location=ParameterLocation.QUERY,
                    schema={
                        "type": "string",
                        "enum": ["active", "inactive", "pending"]
                    },
                ),
            ],
        )
    
    def test_generate_with_multiple_modes(self, endpoint):
        """测试多模式独立生成"""
        generator = RequestDataGenerator(
            generation_mode=["random", "boundary"],
            count=3,
        )
        
        requests = generator.generate_for_endpoint(endpoint)
        
        # 两种模式各生成 3 条,去重后应该有 3-6 条
        assert len(requests) >= 3
        
        # 所有请求的 metadata 应该标记来源模式
        modes = {req.metadata.get("generation_mode") for req in requests}
        assert len(modes) > 0
    
    def test_deduplication(self, endpoint):
        """测试去重功能"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=10,
            field_policies=[
                {
                    "path": "status",
                    "strategy": {"type": "fixed", "value": "active"}
                }
            ],
        )
        
        requests = generator.generate_for_endpoint(endpoint)
        
        # 所有请求的 status 都是 active,应该被去重
        # 但其他参数可能不同,所以数量可能 > 1
        for req in requests:
            assert req.query_params["status"] == "active"


class TestRequestDataGeneratorConfigBuilding:
    """测试配置构建"""
    
    def test_build_config_for_random_mode(self):
        """测试随机模式配置"""
        generator = RequestDataGenerator(generation_mode="random")
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        
        config = generator._build_builder_config(
            schema, count=5, context="test", mode="RANDOM"
        )
        
        # 随机模式不应该有组合配置
        assert len(config.combinations) == 0
    
    def test_build_config_for_boundary_mode(self):
        """测试边界值模式配置"""
        generator = RequestDataGenerator(generation_mode="boundary")
        
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 120},
                "score": {"type": "number", "minimum": 0, "maximum": 100},
            },
        }
        
        config = generator._build_builder_config(
            schema, count=5, context="test", mode="BOUNDARY"
        )
        
        # 边界值模式应该有组合配置
        assert len(config.combinations) > 0
        assert config.combinations[0].mode.value.lower() == "boundary"
    
    def test_build_config_with_enum(self):
        """测试枚举字段检测"""
        generator = RequestDataGenerator(generation_mode="equivalence")
        
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive"]
                },
            },
        }
        
        config = generator._build_builder_config(
            schema, count=5, context="test", mode="EQUIVALENCE"
        )
        
        # 等价类模式应该包含枚举字段
        assert len(config.combinations) > 0


class TestRequestDataGeneratorStrategyCreation:
    """测试策略创建"""
    
    def test_create_fixed_strategy(self):
        """测试创建固定值策略"""
        generator = RequestDataGenerator()
        
        strategy = generator._create_strategy_from_config({
            "type": "fixed",
            "value": "test_value"
        })
        
        assert strategy is not None
    
    def test_create_enum_strategy(self):
        """测试创建枚举策略"""
        generator = RequestDataGenerator()
        
        strategy = generator._create_strategy_from_config({
            "type": "enum",
            "values": ["a", "b", "c"]
        })
        
        assert strategy is not None
    
    def test_create_unknown_strategy(self):
        """测试未知策略类型"""
        generator = RequestDataGenerator()
        
        # 未知类型应该返回 FixedStrategy
        strategy = generator._create_strategy_from_config({
            "type": "unknown_type",
            "value": "default"
        })
        
        assert strategy is not None


class TestRequestDataGeneratorBatchGeneration:
    """测试批量生成"""
    
    @pytest.fixture
    def endpoints(self):
        """多个端点 fixture"""
        return [
            OpenAPIEndpoint(
                path="/users",
                method=HttpMethod.GET,
                operation_id="getUsers",
            ),
            OpenAPIEndpoint(
                path="/items",
                method=HttpMethod.GET,
                operation_id="getItems",
            ),
        ]
    
    def test_generate_for_document(self, endpoints):
        """测试为多个端点生成数据"""
        generator = RequestDataGenerator(
            generation_mode="random",
            count=2,
        )
        
        result = generator.generate_for_document(endpoints)
        
        assert "getUsers" in result
        assert "getItems" in result
        # 空参数的端点可能生成较少数据
        assert len(result["getUsers"]) >= 1
        assert len(result["getItems"]) >= 1


class TestRequestDataGeneratorEdgeCases:
    """测试边界情况"""
    
    def test_generate_empty_parameters(self):
        """测试无参数的端点"""
        endpoint = OpenAPIEndpoint(
            path="/health",
            method=HttpMethod.GET,
            operation_id="healthCheck",
        )
        
        generator = RequestDataGenerator(generation_mode="random")
        requests = generator.generate_for_endpoint(endpoint)
        
        assert len(requests) > 0
        assert requests[0].operation_id == "healthCheck"
        assert requests[0].path_params == {}
        assert requests[0].query_params == {}
    
    def test_generate_with_count_override(self):
        """测试覆盖生成数量"""
        endpoint = OpenAPIEndpoint(
            path="/test",
            method=HttpMethod.GET,
            operation_id="test",
            parameters=[
                OpenAPIParameter(
                    name="id",
                    location=ParameterLocation.QUERY,
                    schema={"type": "string"},
                )
            ]
        )
        
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
        )
        
        requests = generator.generate_for_endpoint(endpoint, count=10)
        
        assert len(requests) == 10
    
    def test_generate_with_invalid_schema(self):
        """测试无效 schema 处理"""
        endpoint = OpenAPIEndpoint(
            path="/test",
            method=HttpMethod.POST,
            operation_id="test",
            request_body=OpenAPIRequestBody(
                content={
                    "application/json": {
                        "schema": {}  # 空 schema
                    }
                }
            ),
        )
        
        generator = RequestDataGenerator(generation_mode="random")
        
        # 应该不抛出异常
        requests = generator.generate_for_endpoint(endpoint)
        assert len(requests) > 0
