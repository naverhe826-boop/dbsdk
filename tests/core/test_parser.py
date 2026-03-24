"""
测试 OpenAPI 文档解析器。
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from data_builder.openapi.parser import OpenAPIParser
from data_builder.openapi.models import (
    HttpMethod,
    OpenAPIDocument,
    OpenAPIEndpoint,
    OpenAPIParameter,
    OpenAPIRequestBody,
    OpenAPIResponse,
    ParameterLocation,
)


class TestOpenAPIParserInit:
    """测试 OpenAPIParser 初始化"""
    
    def test_init_with_document(self):
        """测试使用文档字典初始化"""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        
        parser = OpenAPIParser(document)
        
        assert parser.openapi_version == "3.0.0"
        assert parser.info == {"title": "Test API", "version": "1.0.0"}
        assert parser.paths == {}
    
    def test_init_default_version(self):
        """测试默认版本号"""
        document = {"info": {}, "paths": {}}
        
        parser = OpenAPIParser(document)
        
        assert parser.openapi_version == "3.0.0"


class TestOpenAPIParserFromFile:
    """测试从文件创建解析器"""
    
    def test_from_json_file(self, tmp_path):
        """测试从 JSON 文件加载"""
        document = {
            "openapi": "3.0.2",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        
        json_file = tmp_path / "api.json"
        json_file.write_text(json.dumps(document), encoding="utf-8")
        
        parser = OpenAPIParser.from_file(json_file)
        
        assert parser.openapi_version == "3.0.2"
    
    def test_from_yaml_file(self, tmp_path):
        """测试从 YAML 文件加载"""
        yaml_content = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths:
  /users:
    get:
      operationId: getUsers
      responses:
        '200':
          description: Success
"""
        yaml_file = tmp_path / "api.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")
        
        parser = OpenAPIParser.from_file(yaml_file)
        
        assert parser.openapi_version == "3.0.0"
        assert "/users" in parser.paths
    
    def test_from_dict(self):
        """测试从字典创建"""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        
        parser = OpenAPIParser.from_dict(document)
        
        assert isinstance(parser, OpenAPIParser)
        assert parser.openapi_version == "3.0.0"


class TestOpenAPIParserParse:
    """测试文档解析"""
    
    def test_parse_simple_document(self):
        """测试解析简单文档"""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {"description": "成功"}
                        }
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        assert isinstance(doc, OpenAPIDocument)
        assert doc.openapi_version == "3.0.0"
        assert doc.info["title"] == "Test API"
        assert len(doc.get_all_endpoints()) == 1
    
    def test_parse_multiple_endpoints(self):
        """测试解析多个端点"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    },
                    "post": {
                        "operationId": "createUser",
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/users/{id}": {
                    "get": {
                        "operationId": "getUser",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoints = doc.get_all_endpoints()
        assert len(endpoints) == 3
    
    def test_parse_with_parameters(self):
        """测试解析参数"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "operationId": "getUser",
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
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUser")
        assert endpoint is not None
        assert len(endpoint.parameters) == 2
        
        path_params = endpoint.get_path_parameters()
        assert len(path_params) == 1
        assert path_params[0].name == "id"
        assert path_params[0].required is True
        
        query_params = endpoint.get_query_parameters()
        assert len(query_params) == 1
        assert query_params[0].name == "fields"
    
    def test_parse_with_request_body(self):
        """测试解析请求体"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "createUser",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("createUser")
        assert endpoint.request_body is not None
        assert endpoint.request_body.required is True
        assert "application/json" in endpoint.request_body.content
    
    def test_parse_with_responses(self):
        """测试解析响应"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {
                            "200": {
                                "description": "成功",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "array"}
                                    }
                                }
                            },
                            "400": {"description": "错误请求"},
                            "500": {"description": "服务器错误"}
                        }
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUsers")
        assert len(endpoint.responses) == 3
        
        success_responses = endpoint.get_success_responses()
        assert len(success_responses) == 1
        
        error_responses = endpoint.get_error_responses()
        assert len(error_responses) == 2


