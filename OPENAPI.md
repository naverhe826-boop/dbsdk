# OpenAPI 测试数据生成器

基于 `data_builder` 框架的 OpenAPI 请求数据生成器，支持从 OpenAPI 文档自动生成测试数据。

## 🎯 核心功能

### 1. OpenAPI 文档解析
- ✅ 支持 OpenAPI 3.x 规范
- ✅ 解析 paths、operationId、parameters、requestBody
- ✅ 自动解析 `$ref` 引用（包括循环引用）
- ✅ 支持 JSON 和 YAML 格式

### 2. Schema 转换
- ✅ OpenAPI Schema → JSON Schema 转换
- ✅ 处理 `nullable` → `type: ["string", "null"]`
- ✅ 处理 `example` → `examples` 数组
- ✅ 保留语义字段（deprecated、readOnly、writeOnly）

### 3. 多模式数据生成
支持 6 种生成模式，可单独使用或组合使用：

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| `RANDOM` | 随机生成数据 | 冒烟测试、快速验证 |
| `BOUNDARY` | 边界值测试 | 边界条件测试 |
| `EQUIVALENCE` | 等价类测试 | 分类覆盖测试 |
| `CARTESIAN` | 笛卡尔积组合 | 全面组合测试 |
| `PAIRWISE` | 成对测试 | 组合优化测试 |
| `INVALID` | 非法值测试 | 异常处理测试 |

**多模式组合**：支持传入模式列表，为每种模式独立生成数据后自动去重合并：
```python
"generation_mode": ["boundary", "random", "equivalence"]
```

### 4. 灵活的数据管理
- ✅ 按标签、operationId、路径模式筛选端点
- ✅ 批量生成测试数据
- ✅ 自定义字段策略覆盖
- ✅ 数据持久化（JSON/YAML）

## 📦 模块结构

```
data_builder/openapi/
├── models.py              # 数据模型定义
├── parser.py              # OpenAPI 文档解析器
├── converter.py           # Schema 转换器
├── request_generator.py   # 请求数据生成器
├── response_generator.py  # 响应数据生成器
└── manager.py             # API 测试数据管理器
```

## 🚀 快速开始

### 基本使用

```python
from data_builder.openapi import APITestDataManager

# 1. 创建管理器并加载 OpenAPI 文档
manager = APITestDataManager(
    openapi_document="path/to/api.json",
    generation_config={
        "generation_mode": "boundary",  # 生成模式：支持单个或多个模式列表
        "include_optional": True,       # 包含可选字段
        "count": 5,                     # 每种模式生成 5 组数据
    }
)

# 2. 获取端点
endpoints = manager.get_all_endpoints()

# 3. 为端点生成数据
requests = manager.generate_for_endpoint(endpoints[0].operation_id)

# 4. 使用生成的数据
for req in requests:
    print(f"URL: {req.get_url('https://api.example.com')}")
    print(f"Query Params: {req.query_params}")
    print(f"Request Body: {req.request_body}")
```

### 端点筛选

```python
# 按标签筛选
endpoints = manager.get_endpoints_by_tag("user_management")

# 按 operationId 查询
endpoint = manager.get_endpoint_by_operation_id("get_user_by_id")

# 按路径和方法查询（新增）
endpoint = manager.get_endpoint_by_path_and_method("/users/{id}", "GET")

# 按路径模式筛选（支持通配符）
endpoints = manager.get_endpoints_by_path_pattern("*/users/*")
```

### 自定义字段策略

```python
manager = APITestDataManager(
    openapi_document="api.json",
    generation_config={
        "generation_mode": "random",
        "field_policies": [
            # 固定字段值
            {
                "path": "user_id",
                "strategy": {"type": "fixed", "value": "test-user-001"}
            },
            # 使用枚举值
            {
                "path": "status",
                "strategy": {
                    "type": "enum",
                    "values": ["active", "inactive", "pending"]
                }
            },
            # 使用范围策略
            {
                "path": "price",
                "strategy": {
                    "type": "range",
                    "min_val": 10.0,
                    "max_val": 1000.0,
                    "is_float": True,
                    "precision": 2
                }
            },
            # 使用随机字符串策略
            {
                "path": "order_id",
                "strategy": {
                    "type": "random_string",
                    "length": 10
                }
            },
            # 使用 Faker 生成
            {
                "path": "email",
                "strategy": {"type": "faker", "method": "email"}
            },
        ]
    }
)
```

### 批量生成

```python
# 为特定标签的所有端点生成数据
result = manager.generate_for_tags(
    tags=["user_management", "order"],
    count_per_endpoint=3
)

# 为所有端点生成数据
all_data = manager.generate_for_all(
    exclude_tags=["internal", "deprecated"],
    count_per_endpoint=2
)

# 按路径和方法生成数据（新增）
requests = manager.generate_for_path_method(
    path="/users/{id}",
    method="GET",
    count=5
)
```

### 数据持久化

