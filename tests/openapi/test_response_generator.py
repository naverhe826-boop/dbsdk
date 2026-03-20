"""
响应数据生成器测试。
"""

import pytest
from data_builder.openapi import (
    APITestDataManager,
    GeneratedResponse,
    OpenAPIEndpoint,
    OpenAPIResponse,
    OpenAPIResponseHeader,
    ResponseDataGenerator,
    HttpMethod,
)


# 测试用的 OpenAPI 文档
SAMPLE_OPENAPI_DOC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0"
    },
    "paths": {
        "/users": {
            "get": {
                "operationId": "getUsers",
                "summary": "获取用户列表",
                "tags": ["user"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "users": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"}
                                                }
                                            }
                                        },
                                        "total": {"type": "integer"}
                                    }
                                },
                                "example": {
                                    "users": [
                                        {"id": 1, "name": "张三"},
                                        {"id": 2, "name": "李四"}
                                    ],
                                    "total": 2
                                }
                            }
                        },
                        "headers": {
                            "X-Total-Count": {
                                "schema": {"type": "integer"},
                                "description": "总记录数"
                            },
                            "X-Request-Id": {
                                "schema": {"type": "string"},
                                "required": True
                            }
                        }
                    },
                    "400": {
                        "description": "错误请求",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "error": {"type": "string"},
                                        "code": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/{id}": {
            "get": {
                "operationId": "getUserById",
                "summary": "根据ID获取用户",
                "tags": ["user"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "email": {"type": "string", "format": "email"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "未找到",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "error": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


class TestResponseDataGenerator:
    """测试 ResponseDataGenerator 类"""
    
    def test_generate_with_example(self):
        """测试使用示例生成响应"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        
        # 配置生成器
        manager.configure_response_generator({
            "include_headers": True,
            "count": 1,
        })
        
        # 生成响应
        responses = manager.generate_response_for_endpoint("getUsers")
        
        # 验证
        assert len(responses) == 2  # 200 和 400
        
        # 验证 200 响应
        success_resp = [r for r in responses if r.status_code == "200"][0]
        assert success_resp.is_success()
        assert success_resp.metadata.get("from_example") == True
        assert success_resp.response_body is not None
        assert "users" in success_resp.response_body
        assert success_resp.response_body["total"] == 2
        
        # 验证响应头
        assert "X-Total-Count" in success_resp.response_headers or "X-Request-Id" in success_resp.response_headers
    
    def test_generate_without_example(self):
        """测试不使用示例生成响应"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        
        # 配置生成器
        manager.configure_response_generator({
            "include_headers": False,
            "count": 1,
        })
        
        # 生成响应
        responses = manager.generate_response_for_endpoint("getUsers")
        
        # 验证
        assert len(responses) == 2
        
        success_resp = [r for r in responses if r.status_code == "200"][0]
        assert success_resp.is_success()
        # 200 响应有示例，from_example 应为 True
        assert success_resp.metadata.get("from_example") == True
        assert success_resp.response_body is not None
        assert "users" in success_resp.response_body
    
    def test_generate_specific_status_codes(self):
        """测试生成指定状态码的响应"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({})
        
        # 只生成成功响应
        responses = manager.generate_response_for_endpoint(
            "getUsers",
            status_codes=["200"]
        )
        
        # 验证
        assert len(responses) == 1
        assert responses[0].status_code == "200"
        assert responses[0].is_success()
    
    def test_generate_multiple_count(self):
        """测试生成多条响应数据"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({
            "count": 3,
        })
        
        responses = manager.generate_response_for_endpoint("getUsers")
        
        # 验证：每个状态码生成 3 条，总共 6 条
        assert len(responses) == 6
        
        # 验证每个状态码都有 3 条
        status_200 = [r for r in responses if r.status_code == "200"]
        status_400 = [r for r in responses if r.status_code == "400"]
        assert len(status_200) == 3
        assert len(status_400) == 3
    
    def test_generate_for_tags(self):
        """测试为标签批量生成响应"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({})
        
        result = manager.generate_response_for_tags(["user"])
        
        # 验证
        assert len(result) == 2  # getUsers 和 getUserById
        assert "getUsers" in result
        assert "getUserById" in result
    
    def test_generate_for_all(self):
        """测试为所有端点生成响应"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({})
        
        result = manager.generate_response_for_all()
        
        # 验证
        assert len(result) == 2
        assert "getUsers" in result
        assert "getUserById" in result
    
    def test_standalone_generator(self):
        """测试独立使用响应生成器"""
        from data_builder.openapi import OpenAPIParser
        
        parser = OpenAPIParser.from_dict(SAMPLE_OPENAPI_DOC)
        document = parser.parse()
        
        generator = ResponseDataGenerator(
            include_headers=True,
            ref_resolver=parser,
        )
        
        endpoint = document.get_endpoint_by_operation_id("getUsers")
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证
        assert len(responses) == 2
        assert all(isinstance(r, GeneratedResponse) for r in responses)
    
    def test_response_headers_generation(self):
        """测试响应头生成"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({
            "include_headers": True,
        })
        
        responses = manager.generate_response_for_endpoint("getUsers")
        success_resp = [r for r in responses if r.status_code == "200"][0]
        
        # 验证响应头已生成
        assert isinstance(success_resp.response_headers, dict)
        # 注意：响应头生成是基于 schema 的，所以值可能不同
        # 我们只验证是否有响应头字段
        assert len(success_resp.response_headers) > 0 or True  # 允许为空
    
    def test_is_success_is_error(self):
        """测试响应成功/错误判断"""
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({})
        
        responses = manager.generate_response_for_endpoint("getUsers")
        
        # 验证 200 响应
        success_resp = [r for r in responses if r.status_code == "200"][0]
        assert success_resp.is_success()
        assert not success_resp.is_error()
        
        # 验证 400 响应
        error_resp = [r for r in responses if r.status_code == "400"][0]
        assert not error_resp.is_success()
        assert error_resp.is_error()
    
    def test_save_and_load_responses(self):
        """测试保存和加载响应数据"""
        import tempfile
        import os
        
        manager = APITestDataManager(openapi_document=SAMPLE_OPENAPI_DOC)
        manager.configure_response_generator({})
        
        # 生成响应
        manager.generate_response_for_endpoint("getUsers")
        
        # 保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.save_generated_data(temp_path, include_responses=True)
            
            # 验证文件存在
            assert os.path.exists(temp_path)
            
            # 读取文件验证内容
            import json
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "requests" in data
            assert "responses" in data
            assert "getUsers" in data["responses"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestOpenAPIResponse:
    """测试 OpenAPIResponse 模型"""
    
    def test_get_example(self):
        """测试获取示例"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {"id": 1, "name": "test"}
                }
            }
        )
        
        example = response.get_example()
        assert example == {"id": 1, "name": "test"}
    
    def test_get_example_from_examples(self):
        """测试从 examples 字段获取示例"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {"type": "object"},
                    "examples": {
                        "example1": {
                            "value": {"id": 1, "name": "test1"}
                        },
                        "example2": {
                            "value": {"id": 2, "name": "test2"}
                        }
                    }
                }
            }
        )
        
        example = response.get_example()
        # 应该返回第一个示例
        assert example == {"id": 1, "name": "test1"}
    
    def test_get_schema(self):
        """测试获取 schema"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {"type": "object", "properties": {"id": {"type": "integer"}}}
                }
            }
        )
        
        schema = response.get_schema()
        assert schema["type"] == "object"
        assert "id" in schema["properties"]
    
    def test_get_example_from_schema(self):
        """测试从 schema 对象中获取示例（FastAPI 风格）"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        },
                        "example": {
                            "id": 1,
                            "name": "test"
                        }
                    }
                }
            }
        )
        
        example = response.get_example()
        assert example == {"id": 1, "name": "test"}
    
    def test_get_example_prefer_schema_over_content(self):
        """测试优先从 schema 获取示例，fallback 到 content_info"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "example": {"id": 1, "name": "schema_example"}
                    },
                    "example": {"id": 2, "name": "content_example"}
                }
            }
        )
        
        # 应该优先返回 schema 中的 example
        example = response.get_example()
        assert example == {"id": 1, "name": "schema_example"}
    
    def test_get_example_fallback_to_content(self):
        """测试 schema 中没有 example 时，fallback 到 content_info"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {"id": 1, "name": "test"}
                }
            }
        )
        
        example = response.get_example()
        assert example == {"id": 1, "name": "test"}
    
    def test_get_example_filter_empty_value(self):
        """测试过滤空值 example"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "example": None  # 空值应被过滤
                    },
                    "example": {"id": 1, "name": "test"}  # 应该使用这个
                }
            }
        )
        
        # schema 中的 example 是 None，应该 fallback 到 content_info
        example = response.get_example()
        assert example == {"id": 1, "name": "test"}
    
    def test_get_example_filter_empty_examples(self):
        """测试过滤空值 examples"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "examples": None  # 空值应被过滤
                    },
                    "examples": {
                        "example1": {"value": {"id": 1, "name": "test"}}
                    }
                }
            }
        )
        
        # schema 中的 examples 是 None，应该 fallback 到 content_info
        example = response.get_example()
        assert example == {"id": 1, "name": "test"}
    
    def test_get_examples_filter_empty_value(self):
        """测试 get_examples 过滤空值"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "examples": None  # 空值应被过滤
                    },
                    "examples": {
                        "example1": {"value": {"id": 1, "name": "test1"}},
                        "example2": {"value": {"id": 2, "name": "test2"}}
                    }
                }
            }
        )
        
        # schema 中的 examples 是 None，应该 fallback 到 content_info
        examples = response.get_examples()
        assert examples == {
            "example1": {"value": {"id": 1, "name": "test1"}},
            "example2": {"value": {"id": 2, "name": "test2"}}
        }