class TestOpenAPIParserRefResolution:
    """测试 $ref 引用解析"""
    
    def test_resolve_schema_ref(self):
        """测试解析 schema $ref"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUsers")
        response = endpoint.responses[0]
        schema = response.get_schema("application/json")
        
        assert "type" in schema
        assert "properties" in schema
        assert "id" in schema["properties"]
    
    def test_resolve_parameter_ref(self):
        """测试解析参数 $ref"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "operationId": "getUser",
                        "parameters": [
                            {"$ref": "#/components/parameters/UserId"}
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
            "components": {
                "parameters": {
                    "UserId": {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUser")
        assert len(endpoint.parameters) == 1
        assert endpoint.parameters[0].name == "id"
    
    def test_resolve_nested_refs(self):
        """测试解析嵌套 $ref"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/UserList"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    },
                    "UserList": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/User"
                        }
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUsers")
        response = endpoint.responses[0]
        schema = response.get_schema("application/json")
        
        # 验证嵌套引用被解析
        assert schema["type"] == "array"
        assert "items" in schema
        assert "properties" in schema["items"]
    
    def test_circular_ref_handling(self):
        """测试循环引用处理"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUser",
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Node"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Node": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer"},
                            "next": {
                                "$ref": "#/components/schemas/Node"
                            }
                        }
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        # 循环引用应该被安全处理，不会导致无限递归
        doc = parser.parse()
        
        assert doc is not None


class TestOpenAPIParserHelpers:
    """测试辅助方法"""
    
    def test_get_schema_by_name(self):
        """测试根据名称获取 schema"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {},
            "components": {
                "schemas": {
                    "User": {"type": "object"}
                }
            },
        }
        
        parser = OpenAPIParser(document)
        
        user_schema = parser.get_schema_by_name("User")
        assert user_schema == {"type": "object"}
        
        not_found = parser.get_schema_by_name("NotFound")
        assert not_found is None
    
    def test_get_parameter_by_name(self):
        """测试根据名称获取参数"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {},
            "components": {
                "parameters": {
                    "UserId": {
                        "name": "id",
                        "in": "path",
                        "schema": {"type": "string"}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        
        param = parser.get_parameter_by_name("UserId")
        assert param is not None
        assert param["name"] == "id"
    
    def test_resolve_ref_path(self):
        """测试解析引用路径"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "components": {
                "schemas": {
                    "User": {"type": "object"}
                }
            },
        }
        
        parser = OpenAPIParser(document)
        
        result = parser._resolve_ref_path("#/components/schemas/User")
        assert result == {"type": "object"}
    
    def test_resolve_ref_path_invalid(self):
        """测试无效引用路径"""
        document = {
            "openapi": "3.0.0",
            "info": {},
        }
        
        parser = OpenAPIParser(document)
        
        with pytest.raises(ValueError, match="不支持的引用格式"):
            parser._resolve_ref_path("http://example.com/schema")
        
        with pytest.raises(ValueError, match="无法解析引用路径"):
            parser._resolve_ref_path("#/invalid/path")


class TestOpenAPIParserEdgeCases:
    """测试边界情况"""
    
    def test_parse_without_operation_id(self):
        """测试缺少 operationId"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoints = doc.get_all_endpoints()
        assert len(endpoints) == 1
        # operationId 应该自动生成
        assert endpoints[0].operation_id == "get_/users"
    
    def test_parse_empty_paths(self):
        """测试空路径"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {},
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        assert len(doc.get_all_endpoints()) == 0
    
    def test_parse_path_item_parameters(self):
        """测试路径级别的参数"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "parameters": [
                        {
                            "name": "version",
                            "in": "header",
                            "schema": {"type": "string"}
                        }
                    ],
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    },
                    "post": {
                        "operationId": "createUser",
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            },
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        # 两个端点都应该继承路径级参数
        get_endpoint = doc.get_endpoint_by_operation_id("getUsers")
        post_endpoint = doc.get_endpoint_by_operation_id("createUser")
        
        assert len(get_endpoint.parameters) == 1
        assert len(post_endpoint.parameters) == 1
    
    def test_parse_with_tags(self):
        """测试解析标签"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "tags": ["user", "list"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
            "tags": [
                {"name": "user", "description": "User operations"},
                {"name": "list", "description": "List operations"}
            ],
        }
        
        parser = OpenAPIParser(document)
        doc = parser.parse()
        
        endpoint = doc.get_endpoint_by_operation_id("getUsers")
        assert endpoint.tags == ["user", "list"]
        assert len(doc.tags) == 2