```python
# 保存生成的数据
manager.save_generated_data("test_data.json")

# 保存配置
manager.save_config("config.json", openapi_path="api.json")

# 从配置加载
new_manager = APITestDataManager.from_config("config.json")
```

## 🧪 测试场景示例

### 1. 冒烟测试（快速验证）

```python
manager.configure_generator({
    "generation_mode": "random",
    "include_optional": False,  # 只包含必需字段
    "count": 1,                 # 只生成 1 组数据
})

requests = manager.generate_for_endpoint(operation_id)
# 快速验证接口可用性
```

### 2. 边界值测试

```python
manager.configure_generator({
    "generation_mode": "boundary",
    "include_optional": True,
    "count": 10,  # 生成更多边界用例
})

requests = manager.generate_for_endpoint(operation_id)
# 自动生成包含边界值的测试数据：
# - 最小/最大值
# - 空字符串/最大长度
# - 数值边界
```

### 3. 等价类测试

```python
manager.configure_generator({
    "generation_mode": "equivalence",
    "include_optional": True,
    "count": 5,
})

requests = manager.generate_for_endpoint(operation_id)
# 自动检测枚举字段和约束条件，生成等价类测试数据
```

### 4. 组合测试

```python
manager.configure_generator({
    "generation_mode": "pairwise",  # 成对组合测试
    "include_optional": True,
    "count": 20,
})

requests = manager.generate_for_endpoint(operation_id)
# 对多个字段的组合进行优化测试，减少用例数量但保持覆盖率
```

### 5. 多模式混合测试（特性）

支持同时使用多种生成策略，为每种模式独立生成数据后自动去重合并：

```python
# 同时使用边界值和随机模式
manager.configure_generator({
    "generation_mode": ["boundary", "random"],  # 多种模式
    "include_optional": True,
    "count": 5,  # 每种模式生成 5 条数据
})

requests = manager.generate_for_endpoint(operation_id)
# 结果：
# - 边界值模式生成 5 条
# - 随机模式生成 5 条
# - 自动去重后合并
# - 每条数据带有 metadata["generation_mode"] 标记来源模式

# 同时使用三种模式
manager.configure_generator({
    "generation_mode": ["boundary", "equivalence", "random"],
    "count": 3,
})
# 3 × 3 = 9 条数据（去重前）
```

## 📊 数据模型

### GeneratedRequest

生成的请求数据模型：

```python
class GeneratedRequest:
    operation_id: str           # 操作 ID
    path: str                   # API 路径
    method: HttpMethod          # HTTP 方法
    path_params: Dict           # 路径参数
    query_params: Dict          # 查询参数
    header_params: Dict         # 请求头参数
    request_body: Optional[Dict] # 请求体
    
    def get_url(self, base_url: str) -> str:
        """构建完整 URL"""
        pass
```

### OpenAPIEndpoint

API 端点模型：

```python
class OpenAPIEndpoint:
    path: str                           # API 路径
    method: HttpMethod                  # HTTP 方法
    operation_id: str                   # 操作 ID
    summary: Optional[str]              # 摘要
    description: Optional[str]          # 描述
    parameters: List[OpenAPIParameter]  # 参数列表
    request_body: Optional[OpenAPIRequestBody]  # 请求体
    tags: List[str]                     # 标签列表
    
    def get_path_parameters(self) -> List[OpenAPIParameter]:
        """获取路径参数"""
        pass
    
    def get_query_parameters(self) -> List[OpenAPIParameter]:
        """获取查询参数"""
        pass
    
    def get_required_parameters(self) -> List[OpenAPIParameter]:
        """获取必需参数"""
        pass
```

## 🔧 高级用法

### 完整测试套件

参考 `examples/openapi/openapi_advanced.py` 中的 `APITestSuite` 类，展示如何：
- 构建自动化测试工作流
- 运行多种类型的测试（冒烟、边界值、等价类）
- 生成测试报告

### 响应数据生成

`ResponseDataGenerator` 支持从 OpenAPI 响应定义自动生成 Mock 响应数据，用于 API 测试和模拟场景。

#### 核心特性

1. **多状态码支持**：支持生成特定状态码或所有状态码的响应
2. **响应头生成**：可配置是否生成响应头数据
3. **智能示例处理**：自动处理完整/部分示例，支持补全缺失字段
4. **字段策略覆盖**：支持通过 `field_policies` 覆盖响应字段的生成策略
5. **Schema 自动生成**：基于响应 Schema 约束自动生成数据

#### 基本使用

```python
from data_builder.openapi import APITestDataManager

manager = APITestDataManager(openapi_document="api.json")

# 配置响应生成器
manager.configure_response_generator({
    "include_headers": True,      # 生成响应头
    "count": 2,                   # 每个响应生成 2 条数据
    "field_policies": [           # 字段策略覆盖
        {
            "path": "price",
            "strategy": {"type": "fixed", "value": 199.99}
        }
    ]
})

# 按 operationId 生成所有响应
responses = manager.generate_response_for_endpoint("get_user")

# 生成指定状态码的响应
success_responses = manager.generate_response_for_endpoint(
    "get_user", 
    status_codes=["200", "201"]  # 只生成成功响应
)

# 批量生成响应
result = manager.generate_response_for_tags(["user", "order"])
```

