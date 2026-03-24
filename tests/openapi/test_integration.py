"""
测试 OpenAPI 解析器和生成器的集成功能。

使用真实的 OpenAPI 文档进行测试。
"""

import json
import pytest
from pathlib import Path

from data_builder.openapi import (
    APITestDataManager,
    OpenAPIParser,
    RequestDataGenerator,
    SchemaConverter,
)


# 测试数据路径
API_DOC_PATH = Path(__file__).parent.parent.parent / "docs" / "openapi" / "petstore.json"


@pytest.fixture
def sample_openapi_doc():
    """创建示例 OpenAPI 文档"""
    return {
        "openapi": "3.0.2",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "get_user",
                    "summary": "Get user by ID",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "fields",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/users": {
                "post": {
                    "operationId": "create_user",
                    "summary": "Create user",
                    "tags": ["users"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                                    },
                                    "required": ["name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }


class TestOpenAPIParser:
    """测试 OpenAPI 解析器"""
    
    def test_parse_from_dict(self, sample_openapi_doc):
        """测试从字典解析"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        assert document.openapi_version == "3.0.2"
        assert document.info["title"] == "Test API"
        assert len(document.get_all_endpoints()) == 2
    
    def test_parse_endpoints(self, sample_openapi_doc):
        """测试解析端点"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        endpoints = document.get_all_endpoints()
        
        # 检查 GET 端点
        get_endpoint = document.get_endpoint_by_operation_id("get_user")
        assert get_endpoint is not None
        assert get_endpoint.path == "/users/{id}"
        assert len(get_endpoint.parameters) == 2
        
        # 检查参数
        path_params = get_endpoint.get_path_parameters()
        assert len(path_params) == 1
        assert path_params[0].name == "id"
        assert path_params[0].required is True
        
        # 检查 POST 端点
        post_endpoint = document.get_endpoint_by_operation_id("create_user")
        assert post_endpoint is not None
        assert post_endpoint.request_body is not None
        assert post_endpoint.request_body.required is True
    
    def test_resolve_ref(self, sample_openapi_doc):
        """测试解析 $ref 引用"""
        # 添加一个带 $ref 的 schema
        sample_openapi_doc["paths"]["/ref-test"] = {
            "get": {
                "operationId": "test_ref",
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        # 验证 $ref 已被解析
        endpoint = document.get_endpoint_by_operation_id("test_ref")
        assert endpoint is not None
    
    @pytest.mark.skipif(not API_DOC_PATH.exists(), reason="真实文档不存在")
    def test_parse_real_document(self):
        """测试解析真实的 OpenAPI 文档"""
        parser = OpenAPIParser.from_file(API_DOC_PATH)
        document = parser.parse()
        
        assert document.openapi_version.startswith("3.0")
        assert len(document.get_all_endpoints()) > 0
        
        # 检查第一个端点
        endpoint = document.get_all_endpoints()[0]
        assert endpoint.operation_id
        assert endpoint.path
        assert endpoint.method


class TestSchemaConverter:
    """测试 Schema 转换器"""
    
    def test_convert_nullable(self):
        """测试转换 nullable 字段"""
        openapi_schema = {
            "type": "string",
            "nullable": True,
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(openapi_schema)
        
        assert "nullable" not in json_schema
        assert json_schema["type"] == ["string", "null"]
    
    def test_convert_example(self):
        """测试转换 example 字段"""
        openapi_schema = {
            "type": "string",
            "example": "test",
        }
        
        json_schema = SchemaConverter.convert_openapi_schema_to_json_schema(openapi_schema)
        
        assert "example" not in json_schema
        assert json_schema["examples"] == ["test"]
    
    def test_extract_parameters_schema(self):
        """测试提取参数 schema"""
        from data_builder.openapi import OpenAPIParameter, ParameterLocation
        
        parameters = [
            OpenAPIParameter(
                name="id",
                location=ParameterLocation.PATH,
                schema={"type": "string"},
                required=True,
            ),
            OpenAPIParameter(
                name="name",
                location=ParameterLocation.QUERY,
                schema={"type": "string"},
                required=False,
            ),
        ]
        
        schema = SchemaConverter.extract_parameters_schema(
            parameters,
            ParameterLocation.PATH,
            include_optional=False,
        )
        
        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "id" in schema["required"]
    
    def test_detect_enum_fields(self):
        """测试检测 enum 字段"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive"]},
                "name": {"type": "string"},
            }
        }
        
        enum_fields = SchemaConverter.detect_enum_fields(schema)
        
        assert len(enum_fields) == 1
        assert "status" in enum_fields
    
    def test_detect_boundary_fields(self):
        """测试检测边界约束字段"""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "name": {"type": "string"},
            }
        }
        
        boundary_fields = SchemaConverter.detect_boundary_fields(schema)
        
        assert len(boundary_fields) == 1
        assert "age" in boundary_fields


class TestRequestDataGenerator:
    """测试请求数据生成器"""
    
    def test_generate_for_endpoint(self, sample_openapi_doc):
        """测试为端点生成数据"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(
            generation_mode="random",
            count=3,
        )
        
        endpoint = document.get_endpoint_by_operation_id("get_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        assert len(requests) == 3
        assert all(req.operation_id == "get_user" for req in requests)
        
        # 检查路径参数已填充
        for req in requests:
            if req.path_params:
                assert "id" in req.path_params
    
    def test_generate_with_boundary_mode(self, sample_openapi_doc):
        """测试边界值模式生成"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(
            generation_mode="boundary",
            count=5,
        )
        
        endpoint = document.get_endpoint_by_operation_id("create_user")
        requests = generator.generate_for_endpoint(endpoint, count=3)
        
        assert len(requests) > 0
        assert all(req.operation_id == "create_user" for req in requests)
    
    def test_generate_with_parameter_example(self):
        """测试参数中的 example 被使用"""
        # 创建带参数 example 的 OpenAPI 文档
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "operationId": "get_user_by_id",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer", "example": 999}
                            },
                            {
                                "name": "status",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string", "example": "active"}
                            },
                            {
                                "name": "X-Request-ID",
                                "in": "header",
                                "required": False,
                                "schema": {"type": "string", "example": "req-12345"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(generation_mode="random", count=5)
        endpoint = document.get_endpoint_by_operation_id("get_user_by_id")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证：所有生成的请求都应使用参数中的 example 值
        # 注意：当所有参数都有固定的 example 时，去重后可能只有 1 条数据
        assert len(requests) >= 1
        for req in requests:
            # path 参数 example
            assert req.path_params["id"] == 999
            
            # query 参数 example
            assert req.query_params["status"] == "active"
            
            # header 参数 example
            assert req.header_params["X-Request-ID"] == "req-12345"
    
    def test_generate_with_request_body_example(self):
        """测试请求体中的 example（content 级别）被使用"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "create_user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "age": {"type": "integer"}
                                        }
                                    },
                                    "example": {"name": "张三", "age": 25}
                                }
                            }
                        },
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(generation_mode="random", count=3)
        endpoint = document.get_endpoint_by_operation_id("create_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证：所有生成的请求体都应使用 example 值
        # 注意：当 request body 有固定的 example 时，去重后可能只有 1 条数据
        assert len(requests) >= 1
        for req in requests:
            assert req.request_body is not None
            assert req.request_body["name"] == "张三"
            assert req.request_body["age"] == 25
    
    def test_generate_with_schema_example(self):
        """测试请求体 schema 内的 example 被使用"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/products": {
                    "post": {
                        "operationId": "create_product",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "product_name": {"type": "string"},
                                            "price": {"type": "number"}
                                        },
                                        "example": {"product_name": "测试商品", "price": 99.99}
                                    }
                                }
                            }
                        },
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(generation_mode="random", count=3)
        endpoint = document.get_endpoint_by_operation_id("create_product")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证：schema 内的 example 被转换并使用
        # 注意：当 schema 有固定的 example 时，去重后可能只有 1 条数据
        assert len(requests) >= 1
        for req in requests:
            assert req.request_body is not None
            assert req.request_body["product_name"] == "测试商品"
            assert req.request_body["price"] == 99.99
    
    def test_example_used_in_different_modes(self):
        """测试不同生成模式下 example 的处理"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/items/{id}": {
                    "get": {
                        "operationId": "get_item",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string", "example": "item-001"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        endpoint = document.get_endpoint_by_operation_id("get_item")
        
        # 测试 random 模式
        generator_random = RequestDataGenerator(generation_mode="random", count=3)
        requests_random = generator_random.generate_for_endpoint(endpoint)
        for req in requests_random:
            assert req.path_params["id"] == "item-001"
            assert req.metadata["generation_mode"] == "random"
        
        # 测试 boundary 模式（example 应被使用）
        generator_boundary = RequestDataGenerator(generation_mode="boundary", count=3)
        requests_boundary = generator_boundary.generate_for_endpoint(endpoint)
        # boundary 模式下，由于没有边界约束字段，仍会使用 example
        for req in requests_boundary:
            assert req.path_params["id"] == "item-001"
            assert req.metadata["generation_mode"] == "boundary"
        
        # 测试多模式混合
        generator_multi = RequestDataGenerator(
            generation_mode=["random", "boundary"],
            count=2
        )
        requests_multi = generator_multi.generate_for_endpoint(endpoint)
        # 多模式下应去重，所有请求都应使用 example
        assert len(set(req.path_params["id"] for req in requests_multi)) == 1
        assert all(req.path_params["id"] == "item-001" for req in requests_multi)
    
    def test_field_policies_override_example(self):
        """测试 field_policies 优先于 example"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/orders": {
                    "post": {
                        "operationId": "create_order",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "order_id": {"type": "string"},
                                            "amount": {"type": "number"},
                                            "status": {"type": "string"}
                                        }
                                    },
                                    "example": {
                                        "order_id": "EXAMPLE-ORDER-001",
                                        "amount": 100.00,
                                        "status": "pending"
                                    }
                                }
                            }
                        },
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 field_policies 覆盖部分字段
        generator = RequestDataGenerator(
            generation_mode="random",
            count=3,
            field_policies=[
                {
                    "path": "order_id",
                    "strategy": {"type": "fixed", "value": "POLICY-ORDER-999"}
                },
                {
                    "path": "amount",
                    "strategy": {"type": "fixed", "value": 299.99}
                }
                # status 字段没有显式策略，应使用 example
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("create_order")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证：有显式策略的字段使用策略值，无策略的字段使用 example
        # 注意：由于字段值固定，去重后可能只有 1 条数据
        assert len(requests) >= 1
        for req in requests:
            assert req.request_body["order_id"] == "POLICY-ORDER-999"  # 策略值
            assert req.request_body["amount"] == 299.99  # 策略值
            assert req.request_body["status"] == "pending"  # example 值


class TestAPITestDataManager:
    """测试 API 测试数据管理器"""
    
    def test_create_manager(self, sample_openapi_doc):
        """测试创建管理器"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": "random",
                "count": 2,
            }
        )
        
        summary = manager.summary()
        assert summary["total_endpoints"] == 2
        assert summary["generation_modes"] == ["RANDOM"]
    
    def test_get_endpoints(self, sample_openapi_doc):
        """测试获取端点"""
        manager = APITestDataManager(openapi_document=sample_openapi_doc)
        
        # 获取所有端点
        all_endpoints = manager.get_all_endpoints()
        assert len(all_endpoints) == 2
        
        # 按 operationId 获取
        endpoint = manager.get_endpoint_by_operation_id("get_user")
        assert endpoint is not None
        assert endpoint.operation_id == "get_user"
        
        # 按标签获取
        user_endpoints = manager.get_endpoints_by_tag("users")
        assert len(user_endpoints) == 2
    
    def test_get_endpoint_by_path_and_method(self, sample_openapi_doc):
        """测试按路径和方法获取端点"""
        manager = APITestDataManager(openapi_document=sample_openapi_doc)
        
        # 测试查找 GET /users/{id}
        endpoint = manager.get_endpoint_by_path_and_method("/users/{id}", "GET")
        assert endpoint is not None
        assert endpoint.operation_id == "get_user"
        
        # 测试查找 POST /users
        endpoint = manager.get_endpoint_by_path_and_method("/users", "POST")
        assert endpoint is not None
        assert endpoint.operation_id == "create_user"
        
        # 测试方法大小写不敏感
        endpoint = manager.get_endpoint_by_path_and_method("/users/{id}", "get")
        assert endpoint is not None
        assert endpoint.operation_id == "get_user"
        
        # 测试不存在的端点
        endpoint = manager.get_endpoint_by_path_and_method("/nonexistent", "GET")
        assert endpoint is None
    
    def test_generate_for_path_method(self, sample_openapi_doc):
        """测试按路径和方法生成数据"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": "random",
                "count": 3,
            }
        )
        
        # 按 path + method 生成数据
        requests = manager.generate_for_path_method("/users/{id}", "GET", count=2)
        assert len(requests) == 2
        assert all(req.operation_id == "get_user" for req in requests)
        
        # 按 path + method 生成 POST 数据
        requests = manager.generate_for_path_method("/users", "POST", count=2)
        assert len(requests) == 2
        assert all(req.operation_id == "create_user" for req in requests)
        
        # 测试不存在的端点抛出异常
        with pytest.raises(ValueError, match="未找到端点"):
            manager.generate_for_path_method("/nonexistent", "GET")
    
    def test_generate_and_save(self, sample_openapi_doc, tmp_path):
        """测试生成和保存数据"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": "random",
                "count": 2,
            }
        )
        
        # 生成数据
        result = manager.generate_for_all()
        assert len(result) == 2
        
        # 保存数据
        output_file = tmp_path / "test_data.json"
        manager.save_generated_data(output_file)
        
        assert output_file.exists()
        
        # 加载数据
        with open(output_file) as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == 2


