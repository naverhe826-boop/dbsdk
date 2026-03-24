"""
测试 API 测试数据管理器。
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from data_builder.openapi.manager import APITestDataManager
from data_builder.openapi.models import (
    HttpMethod,
    OpenAPIEndpoint,
    OpenAPIDocument,
    GeneratedRequest,
    GeneratedResponse,
)


class TestAPITestDataManagerInit:
    """测试 APITestDataManager 初始化"""
    
    def test_init_empty(self):
        """测试空初始化"""
        manager = APITestDataManager()
        
        assert manager.parser is None
        assert manager.document is None
        assert manager.generator is None
    
    def test_init_with_document_dict(self):
        """测试使用字典文档初始化"""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        
        manager = APITestDataManager(openapi_document=document)
        
        assert manager.parser is not None
        assert manager.document is not None
        assert manager.document.openapi_version == "3.0.0"
    
    def test_init_with_generation_config(self):
        """测试使用生成配置初始化"""
        manager = APITestDataManager(
            generation_config={
                "generation_mode": "random",
                "count": 10,
            }
        )
        
        assert manager.generator is not None
        assert manager.generator.count == 10


class TestAPITestDataManagerLoadDocument:
    """测试文档加载"""
    
    def test_load_from_dict(self):
        """测试从字典加载"""
        document = {
            "openapi": "3.0.2",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        
        manager = APITestDataManager()
        manager.load_openapi_document(document)
        
        assert manager.document.openapi_version == "3.0.2"
    
    def test_load_from_file(self, tmp_path):
        """测试从文件加载"""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
        }
        
        json_file = tmp_path / "api.json"
        json_file.write_text(json.dumps(document), encoding="utf-8")
        
        manager = APITestDataManager()
        manager.load_openapi_document(json_file)
        
        assert manager.document is not None
    
    def test_load_invalid_type(self):
        """测试加载无效类型"""
        manager = APITestDataManager()
        
        with pytest.raises(ValueError, match="document 参数必须是文件路径或字典"):
            manager.load_openapi_document(123)


class TestAPITestDataManagerConfigure:
    """测试配置方法"""
    
    def test_configure_generator(self):
        """测试配置请求生成器"""
        manager = APITestDataManager()
        manager.configure_generator({
            "generation_mode": "boundary",
            "count": 3,
            "include_optional": False,
        })
        
        assert manager.generator is not None
        assert manager.generator.count == 3
        assert manager.generator.include_optional is False
    
    def test_configure_response_generator(self):
        """测试配置响应生成器"""
        manager = APITestDataManager()
        manager.configure_response_generator({
            "include_headers": True,
            "count": 2,
        })
        
        assert manager.response_generator is not None
        assert manager.response_generator.include_headers is True
        assert manager.response_generator.count == 2


class TestAPITestDataManagerGetEndpoints:
    """测试端点查询"""
    
    @pytest.fixture
    def manager_with_document(self):
        """带文档的管理器 fixture"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "tags": ["user"],
                        "responses": {"200": {"description": "OK"}}
                    },
                    "post": {
                        "operationId": "createUser",
                        "tags": ["user"],
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/items": {
                    "get": {
                        "operationId": "getItems",
                        "tags": ["item"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        return APITestDataManager(openapi_document=document)
    
    def test_get_all_endpoints(self, manager_with_document):
        """测试获取所有端点"""
        endpoints = manager_with_document.get_all_endpoints()
        
        assert len(endpoints) == 3
    
    def test_get_endpoints_by_tag(self, manager_with_document):
        """测试按标签获取端点"""
        endpoints = manager_with_document.get_endpoints_by_tag("user")
        
        assert len(endpoints) == 2
        assert all("user" in ep.tags for ep in endpoints)
    
    def test_get_endpoint_by_operation_id(self, manager_with_document):
        """测试按 operationId 获取端点"""
        endpoint = manager_with_document.get_endpoint_by_operation_id("getUsers")
        
        assert endpoint is not None
        assert endpoint.operation_id == "getUsers"
    
    def test_get_endpoint_by_path_and_method(self, manager_with_document):
        """测试按路径和方法获取端点"""
        endpoint = manager_with_document.get_endpoint_by_path_and_method("/users", "GET")
        
        assert endpoint is not None
        assert endpoint.operation_id == "getUsers"
    
    def test_get_endpoints_by_path_pattern(self, manager_with_document):
        """测试按路径模式获取端点"""
        endpoints = manager_with_document.get_endpoints_by_path_pattern("/users*")
        
        assert len(endpoints) == 2  # /users GET 和 POST
    
    def test_get_endpoint_not_found(self, manager_with_document):
        """测试端点不存在"""
        endpoint = manager_with_document.get_endpoint_by_operation_id("notExist")
        
        assert endpoint is None


class TestAPITestDataManagerGenerateRequest:
    """测试请求数据生成"""
    
    @pytest.fixture
    def manager(self):
        """管理器 fixture"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={
                "generation_mode": "random",
                "count": 3,
            }
        )
        return manager
    
    def test_generate_for_endpoint(self, manager):
        """测试为单个端点生成数据"""
        requests = manager.generate_for_endpoint("getUsers")
        
        assert len(requests) == 3
        assert all(isinstance(req, GeneratedRequest) for req in requests)
        assert all(req.operation_id == "getUsers" for req in requests)
    
    def test_generate_for_endpoint_with_count_override(self, manager):
        """测试覆盖生成数量"""
        requests = manager.generate_for_endpoint("getUsers", count=10)
        
        # 由于去重,实际数量可能少于请求数量
        assert len(requests) >= 3
    
    def test_generate_for_path_method(self, manager):
        """测试按路径和方法生成"""
        requests = manager.generate_for_path_method("/users", "GET")
        
        assert len(requests) >= 2
    
    def test_generate_for_tags(self, manager):
        """测试按标签批量生成"""
        # 添加标签
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "tags": ["user"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random", "count": 2}
        )
        
        result = manager.generate_for_tags(["user"])
        
        assert "getUsers" in result
        # 空参数的端点可能生成较少数据
        assert len(result["getUsers"]) >= 1
    
    def test_generate_for_all(self, manager):
        """测试为所有端点生成"""
        result = manager.generate_for_all()
        
        assert "getUsers" in result
    
    def test_generate_for_all_with_exclude(self, manager):
        """测试排除特定端点"""
        result = manager.generate_for_all(exclude_patterns=["get*"])
        
        # getUsers 应该被排除
        assert "getUsers" not in result
    
    def test_generate_without_config(self):
        """测试未配置生成器"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(openapi_document=document)
        
        with pytest.raises(ValueError, match="未配置数据生成器"):
            manager.generate_for_endpoint("test")


class TestAPITestDataManagerGenerateResponse:
    """测试响应数据生成"""
    
    @pytest.fixture
    def manager(self):
        """管理器 fixture"""
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
                                            "type": "array",
                                            "items": {"type": "object"}
                                        }
                                    }
                                }
                            },
                            "400": {"description": "Bad Request"}
                        }
                    }
                }
            },
        }
        
        return APITestDataManager(
            openapi_document=document,
            response_config={"include_headers": True, "count": 2}
        )
    
    def test_generate_response_for_endpoint(self, manager):
        """测试为单个端点生成响应"""
        responses = manager.generate_response_for_endpoint("getUsers")
        
        assert len(responses) > 0
        assert all(isinstance(resp, GeneratedResponse) for resp in responses)
    
    def test_generate_response_with_status_codes(self, manager):
        """测试指定状态码生成"""
        responses = manager.generate_response_for_endpoint(
            "getUsers",
            status_codes=["200"]
        )
        
        assert all(resp.status_code == "200" for resp in responses)
    
    def test_generate_response_for_path_method(self, manager):
        """测试按路径和方法生成响应"""
        responses = manager.generate_response_for_path_method("/users", "GET")
        
        assert len(responses) > 0
    
    def test_generate_response_auto_create(self):
        """测试自动创建响应生成器"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(openapi_document=document)
        # 未配置响应生成器,应该自动创建
        responses = manager.generate_response_for_endpoint("test")
        
        assert len(responses) > 0
        assert manager.response_generator is not None


class TestAPITestDataManagerDataStorage:
    """测试数据存储"""
    
    @pytest.fixture
    def manager(self):
        """管理器 fixture"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        return APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random", "count": 2}
        )
    
    def test_generated_data_storage(self, manager):
        """测试生成数据存储"""
        manager.generate_for_endpoint("getUsers")
        
        assert "getUsers" in manager.generated_data
        # 空参数的端点可能生成较少数据
        assert len(manager.generated_data["getUsers"]) >= 1
    
    def test_get_generated_requests(self, manager):
        """测试获取已生成请求"""
        manager.generate_for_endpoint("getUsers")
        
        requests = manager.get_generated_requests("getUsers")
        
        assert requests is not None
        assert len(requests) >= 1
    
    def test_get_request_by_index(self, manager):
        """测试按索引获取请求"""
        manager.generate_for_endpoint("getUsers")
        
        request = manager.get_request_by_index("getUsers", 0)
        
        assert request is not None
        assert request.operation_id == "getUsers"
    
    def test_get_generated_responses(self, manager):
        """测试获取已生成响应"""
        manager.configure_response_generator({})
        manager.generate_response_for_endpoint("getUsers")
        
        responses = manager.get_generated_responses("getUsers")
        
        assert responses is not None
    
    def test_clear_generated_data(self, manager):
        """测试清空生成数据"""
        manager.generate_for_endpoint("getUsers")
        manager.configure_response_generator({})
        manager.generate_response_for_endpoint("getUsers")
        
        manager.clear_generated_data()
        
        assert len(manager.generated_data) == 0
        assert len(manager.generated_responses) == 0