#### 数据生成优先级

1. **字段策略优先**（field_policies）→ 显式指定的策略覆盖一切
2. **Schema 自动生成** → 根据 Schema 约束自动生成数据（DataBuilder 自动处理 examples）

**示例处理机制**：OpenAPI 响应中的 `example/examples` 会被自动合并到 schema 中，由 DataBuilder 统一处理。当 schema 包含 examples 时，DataBuilder 会优先使用示例值作为基础，再根据 schema 约束补全缺失字段。

#### 独立响应生成器

```python
from data_builder.openapi import ResponseDataGenerator
from data_builder.openapi import OpenAPIParser

# 独立使用响应生成器
parser = OpenAPIParser(openapi_document="api.json")
document = parser.parse()

generator = ResponseDataGenerator(
    include_headers=True,     # 包含响应头
    count=2,                  # 每个响应生成 2 条数据
    ref_resolver=parser,      # 引用解析器
    field_policies=[...]      # 字段策略
)

# 为端点生成响应
endpoint = document.get_endpoint_by_operation_id("get_users")
responses = generator.generate_for_endpoint(endpoint)

# 生成指定状态码的响应
responses = generator.generate_for_endpoint(
    endpoint,
    status_codes=["200", "404"],  # 只生成 200 和 404 响应
    count=3
)
```

#### 响应数据模型

```python
class GeneratedResponse:
    status_code: str                     # 响应状态码
    response_body: Optional[Dict]        # 响应体数据
    response_headers: Dict               # 响应头数据
    metadata: Dict                       # 元数据
    
    # 元数据包含：
    # - from_example: 是否来自示例
    # - field_policies_used: 使用的字段策略
```

### 与 HTTP 客户端集成

```python
import requests

# 生成测试数据
manager = APITestDataManager(openapi_document="api.json")
requests_data = manager.generate_for_endpoint("get_users")

# 执行 HTTP 请求
for req in requests_data:
    response = requests.get(
        req.get_url("https://api.example.com"),
        params=req.query_params,
        headers=req.header_params,
    )
    print(f"Status: {response.status_code}")
```

## 📝 示例文件

- `examples/openapi/openapi_quickstart.py` - 快速入门示例
- `examples/openapi/openapi_advanced.py` - 高级用法示例
- `examples/openapi/gen_openapi_request.py` - 请求数据生成完整功能演示（包含多模式混合测试示例）
- `examples/openapi/gen_openapi_response.py` - 响应数据 Mock 生成演示
- `examples/openapi/openapi_field_policies.py` - **新增**：field_policies 策略使用示例（enum、range、random_string 等策略）

### 新增示例：openapi_field_policies.py

该示例展示如何在 OpenAPI 测试数据生成中使用多种策略类型：

```python
from data_builder.openapi import APITestDataManager

manager = APITestDataManager(
    openapi_document=openapi_doc,
    generation_config={
        "generation_mode": "random",
        "count": 5,
        "field_policies": [
            # 1. enum 策略：限制字段值为预定义枚举值
            {
                "path": "status",
                "strategy": {
                    "type": "enum",
                    "values": ["active", "inactive", "pending"]
                }
            },
            # 2. range 策略：限制数值范围
            {
                "path": "price",
                "strategy": {
                    "type": "range",
                    "min_val": 10.0,
                    "max_val": 1000.0,
                    "is_float": True,
                    "precision": 2
                }
            },
            # 3. random_string 策略：生成固定长度的随机字符串
            {
                "path": "order_id",
                "strategy": {
                    "type": "random_string",
                    "length": 10
                }
            },
            # 4. 混合策略：同时使用多种策略类型
        ]
    }
)
```

包含的示例场景：
- `example_enum_strategy()` - enum 策略覆盖字段
- `example_range_strategy()` - range 策略生成数值  
- `example_random_string_strategy()` - random_string 策略生成字符串
- `example_mixed_strategies()` - 混合使用多种策略

## 🧪 测试

运行测试：

```bash
# 运行所有 OpenAPI 模块测试
pytest tests/openapi/ -v

# 运行特定测试
pytest tests/openapi/test_integration.py -v
```

## 📖 相关文档

- [JSONSCHEMA.md](JSONSCHEMA.md) - JSON Schema 支持说明

## 🤝 集成优势

基于 `data_builder` 框架，OpenAPI 数据生成器继承了以下优势：

- 🎯 **策略模式**：灵活的字段生成策略
- 🔄 **组合生成**：支持多种组合测试模式
- 🎨 **自定义扩展**：轻松扩展自定义策略
- 📊 **智能推导**：基于 Schema 自动推导约束
- ✅ **类型安全**：完整的类型注解支持

## 📄 许可证

MIT License
