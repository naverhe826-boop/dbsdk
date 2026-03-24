"""
测试 OpenAPI 数据模型。
"""

import pytest

from data_builder.openapi import (
    HttpMethod,
    OpenAPIEndpoint,
    OpenAPIParameter,
    OpenAPIRequestBody,
    ParameterLocation,
    GeneratedRequest,
)


class TestOpenAPIParameter:
    """测试 OpenAPIParameter 模型"""
    
    def test_create_parameter(self):
        """测试创建参数"""
        param = OpenAPIParameter(
            name="user_id",
            location=ParameterLocation.PATH,
            schema={"type": "string"},
            required=True,
            description="用户ID",
        )
        
        assert param.name == "user_id"
        assert param.location == ParameterLocation.PATH
        assert param.schema == {"type": "string"}
        assert param.required is True
        assert param.description == "用户ID"
    
    def test_string_location_conversion(self):
        """测试字符串位置转换为枚举"""
        param = OpenAPIParameter(
            name="limit",
            location="query",  # 字符串
            schema={"type": "integer"},
        )
        
        assert param.location == ParameterLocation.QUERY
    
    def test_to_dict(self):
        """测试转换为字典"""
        param = OpenAPIParameter(
            name="owner_id",
            location=ParameterLocation.QUERY,
            schema={"type": "string"},
            required=True,
        )
        
        param_dict = param.to_dict()
        
        assert param_dict["name"] == "owner_id"
        assert param_dict["location"] == "query"
        assert param_dict["required"] is True


class TestOpenAPIRequestBody:
    """测试 OpenAPIRequestBody 模型"""
    
    def test_create_request_body(self):
        """测试创建请求体"""
        body = OpenAPIRequestBody(
            content={
                "application/json": {
                    "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                    "example": {"name": "test"},
                }
            },
            required=True,
        )
        
        assert body.required is True
        assert "application/json" in body.content
    
    def test_get_schema(self):
        """测试获取 schema"""
        body = OpenAPIRequestBody(
            content={
                "application/json": {
                    "schema": {"type": "object"},
                }
            }
        )
        
        schema = body.get_schema("application/json")
        assert schema == {"type": "object"}
        
        # 不存在的 content-type
        schema = body.get_schema("text/plain")
        assert schema is None
    
    def test_get_example(self):
        """测试获取示例"""
        body = OpenAPIRequestBody(
            content={
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {"name": "test"},
                }
            }
        )
        
        example = body.get_example("application/json")
        assert example == {"name": "test"}


class TestOpenAPIEndpoint:
    """测试 OpenAPIEndpoint 模型"""
    
    @pytest.fixture
    def sample_endpoint(self):
        """创建示例端点"""
        return OpenAPIEndpoint(
            path="/users/{id}",
            method="get",
            operation_id="get_user_by_id",
            summary="获取用户信息",
            tags=["user"],
            parameters=[
                OpenAPIParameter(
                    name="id",
                    location=ParameterLocation.PATH,
                    schema={"type": "string"},
                    required=True,
                ),
                OpenAPIParameter(
                    name="fields",
                    location=ParameterLocation.QUERY,
                    schema={"type": "string"},
                    required=False,
                ),
            ],
        )
    
    def test_create_endpoint(self, sample_endpoint):
        """测试创建端点"""
        assert sample_endpoint.path == "/users/{id}"
        assert sample_endpoint.method == HttpMethod.GET
        assert sample_endpoint.operation_id == "get_user_by_id"
        assert len(sample_endpoint.parameters) == 2
    
    def test_get_parameters_by_location(self, sample_endpoint):
        """测试按位置获取参数"""
        path_params = sample_endpoint.get_path_parameters()
        assert len(path_params) == 1
        assert path_params[0].name == "id"
        
        query_params = sample_endpoint.get_query_parameters()
        assert len(query_params) == 1
        assert query_params[0].name == "fields"
    
    def test_get_required_parameters(self, sample_endpoint):
        """测试获取必需参数"""
        required_params = sample_endpoint.get_required_parameters()
        assert len(required_params) == 1
        assert required_params[0].name == "id"
    
    def test_to_dict(self, sample_endpoint):
        """测试转换为字典"""
        endpoint_dict = sample_endpoint.to_dict()
        
        assert endpoint_dict["path"] == "/users/{id}"
        assert endpoint_dict["method"] == "get"
        assert endpoint_dict["operation_id"] == "get_user_by_id"
        assert len(endpoint_dict["parameters"]) == 2


class TestGeneratedRequest:
    """测试 GeneratedRequest 模型"""
    
    def test_create_request(self):
        """测试创建请求"""
        request = GeneratedRequest(
            operation_id="get_user",
            path="/users/{id}",
            method="get",
            path_params={"id": "123"},
            query_params={"fields": "name,email"},
            header_params={"Authorization": "Bearer token"},
            request_body=None,
        )
        
        assert request.operation_id == "get_user"
        assert request.method == HttpMethod.GET
        assert request.path_params == {"id": "123"}
    
    def test_get_url(self):
        """测试构建 URL"""
        request = GeneratedRequest(
            operation_id="get_user",
            path="/users/{id}",
            method="get",
            path_params={"id": "123"},
            query_params={"fields": "name"},
        )
        
        # 无 base_url
        url = request.get_url()
        assert url == "/users/123?fields=name"
        
        # 有 base_url
        url = request.get_url("https://api.example.com")
        assert url == "https://api.example.com/users/123?fields=name"
    
    def test_to_dict(self):
        """测试转换为字典"""
        request = GeneratedRequest(
            operation_id="create_user",
            path="/users",
            method="post",
            request_body={"name": "test"},
        )
        
        request_dict = request.to_dict()
        
        assert request_dict["operation_id"] == "create_user"
        assert request_dict["method"] == "post"
        assert request_dict["request_body"] == {"name": "test"}
    
    def test_to_dict_with_resolved_path(self):
        """测试转换为字典包含 resolved_path 字段（Bug Fix: 路径参数实例化）"""
        request = GeneratedRequest(
            operation_id="get_user",
            path="/users/{id}/posts/{post_id}",
            method="get",
            path_params={"id": "123", "post_id": "456"},
            query_params={"fields": "title"},
        )
        
        request_dict = request.to_dict()
        
        # 验证原始路径
        assert request_dict["path"] == "/users/{id}/posts/{post_id}"
        
        # 验证实例化后的路径
        assert request_dict["resolved_path"] == "/users/123/posts/456"
        
        # 验证路径参数也被保存
        assert request_dict["path_params"] == {"id": "123", "post_id": "456"}
    
    def test_resolved_path_with_no_params(self):
        """测试无路径参数时的 resolved_path"""
        request = GeneratedRequest(
            operation_id="list_users",
            path="/users",
            method="get",
        )
        
        request_dict = request.to_dict()
        
        # 无参数时，resolved_path 等于原始 path
        assert request_dict["path"] == "/users"
        assert request_dict["resolved_path"] == "/users"