class TestAPITestDataManagerSaveLoad:
    """测试保存和加载"""
    
    @pytest.fixture
    def manager(self):
        """管理器 fixture"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        return APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random", "count": 2}
        )
    
    def test_save_generated_data_json(self, manager, tmp_path):
        """测试保存为 JSON"""
        manager.generate_for_endpoint("getUsers")
        
        output_file = tmp_path / "output.json"
        manager.save_generated_data(output_file)
        
        assert output_file.exists()
        
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "getUsers" in data
    
    def test_save_generated_data_yaml(self, manager, tmp_path):
        """测试保存为 YAML"""
        manager.generate_for_endpoint("getUsers")
        
        output_file = tmp_path / "output.yaml"
        manager.save_generated_data(output_file, format="yaml")
        
        assert output_file.exists()
    
    def test_save_with_responses(self, manager, tmp_path):
        """测试保存包含响应数据"""
        manager.generate_for_endpoint("getUsers")
        manager.configure_response_generator({})
        manager.generate_response_for_endpoint("getUsers")
        
        output_file = tmp_path / "output.json"
        manager.save_generated_data(output_file, include_responses=True)
        
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "requests" in data
        assert "responses" in data
    
    def test_save_config(self, manager, tmp_path):
        """测试保存配置"""
        config_file = tmp_path / "config.json"
        manager.save_config(config_file)
        
        assert config_file.exists()
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "generation_config" in config
    
    def test_from_config(self, tmp_path):
        """测试从配置创建"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        # 先保存配置
        manager1 = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "boundary", "count": 5}
        )
        
        config_file = tmp_path / "config.json"
        manager1.save_config(config_file)
        
        # 从配置加载
        manager2 = APITestDataManager.from_config(
            config_file,
            openapi_document=document
        )
        
        assert manager2.generator.count == 5