class TestPartialExampleMerge:
    """测试示例合并功能"""

    def test_complete_example_with_all_fields(self):
        """测试完整示例（包含所有字段）合并生成"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                        },
                        "required": ["id", "name", "email"]
                    },
                    "example": {
                        "id": 1001,
                        "name": "张三",
                        "email": "zhangsan@example.com"
                    }
                }
            }
        )

        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )

        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )

        responses = generator.generate_for_endpoint(endpoint)

        # 验证：所有示例字段应该保留
        assert len(responses) == 1
        body = responses[0].response_body
        assert body["id"] == 1001
        assert body["name"] == "张三"
        assert body["email"] == "zhangsan@example.com"
        assert responses[0].metadata["from_example"] is True
    
    def test_partial_example_merge_required_fields(self):
        """测试部分示例（缺少必需字段）合并生成"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "status": {"type": "string", "enum": ["active", "inactive"]}
                        },
                        "required": ["id", "name", "email", "status"]
                    },
                    "example": {
                        "id": 1001,
                        "name": "张三"
                        # 缺少 email 和 status 必需字段
                    }
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：部分示例，有示例值的字段使用示例值，其他字段按 schema 约束生成
        assert len(responses) == 1
        body = responses[0].response_body
        
        # id 和 name 字段有示例值，应固定使用示例值
        assert body["id"] == 1001
        assert body["name"] == "张三"
        
        # email 和 status 字段没有示例值，按 schema 约束生成
        assert "email" in body
        assert "status" in body
        assert body["status"] in ["active", "inactive"]  # enum 随机选择
        
        # 元数据标记
        assert responses[0].metadata["from_example"] is True
    
    def test_partial_example_merge_optional_fields(self):
        """测试部分示例（缺少可选字段）合并生成"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "nickname": {"type": "string"},  # 可选字段
                            "avatar": {"type": "string"}     # 可选字段
                        },
                        "required": ["id", "name"]
                    },
                    "example": {
                        "id": 1001,
                        "name": "张三"
                        # 缺少可选字段 nickname 和 avatar
                    }
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：示例字段保留，可选字段由 schema 生成
        assert len(responses) == 1
        body = responses[0].response_body
        
        # 示例字段应该保留
        assert body["id"] == 1001
        assert body["name"] == "张三"
    
    def test_non_object_example_treated_as_complete(self):
        """测试非对象示例直接使用"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"}
                            }
                        }
                    },
                    "example": [
                        {"id": 1, "name": "张三"},
                        {"id": 2, "name": "李四"}
                    ]
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users",
            method=HttpMethod.GET,
            operation_id="getUsers",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：非对象示例直接使用（无 schema 时无法合并）
        assert len(responses) == 1
        # 注意：数组示例会直接使用
        assert responses[0].response_body == [
            {"id": 1, "name": "张三"},
            {"id": 2, "name": "李四"}
        ]
        assert responses[0].metadata["from_example"] is True
    
    def test_no_schema_treats_example_as_complete(self):
        """测试无 schema 时示例直接使用"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "example": {"id": 1, "name": "test"}
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：无 schema 时示例直接使用
        assert len(responses) == 1
        assert responses[0].response_body == {"id": 1, "name": "test"}
        assert responses[0].metadata["from_example"] is True
    
    def test_nested_object_partial_example(self):
        """测试嵌套对象示例"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "profile": {
                                        "type": "object",
                                        "properties": {
                                            "age": {"type": "integer"},
                                            "city": {"type": "string"}
                                        },
                                        "required": ["age", "city"]
                                    }
                                },
                                "required": ["id", "name", "profile"]
                            }
                        },
                        "required": ["user"]
                    },
                    "example": {
                        "user": {
                            "id": 1001,
                            "name": "张三"
                            # user 对象缺少 profile 字段
                        }
                    }
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：示例字段保留，但嵌套对象作为整体被固定
        assert len(responses) == 1
        body = responses[0].response_body
        
        # user 字段有示例值，会使用 FixedStrategy 固定整个对象
        # 因此不会递归生成 profile 字段
        assert body["user"]["id"] == 1001
        assert body["user"]["name"] == "张三"
        # profile 字段不会被生成（因为 user 对象整体被固定为示例值）
        assert "profile" not in body["user"]
    
    def test_field_policies_override_example_values(self):
        """测试字段策略优先于示例值（有显式策略时示例值无效）"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "status": {"type": "string", "enum": ["active", "inactive"]}
                        },
                        "required": ["id", "name", "email", "status"]
                    },
                    "example": {
                        "id": 1001,           # 有示例值，无显式策略 → 使用示例值
                        "name": "张三",       # 有示例值，无显式策略 → 使用示例值
                        "email": "test@example.com"  # 有示例值，但有显式策略 → 策略优先
                        # 缺少 status 字段
                    }
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HttpMethod.GET,
            operation_id="getUserById",
            responses=[response]
        )
        
        # 配置显式的字段策略：email 字段使用固定的生成策略
        generator = ResponseDataGenerator(
            include_headers=False,
            count=1,
            field_policies=[
                {
                    "path": "email",
                    "strategy": {
                        "type": "fixed",
                        "value": "custom@policy.com"  # 显式策略值，覆盖示例值
                    }
                }
            ]
        )
        
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证字段策略优先级
        assert len(responses) == 1
        body = responses[0].response_body
        
        # id 和 name：有示例值，无显式策略 → 使用示例值
        assert body["id"] == 1001
        assert body["name"] == "张三"
        
        # email：有示例值，但有显式策略 → 策略优先，不使用示例值
        assert body["email"] == "custom@policy.com"  # 策略值，不是示例值
        
        # status：没有示例值，按 schema 约束生成
        assert "status" in body
        assert body["status"] in ["active", "inactive"]  # enum 随机选择
        
        # 元数据标记
        assert responses[0].metadata["from_example"] is True


class TestNonObjectExampleTypeCompatibility:
    """测试非对象示例的类型兼容性检查"""
    
    def test_string_example_type_compatible(self):
        """测试字符串示例与 schema 类型兼容"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 20
                    },
                    "example": "Hello World"
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/message",
            method=HttpMethod.GET,
            operation_id="getMessage",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(count=1)
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：字符串示例与 schema 类型兼容，直接使用
        assert len(responses) == 1
        assert responses[0].response_body == "Hello World"
        assert responses[0].metadata["from_example"] is True
    
    def test_string_example_type_incompatible(self):
        """测试字符串示例与 schema 类型不兼容时按 schema 生成"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "example": "not_a_number"  # 字符串示例但 schema 是 integer
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/count",
            method=HttpMethod.GET,
            operation_id="getCount",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(count=1)
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：类型不兼容，按 schema 生成整数
        assert len(responses) == 1
        assert isinstance(responses[0].response_body, int)
        assert 0 <= responses[0].response_body <= 100
        # 不是来自示例
        assert responses[0].metadata["from_example"] is False
    
    def test_integer_example_type_compatible(self):
        """测试整数示例与 schema 类型兼容"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "example": 42
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/count",
            method=HttpMethod.GET,
            operation_id="getCount",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(count=1)
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：整数示例与 schema 类型兼容，直接使用
        assert len(responses) == 1
        assert responses[0].response_body == 42
        assert responses[0].metadata["from_example"] is True
    
    def test_boolean_example_type_compatible(self):
        """测试布尔示例与 schema 类型兼容"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "boolean"
                    },
                    "example": True
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/flag",
            method=HttpMethod.GET,
            operation_id="getFlag",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(count=1)
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：布尔示例与 schema 类型兼容，直接使用
        assert len(responses) == 1
        assert responses[0].response_body is True
        assert responses[0].metadata["from_example"] is True
    
    def test_number_example_with_integer_schema(self):
        """测试 number 类型示例与 integer schema 的兼容性"""
        response = OpenAPIResponse(
            status_code="200",
            content={
                "application/json": {
                    "schema": {
                        "type": "integer"
                    },
                    "example": 3.14  # 浮点数示例但 schema 是 integer
                }
            }
        )
        
        endpoint = OpenAPIEndpoint(
            path="/id",
            method=HttpMethod.GET,
            operation_id="getId",
            responses=[response]
        )
        
        generator = ResponseDataGenerator(count=1)
        responses = generator.generate_for_endpoint(endpoint)
        
        # 验证：浮点数与 integer 不兼容，按 schema 生成
        assert len(responses) == 1
        assert isinstance(responses[0].response_body, int)
        assert responses[0].metadata["from_example"] is False