class TestMultipleModes:
    """测试多模式生成功能"""
    
    def test_generation_mode_list(self, sample_openapi_doc):
        """测试 generation_mode 支持列表"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": ["boundary", "random"],
                "count": 3,
            }
        )
        
        # 检查 generation_modes 属性
        assert manager.generator.generation_modes == ["BOUNDARY", "RANDOM"]
        assert manager.generator.generation_mode in ["BOUNDARY", "multiple"]
    
    def test_multiple_modes_generate_data(self, sample_openapi_doc):
        """测试多模式生成数据"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        generator = RequestDataGenerator(
            generation_mode=["boundary", "random"],
            count=3,
        )
        
        endpoint = document.get_endpoint_by_operation_id("get_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 检查生成了数据
        assert len(requests) > 0
        
        # 检查每条数据都有 generation_mode 标记
        for req in requests:
            assert "generation_mode" in req.metadata
            assert req.metadata["generation_mode"] in ["boundary", "random"]
    
    def test_deduplication(self, sample_openapi_doc):
        """测试去重功能"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        # 使用相同模式两次（应该去重）
        generator = RequestDataGenerator(
            generation_mode=["random", "random"],
            count=5,
        )
        
        endpoint = document.get_endpoint_by_operation_id("get_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 即使两次 random 模式，也应该去重
        # 检查没有完全重复的请求
        content_keys = [req.content_key() for req in requests]
        assert len(content_keys) == len(set(content_keys)), "存在重复的请求"
    
    def test_content_key_generation(self):
        """测试 GeneratedRequest.content_key() 方法"""
        from data_builder.openapi.models import GeneratedRequest, HttpMethod
        
        # 创建两个内容相同但 metadata 不同的请求
        req1 = GeneratedRequest(
            operation_id="test",
            path="/test",
            method=HttpMethod.GET,
            path_params={"id": "123"},
            query_params={"name": "test"},
            metadata={"generation_mode": "boundary"},
        )
        
        req2 = GeneratedRequest(
            operation_id="test",
            path="/test",
            method=HttpMethod.GET,
            path_params={"id": "123"},
            query_params={"name": "test"},
            metadata={"generation_mode": "random"},  # metadata 不同
        )
        
        # 内容相同，content_key 应该相同
        assert req1.content_key() == req2.content_key()
        
        # 内容不同，content_key 应该不同
        req3 = GeneratedRequest(
            operation_id="test",
            path="/test",
            method=HttpMethod.GET,
            path_params={"id": "456"},  # 不同的值
            query_params={"name": "test"},
            metadata={"generation_mode": "random"},
        )
        
        assert req1.content_key() != req3.content_key()
    
    def test_manager_summary_with_multiple_modes(self, sample_openapi_doc):
        """测试 summary 返回 generation_modes"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": ["boundary", "random"],
                "count": 3,
            }
        )
        
        summary = manager.summary()
        assert "generation_modes" in summary
        assert summary["generation_modes"] == ["BOUNDARY", "RANDOM"]
    
    def test_save_config_with_multiple_modes(self, sample_openapi_doc, tmp_path):
        """测试保存配置时保留多模式"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": ["boundary", "random"],
                "count": 3,
            }
        )
        
        # 保存配置
        config_path = tmp_path / "config.json"
        manager.save_config(config_path)
        
        # 加载配置
        with open(config_path) as f:
            config = json.load(f)
        
        # 检查保存的是列表
        assert "generation_config" in config
        assert config["generation_config"]["generation_mode"] == ["boundary", "random"]
    
    def test_save_config_with_single_mode(self, sample_openapi_doc, tmp_path):
        """测试保存配置时单个模式保存为字符串"""
        manager = APITestDataManager(
            openapi_document=sample_openapi_doc,
            generation_config={
                "generation_mode": "boundary",  # 单个模式
                "count": 3,
            }
        )
        
        # 保存配置
        config_path = tmp_path / "config.json"
        manager.save_config(config_path)
        
        # 加载配置
        with open(config_path) as f:
            config = json.load(f)
        
        # 检查保存的是字符串
        assert config["generation_config"]["generation_mode"] == "boundary"


class TestFieldPoliciesStrategies:
    """测试 field_policies 中各种策略的使用"""
    
    def test_field_policies_enum_strategy(self, sample_openapi_doc):
        """测试 enum 策略在 field_policies 中的使用"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        # 配置 enum 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "status",
                    "strategy": {
                        "type": "enum",
                        "values": ["active", "inactive", "pending"]
                    }
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("create_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的数据中 status 字段都在枚举值中
        valid_values = ["active", "inactive", "pending"]
        for req in requests:
            if req.request_body and "status" in req.request_body:
                assert req.request_body["status"] in valid_values
    
    def test_field_policies_range_strategy(self, sample_openapi_doc):
        """测试 range 策略在 field_policies 中的使用"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        # 配置 range 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "age",
                    "strategy": {
                        "type": "range",
                        "min_val": 18,
                        "max_val": 65
                    }
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("create_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的数据中 age 字段都在范围内
        for req in requests:
            if req.request_body and "age" in req.request_body:
                assert 18 <= req.request_body["age"] <= 65
    
    def test_field_policies_random_string_strategy(self, sample_openapi_doc):
        """测试 random_string 策略在 field_policies 中的使用"""
        parser = OpenAPIParser.from_dict(sample_openapi_doc)
        document = parser.parse()
        
        # 配置 random_string 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "name",
                    "strategy": {
                        "type": "random_string",
                        "length": 10
                    }
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("create_user")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的数据中 name 字段都是 10 位字符串
        for req in requests:
            if req.request_body and "name" in req.request_body:
                assert isinstance(req.request_body["name"], str)
                assert len(req.request_body["name"]) == 10


class TestPathParamsNameFieldStrategy:
    """
    测试路径参数中的 name 字段使用 username 策略
    
    Bug Fix: 路径参数必须符合 URI 规范，不允许空格
    """
    
    def test_path_params_name_uses_username_strategy(self):
        """
        测试路径参数中的 name 字段使用 username 策略（无空格）
        
        Bug Fix: 路径参数不允许出现空格，必须符合 URI 规范
        URI 允许的字符：A-Z a-z 0-9 - . _ ~ : / ? # [ ] @ ! $ & ' ( ) * + , ; =
        """
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{name}/profile": {
                    "get": {
                        "operationId": "get_user_profile",
                        "parameters": [
                            {
                                "name": "name",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 name 字段使用 faker("name") 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=10,
            field_policies=[
                {
                    "path": "name",
                    "strategy": {"type": "faker", "method": "name", "locale": "zh_CN"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("get_user_profile")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的请求中 name 字段无空格（符合 URI 规范）
        for req in requests:
            name_value = req.path_params.get("name")
            assert name_value is not None
            assert isinstance(name_value, str)
            # 路径参数中不应包含空格
            assert " " not in name_value, f"name 字段包含空格: {name_value}"
            # 验证 resolved_path 中也不包含空格
            assert " " not in req.get_url(), f"URL 包含空格: {req.get_url()}"
    
    def test_query_params_name_can_use_chinese(self):
        """
        测试查询参数中的 name 字段可以使用中文
        
        查询参数不受 URI 路径规范限制，可以使用中文名
        """
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "search_users",
                        "parameters": [
                            {
                                "name": "name",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 name 字段使用 faker("name") 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=10,
            field_policies=[
                {
                    "path": "name",
                    "strategy": {"type": "faker", "method": "name", "locale": "zh_CN"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("search_users")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证查询参数中的 name 字段可以包含中文字符
        chinese_count = 0
        for req in requests:
            name_value = req.query_params.get("name")
            if name_value:
                # 检查是否包含中文字符（Unicode 范围：\u4e00-\u9fff）
                if any('\u4e00' <= char <= '\u9fff' for char in str(name_value)):
                    chinese_count += 1
        
        # 至少有一些 name 包含中文（概率很高）
        assert chinese_count > 0, "查询参数中的 name 字段应包含中文姓名"
    
    def test_path_params_with_custom_name_strategy(self):
        """
        测试路径参数中的 name 字段支持自定义策略
        
        如果用户明确指定了 username 策略，应优先使用用户配置
        """
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/items/{item_name}/details": {
                    "get": {
                        "operationId": "get_item_details",
                        "parameters": [
                            {
                                "name": "item_name",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 item_name 字段使用 username 策略（自定义）
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "item_name",
                    "strategy": {"type": "username", "mode": "random"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("get_item_details")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的请求中 item_name 字段无空格
        for req in requests:
            item_name = req.path_params.get("item_name")
            assert item_name is not None
            assert " " not in item_name, f"item_name 包含空格: {item_name}"


class TestFieldPoliciesWithStrategyRegistry:
    """
    测试 StrategyRegistry.create() 支持所有策略类型
    
    Bug Fix: uuid 字段生成 null，因为 _create_strategy_from_config() 只支持 4 种策略
    """
    
    def test_faker_strategy_with_uuid4(self):
        """
        测试 faker 策略生成 UUID（Bug Fix: uuid 字段生成 null）
        
        Bug Fix: _create_strategy_from_config() 只支持 fixed/range/enum/random_string，
        faker 类型不被支持，返回 FixedStrategy(value=None)
        """
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/resources": {
                    "get": {
                        "operationId": "list_resources",
                        "parameters": [
                            {
                                "name": "uuid",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 uuid 字段使用 faker("uuid4") 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=10,
            field_policies=[
                {
                    "path": "uuid",
                    "strategy": {"type": "faker", "method": "uuid4"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("list_resources")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的请求中 uuid 字段不为 null，且符合 UUID 格式
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        )
        
        for req in requests:
            uuid_value = req.query_params.get("uuid")
            assert uuid_value is not None, "uuid 字段不应为 null"
            assert uuid_pattern.match(uuid_value), f"uuid 格式不正确: {uuid_value}"
    
    def test_datetime_strategy_support(self):
        """测试 datetime 策略支持"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/events": {
                    "get": {
                        "operationId": "list_events",
                        "parameters": [
                            {
                                "name": "created_at",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string", "format": "date-time"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 created_at 字段使用 datetime 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "created_at",
                    "strategy": {"type": "datetime", "format": "%Y-%m-%d %H:%M:%S"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("list_events")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的请求中 created_at 字段符合指定格式
        import re
        datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
        
        for req in requests:
            created_at = req.query_params.get("created_at")
            if created_at:  # 可选字段可能为 None
                assert datetime_pattern.match(created_at), f"日期格式不正确: {created_at}"
    
    def test_ipv4_strategy_support(self):
        """测试 ipv4 策略支持"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/servers": {
                    "get": {
                        "operationId": "list_servers",
                        "parameters": [
                            {
                                "name": "ip",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 ip 字段使用 ipv4 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "ip",
                    "strategy": {"type": "ipv4"}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("list_servers")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证所有生成的请求中 ip 字段符合 IPv4 格式
        import re
        ipv4_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        
        for req in requests:
            ip_value = req.query_params.get("ip")
            if ip_value:
                assert ipv4_pattern.match(ip_value), f"IPv4 格式不正确: {ip_value}"
    
    def test_sequence_strategy_support(self):
        """测试 sequence 策略支持"""
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/orders": {
                    "get": {
                        "operationId": "list_orders",
                        "parameters": [
                            {
                                "name": "order_id",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        parser = OpenAPIParser.from_dict(openapi_doc)
        document = parser.parse()
        
        # 配置 order_id 字段使用 sequence 策略
        generator = RequestDataGenerator(
            generation_mode="random",
            count=5,
            field_policies=[
                {
                    "path": "order_id",
                    "strategy": {"type": "sequence", "start": 1001, "step": 1}
                }
            ]
        )
        
        endpoint = document.get_endpoint_by_operation_id("list_orders")
        requests = generator.generate_for_endpoint(endpoint)
        
        # 验证生成的 order_id 是递增的序列
        order_ids = [req.query_params.get("order_id") for req in requests]
        order_ids = [oid for oid in order_ids if oid is not None]  # 过滤 None
        
        # 验证序列递增
        for i in range(1, len(order_ids)):
            assert order_ids[i] > order_ids[i-1], f"序列不是递增的: {order_ids}"