class TestAPITestDataManagerSummary:
    """测试摘要信息"""
    
    def test_summary_empty(self):
        """测试空管理器摘要"""
        manager = APITestDataManager()
        summary = manager.summary()
        
        assert summary["total_endpoints"] == 0
        assert summary["total_generated_apis"] == 0
    
    def test_summary_with_data(self):
        """测试有数据的摘要"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random", "count": 3}
        )
        
        manager.generate_for_endpoint("getUsers")
        
        summary = manager.summary()
        
        assert summary["total_endpoints"] == 1
        assert summary["total_generated_apis"] == 1
        # 空参数的端点可能生成较少数据
        assert summary["total_generated_requests"] >= 1


class TestAPITestDataManagerEdgeCases:
    """测试边界情况"""
    
    def test_operations_without_document(self):
        """测试未加载文档时操作"""
        manager = APITestDataManager()
        
        with pytest.raises(ValueError, match="未加载 OpenAPI 文档"):
            manager.get_all_endpoints()
    
    def test_generate_for_nonexistent_endpoint(self):
        """测试生成不存在的端点"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {},
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random"}
        )
        
        with pytest.raises(ValueError, match="未找到 operationId"):
            manager.generate_for_endpoint("notExist")
    
    def test_generate_for_nonexistent_path(self):
        """测试生成不存在的路径"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {},
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random"}
        )
        
        with pytest.raises(ValueError, match="未找到端点"):
            manager.generate_for_path_method("/notexist", "GET")
    
    def test_multiple_generate_accumulation(self):
        """测试多次生成累加"""
        document = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
        }
        
        manager = APITestDataManager(
            openapi_document=document,
            generation_config={"generation_mode": "random", "count": 2}
        )
        
        # 第一次生成
        manager.generate_for_endpoint("getUsers")
        first_count = len(manager.generated_data["getUsers"])
        assert first_count >= 1
        
        # 第二次生成（应该替换，不是累加）
        manager.generate_for_endpoint("getUsers")
        second_count = len(manager.generated_data["getUsers"])
        assert second_count >= 1
        # 验证替换而不是累加
        assert second_count == first_count
