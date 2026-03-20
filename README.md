# dbsdk

基于策略模式的 Python 数据生成框架，支持 JSON Schema 和 OpenAPI 文档批量生成测试数据。

## 安装

```bash
./install.sh setup          # 当前版本安装
./install.sh setup 0.3.0    # 指定版本号安装
./install.sh list           # 查看版本及安装状态
./install.sh remove         # 卸载
```

### 依赖说明

**核心依赖**（自动安装）：
- `faker` - 虚拟数据生成库
- `exrex` - 正则表达式数据生成
- `python-dotenv` - 环境变量加载
- `pyyaml` - YAML 文件解析
- `idna` - 国际化域名支持

**可选依赖**：
- `openai` - LLMStrategy 需要（`pip install dbsdk[llm]`）
- `pytest` - 测试框架（`pip install dbsdk[dev]`）

## 模块组织

项目采用模块化设计，核心模块按职责分离：

- **`config.py`** (~250 行) - 配置管理
  - `FieldPolicy` - 字段策略配置
  - `BuilderConfig` - 构建器配置
  - 支持从字典/文件动态加载配置

- **`generators.py`** (~650 行) - 值生成器
  - `SchemaResolver` - Schema 解析器（处理 $ref、allOf 等）
  - `ValueGenerator` - 值生成器（对象、数组、基本类型）

- **`combination_builder.py`** (~220 行) - 组合模式构建器
  - `CombinationBuilder` - 组合测试数据生成
  - 支持笛卡尔积、成对组合、正交数组等模式

- **`builder.py`** (~150 行) - 核心入口
  - `DataBuilder` - 主入口类
  - 组合其他模块，提供统一 API

**设计原则**：组合模式、单一职责、向后兼容。

## 快速开始

```python
from data_builder import DataBuilder, BuilderConfig, FieldPolicy
from data_builder import fixed, seq, faker, range_int, enum, datetime

schema = {
    "type": "object",
    "properties": {
        "id":     {"type": "integer"},
        "name":   {"type": "string"},
        "status": {"type": "string"},
        "amount": {"type": "number"},
        "created_at": {"type": "string"}
    }
}

config = BuilderConfig(policies=[
    FieldPolicy("id",         seq(start=1001)),
    FieldPolicy("name",       faker("name")),
    FieldPolicy("status",     enum(["active", "inactive", "pending"])),
    FieldPolicy("amount",     range_int(100, 9999)),
    FieldPolicy("created_at", datetime()),
])

builder = DataBuilder(schema, config)
records = builder.build(count=10)
```

### 通过 dict 动态构建

支持从字典动态构建配置，无需显式导入 `BuilderConfig`：

```python
from data_builder import DataBuilder

schema = {
    "type": "object",
    "properties": {
        "id":     {"type": "integer"},
        "name":   {"type": "string"},
        "status": {"type": "string"},
        "amount": {"type": "number"},
    }
}

# 通过 dict 动态构建配置
config_dict = {
    "policies": [
        {"path": "id",      "strategy": {"type": "sequence", "start": 1001}},
        {"path": "name",    "strategy": {"type": "faker",    "method": "name"}},
        {"path": "status",  "strategy": {"type": "enum",     "values": ["active", "inactive", "pending"]}},
        {"path": "amount",  "strategy": {"type": "range",    "min": 100, "max": 9999}},
    ],
    "count": 10
}

records = DataBuilder(schema).config_from_dict(config_dict).build()
```

也支持 `params` 嵌套写法：

```python
config_dict = {
    "policies": [
        {"path": "id", "strategy": {
            "type": "sequence",
            "params": {"start": 1001, "prefix": "ORD-", "padding": 6}
        }},
    ]
}
DataBuilder(schema).config_from_dict(config_dict).build()
```

## 使用方式概述

dbsdk 支持两种主要的测试数据生成方式：**JSON Schema** 和 **OpenAPI** 文档。

### 1. JSON Schema 方式

适用于已有 JSON Schema 定义，需要生成结构化测试数据的场景。

```python
from data_builder import DataBuilder, BuilderConfig, FieldPolicy

schema = {"type": "object", "properties": {...}}
builder = DataBuilder(schema, config=BuilderConfig(policies=[...]))
data = builder.build(count=5)
```

**核心特性**：
- 20+ 内置策略：fixed、enum、range、seq、faker、datetime、email、password、ipv4/ipv6、domain、url、mac、cidr、regex 等
- 组合生成：支持 CARTESIAN、PAIRWISE、ORTHOGONAL、EQUIVALENCE、BOUNDARY、INVALID 模式
- 智能推导：自动根据 schema 的 format、enum、pattern、字段名语义生成数据
- 动态配置：支持从 dict/JSON/YAML 文件加载配置
- 高级功能：字段引用（ref）、自定义函数（callable_strategy）、LLM 生成（llm）、联合类型、nullable

### 2. OpenAPI 方式

适用于从 OpenAPI 3.x 文档自动生成 API 测试数据的场景。

```python
from data_builder.openapi import APITestDataManager

manager = APITestDataManager(openapi_document="api.json")
requests = manager.generate_for_endpoint("get_user")
```

**核心特性**：
- 文档解析：支持 JSON/YAML，自动解析 $ref 引用（含循环引用）
- Schema 转换：OpenAPI Schema → JSON Schema，处理 nullable、example
- 多模式生成：RANDOM、BOUNDARY、EQUIVALENCE、CARTESIAN、PAIRWISE、INVALID，支持多模式混合
- 端点筛选：按标签、operationId、路径模式筛选
- 响应生成：支持生成 Mock 响应数据，包含响应头、多状态码、示例补全
- 字段策略：支持 field_policies 覆盖自动生成策略
- 数据持久化：支持保存/加载配置和数据

**响应 Mock 数据生成**：
```python
# 方式一：通过管理器统一生成
manager = APITestDataManager(openapi_document="api.json")
manager.configure_response_generator({
    "include_headers": True,
    "count": 2,
    "field_policies": [{"path": "price", "strategy": {"type": "fixed", "value": 99.9}}]
})
responses = manager.generate_response_for_endpoint("get_user", status_codes=["200", "404"])

# 方式二：独立使用响应生成器
from data_builder.openapi import ResponseDataGenerator, OpenAPIParser
parser = OpenAPIParser(openapi_document="api.json")
generator = ResponseDataGenerator(ref_resolver=parser, include_headers=True)
responses = generator.generate_for_endpoint(endpoint, status_codes=["200"])
```

数据生成优先级：字段策略 > 示例 > Schema 自动生成。

### Agent 使用方式（Skill）

dbsdk 提供了 AI Agent 技能定义，可用于 Claude、Cline 等 AI 编程助手自动生成测试数据脚本。

**Skill 名称**：`gen-data`

**输入方式**：
- 内联粘贴 JSON Schema
- 提供文件路径（Read 工具读取）
- 提供 URL（WebFetch 获取）

**输出模板**：
```python
import json
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, ...

schema = { ... }

config = BuilderConfig(
    policies=[
        FieldPolicy("field_path", strategy()),  # 策略选择理由
    ]
)

builder = DataBuilder(schema, config)
data = builder.build(count=N)
print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
```

**约束规则**：
1. 不使用 LLMStrategy，除非用户明确要求
2. 输出用 `json.dumps(data, ensure_ascii=False, indent=2, default=str)`
3. 为每个 FieldPolicy 添加行尾注释说明策略选择理由
4. 被 `ref()` 引用的字段必须排在引用者之前
5. 结构策略绑定到父级路径（如 `"items"` 而非 `"items[*].id"`）
6. 默认生成 `count=5`
7. 优先为 `required` 字段配置策略

## 核心概念

### FieldPolicy

绑定字段路径与生成策略，`path` 支持通配符：

| 路径写法 | 说明 |
| --- | --- |
| `"user.name"` | 精确路径 |
| `"user.*"` | user 下所有字段 |
| `"orders[*].id"` | 数组元素的 id 字段 |

### DataBuilder 配置

```python
builder = DataBuilder(schema)
builder.config(
    FieldPolicy("field1", strategy1),
    FieldPolicy("field2", strategy2),
)
# 或使用配置字典
builder.config_from_dict({
    "policies": [...],
    "combinations": [...],
    "post_filters": [...],
    "strict_mode": False,
    "null_probability": 0.0,
    "max_depth": None,
})
```

### DataBuilder 使用

```python
builder.build()          # 生成单个对象
builder.build(count=50)  # 生成 50 个对象的列表
```

### 联合类型（Union Type）

支持 JSON Schema 联合类型，可以配置类型优先级：

```python
from data_builder import DataBuilder, BuilderConfig

# 联合类型 schema
schema = {
    "type": ["string", "integer", "number"],
    "minLength": 5
}

# 配置优先级，优先选择 string 类型
builder = DataBuilder(
    schema,
    config=BuilderConfig(
        union_type_priority=["string", "integer", "number"]
    )
)
result = builder.build(count=5)  # 全部返回 string 类型
```

### nullable 关键字

支持 Draft 7+ 的 `nullable` 关键字和 Draft 4-6 的联合类型 null：

```python
# Draft 7+ 方式
schema1 = {
    "type": "string",
    "nullable": True
}

# Draft 4-6 方式（联合类型）
schema2 = {
    "type": ["string", "null"]
}

# 配置 null 概率
builder = DataBuilder(
    schema1,
    config=BuilderConfig(null_probability=0.2)  # 20% 概率生成 null
)
result = builder.build(count=10)
```

配置参数说明：
- `policies` - FieldPolicy 列表
- `strict_mode` - True 时无策略则抛异常
- `null_probability` - 生成 null 的概率 (0~1)
- `union_type_priority` - 联合类型优先级（如 `["string", "integer"]`），按配置顺序选择类型
- `combinations` - CombinationSpec 列表，支持分层组合
- `post_filters` - 后置过滤器列表
- `max_depth` - 递归深度限制，None 时循环引用抛异常，>=1 时启用递归生成

## 内置策略

| 工厂函数 | 说明 |
| --- | --- |
| `fixed(value)` | 固定值 |
| `random_string(length, charset)` | 随机字符串 |
| `range_int(min, max)` | 随机整数 |
| `range_float(min, max, precision)` | 随机浮点数 |
| `enum(choices, weights)` | 枚举随机选择，支持权重 |
| `regex(pattern)` | 按正则生成字符串 |
| `seq(start, step, prefix, suffix, padding)` | 自增序列 |
| `concat(strategies, separators)` | 级联合并多个策略的值 |
| `faker(method, locale, **kwargs)` | 调用 Faker 方法，默认 `zh_CN` |
| `ref(ref_path, transform)` | 引用其他字段的值 |
| `datetime(start, end, format, timezone, anchor, offset, date_range, time_range, specific_date, specific_time)` | 随机日期时间，支持 anchor/offset/date_range/time_range/specific_date/specific_time/timezone |
| `password(length, use_digits, use_uppercase, use_lowercase, use_special, special_chars)` | 密码生成，符合 Linux/Windows 密码策略，length 8-32 |
| `email(email_type, locale, domains)` | 邮箱生成，支持 qq/gmail/163/outlook/custom/safe/idn/random 类型，domains 可指定域名列表 |
| `ipv4(ip_class, ip_address_type, ip_subnet_mask, ip_multicast_groups)` | IPv4 地址生成，支持 A/B/C/D/E 类、私有地址、组播地址、指定网段等 |
| `ipv6(ip_class, ip_address_type, ip_scope)` | IPv6 地址生成，支持全局单播、链路本地、唯一本地、组播、回环地址等 |
| `domain(domain_type, tld_list, max_level)` | 域名生成，支持 IDN/Punycode、自定义 TLD、多级域名 |
| `url(protocol, host_type, path_type, query_type)` | URL/URI 生成，支持 scheme、host、port、path、query、fragment |
| `mac(oui, address_type, administration_type, broadcast_address)` | MAC 地址生成，支持 OUI、单播/组播、全局/本地管理位 |
| `cidr(ip_version, prefix_length, network_class)` | CIDR 表示法生成，支持 IPv4/IPv6 |
| `ip_range(ip_version, ip_class)` | IP 范围生成，支持 IPv4/IPv6 |
| `id_card(min_age, max_age, gender, region)` | 身份证号生成，支持年龄范围、性别、地区码配置 |
| `bank_card(bank, card_type)` | 银行卡号生成，支持15家主流银行BIN，自动Luhn校验 |
| `phone(carrier, number_type)` | 手机号生成，支持三大运营商和虚拟运营商号段 |
| `username(min_length, max_length, charset, reserved_words, allow_uppercase)` | 用户名生成，支持长度、字符集、保留字过滤 |
| `array_count(source)` | 控制数组元素数量 |
| `property_count(source)` | 控制对象属性数量 |
| `property_selection(properties)` | 控制对象生成哪些属性 |
| `contains_count(source)` | 控制数组 contains 元素数量 |
| `schema_selection(source)` | 控制 oneOf/anyOf 分支选择 |
| `llm(config, prompt, system_prompt, json_output)` | 调用 LLM 生成，`config` 为 `LLMConfig` 实例 |
| `callable_strategy(func)` | 自定义函数 `func(ctx) -> Any` |

## 组合生成

通过 `CombinationSpec` 在字段间生成组合覆盖的测试数据集，不配置时行为完全不变。

### 组合模式

| 模式 | 说明 |
| --- | --- |
| `RANDOM` | 默认，走原有随机生成逻辑 |
| `CARTESIAN` | 笛卡尔积，穷举所有组合 |
| `PAIRWISE` | 成对组合，覆盖所有二元组 |
| `ORTHOGONAL` | 正交数组，覆盖 t-元组（`strength` 控制 t） |
| `EQUIVALENCE` | 等价类代表值全组合 |
| `BOUNDARY` | 边界值全组合 |
| `INVALID` | 非法值轮流注入（每行只有一个字段取非法值，其余取正常值） |

### 基本用法

```python
from data_builder import DataBuilder

schema = {
    "type": "object",
    "properties": {
        "method":   {"type": "string"},
        "currency": {"type": "string"},
        "amount":   {"type": "integer"},
    },
}

# 笛卡尔积：3×2=6 条
config_dict = {
    "policies": [
        {"path": "method",   "strategy": {"type": "enum",   "values": ["alipay", "wechat", "card"]}},
        {"path": "currency", "strategy": {"type": "enum",   "values": ["CNY", "USD"]}},
        {"path": "amount",   "strategy": {"type": "fixed",  "value": 100}},
    ],
    "combinations": [
        {"mode": "CARTESIAN", "fields": ["method", "currency"]},
    ],
}
results = DataBuilder(schema).config_from_dict(config_dict).build()
```

### 非法值测试（INVALID 模式）

轮流非法：每行只有一个字段取非法值，其余字段取正常值（等价类中间值）。

```python
config_dict = {
    "policies": [
        {"path": "amount", "strategy": {"type": "range", "min": 0, "max": 100}},
        {"path": "name", "strategy": {"type": "faker", "method": "name"}},
    ],
    "combinations": [
        {"mode": "INVALID", "fields": ["amount", "name"]},
    ],
}
results = DataBuilder(schema).config_from_dict(config_dict).build()
# 每行只有 amount 或 name 是非法值
```

无策略字段在 BOUNDARY/EQUIVALENCE/INVALID 模式下会自动根据 schema 约束（minimum/maximum/minLength/maxLength 等）推导值域。

### 约束过滤

```python
{
    "mode": "CARTESIAN",
    "constraints": [
        {
            "predicate": "not (row['method'] == 'card' and row['currency'] == 'CNY')",
            "description": "card 不支持 CNY",
        },
    ],
}
```

### 分层组合（Scoped Combination）

通过多个 `CombinationSpec` 为不同层级的字段配置不同的组合模式：

```python
config_dict = {
    "policies": [
        {"path": "status",      "strategy": {"type": "enum", "values": ["active", "inactive"]}},
        {"path": "priority",    "strategy": {"type": "enum", "values": [1, 2, 3]}},
        {"path": "user.level",  "strategy": {"type": "enum", "values": ["vip", "normal"]}},
        {"path": "user.region", "strategy": {"type": "enum", "values": ["cn", "us"]}},
    ],
    "combinations": [
        {"mode": "PAIRWISE", "scope": None},
        {"mode": "CARTESIAN", "scope": "user"},
    ],
}
# 结果：顶层 PAIRWISE 组合 × 嵌套 CARTESIAN 组合
```

`scope` 参数：

- `None`：匹配顶层字段（不含 `.`）
- `"user"`：匹配 `user.*` 字段

不同 scope 的组合结果会进行笛卡尔积合并。

### 后置过滤器

```python
{
    "policies": [...],
    "combinations": [{"mode": "CARTESIAN"}],
    "post_filters": [
        {"type": "deduplicate", "fields": ["method"]},
        {"type": "constraint_filter", "predicate": "r['amount'] > 0"},
        {"type": "limit", "count": 10},
        {"type": "tag_rows", "field": "_tag", "value": "normal"},
    ],
}
```

### count 与组合的关系

```python
builder.build()         # 返回全部组合行
builder.build(count=3)  # 从组合结果中随机采样 3 条
builder.build(count=99) # 全集 + 随机补充至 99 条
```

## Schema format 关键字

未配置 `FieldPolicy` 时，`string` 类型字段的 `format` 关键字会自动生成对应格式的值：

| format | 示例输出 |
| --- | --- |
| `email` | `john@example.com` |
| `idn-email` | `user@中国.cn` |
| `uri` | `https://example.com/path` |
| `uuid` | `550e8400-e29b-41d4-a716-446655440000` |
| `date` | `2024-03-15` |
| `date-time` | `2024-03-15T10:30:00` |
| `time` | `14:30:00` |
| `ipv4` | `192.168.1.1` |
| `ipv6` | `2001:db8::1` |
| `hostname` | `example.com` |
| `idn-hostname` | `中国.cn` |
| `mac` | `00:1A:2B:3C:4D:5E` |
| `cidr` | `192.168.0.0/24` |
| `ip-range` | `192.168.1.1-192.168.1.254` |
| `duration` | `P3DT4H5M` |
| `uri-reference` | `/path/to/resource` |
| `json-pointer` | `/users/0` |
| `relative-json-pointer` | `1/0` |
| `regex` | `^[a-z]+$` |
| `iri` | `https://example.com/路径` |
| `iri-reference` | `/路径/资源` |

未识别的 format 值会 fallthrough 到默认随机字符串生成（符合 JSON Schema 规范）。

优先级：`FieldPolicy` > `enum`/`const`/`default` > `pattern` > `format` > 类型兜底

## Schema example / examples 关键字

当字段 schema 包含 `example` 或 `examples` 关键字，且未配置 `FieldPolicy` 时，自动使用 example 值生成数据。

优先级：`enum` > `const` > `default` > `examples`（随机选一个）> `example`（固定值）> 类型兜底

```python
schema = {
    "type": "object",
    "properties": {
        "code":  {"type": "string",  "example": "CN"},        # 固定返回 "CN"
        "level": {"type": "integer", "examples": [1, 2, 3]},  # 从列表随机选
        "name":  {"type": "string"},                           # 走类型兜底
    }
}
DataBuilder(schema).build(count=3)
```

> 显式 `FieldPolicy` 始终优先，会覆盖 `example`/`examples`。

## 示例：嵌套订单数据

```python
from data_builder import DataBuilder

schema = {
    "type": "object",
    "properties": {
        "id":       {"type": "integer"},
        "order_no": {"type": "string"},
        "user": {
            "type": "object",
            "properties": {
                "name":  {"type": "string"},
                "phone": {"type": "string"}
            }
        },
        "items": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "price":      {"type": "number"}
                }
            }
        },
        "status":     {"type": "string"},
        "created_at": {"type": "string"}
    }
}

orders = DataBuilder(schema).config_from_dict({
    "policies": [
        {"path": "id",                "strategy": {"type": "sequence", "start": 1001}},
        {"path": "order_no",          "strategy": {"type": "sequence", "start": 1, "prefix": "ORD-", "padding": 6}},
        {"path": "user.name",         "strategy": {"type": "faker",    "method": "name"}},
        {"path": "user.phone",        "strategy": {"type": "faker",    "method": "phone_number"}},
        {"path": "items[*].product_id", "strategy": {"type": "range",    "min": 1, "max": 100}},
        {"path": "items[*].price",    "strategy": {"type": "range",    "min": 10, "max": 500}},
        {"path": "status",            "strategy": {"type": "enum",     "values": ["pending", "paid", "shipped", "done"]}},
        {"path": "created_at",        "strategy": {"type": "datetime"}},
    ],
}).build(count=3)
```

## LLMStrategy

通过 OpenAI 兼容接口调用 LLM 生成字段值，需要额外安装 `openai` 包：

```bash
pip install openai
```

或使用可选依赖安装：

```bash
pip install dbsdk[llm]
```

```python
from data_builder import DataBuilder

llm_config = {
    "api_key": "your-api-key",
    "model": "gpt-4o-mini",
    "base_url": "https://api.openai.com/v1",  # 可替换为任意 OpenAI 兼容地址
}

DataBuilder(schema).config_from_dict({
    "policies": [
        {
            "path": "description",
            "strategy": {
                "type": "llm",
                "config": llm_config,
                "prompt": "为字段 {field_path} 生成一段真实的商品描述，字段 schema：{field_schema}",
            }
        },
        {
            "path": "tags",
            "strategy": {
                "type": "llm",
                "config": llm_config,
                "prompt": "为商品生成 3 个标签，返回 JSON 数组",
                "json_output": True,
            }
        },
    ],
}).build()
```

`LLMConfig` 参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `api_key` | 必填 | API 密钥 |
| `model` | 必填 | 模型名称 |
| `base_url` | `https://api.openai.com/v1` | API 地址 |
| `timeout` | `30` | 请求超时（秒） |
| `max_tokens` | `256` | 最大输出 token 数 |
| `temperature` | `0.7` | 生成温度 |
| `extra_headers` | `{}` | 附加请求头 |

`prompt` 模板占位符：`{field_path}`、`{field_schema}`、`{root_data_json}`、`{parent_data_json}`、`{index}`

自定义策略可通过 `ctx` 访问完整上下文：

```python
from data_builder import DataBuilder

def my_func(ctx):
    # ctx.field_path  - 当前字段路径
    # ctx.field_schema - 当前字段 schema
    # ctx.root_data   - 根数据对象（已生成部分）
    # ctx.parent_data - 父级数据对象
    # ctx.index       - 批量生成时的当前索引
    return f"custom-{ctx.index}"

DataBuilder(schema).config_from_dict({
    "policies": [
        {"path": "code", "strategy": {"type": "callable", "func": my_func}},
    ],
}).build()
```

## 相关文档

- [AGENTS.md](AGENTS.md) - 项目架构和约定
- [NEWBIE.md](NEWBIE.md) - 新手入门指南
- [CLAUDE.md](CLAUDE.md) - Claude AI 辅助开发指南
- [JSONSCHEMA.md](JSONSCHEMA.md) - JSON Schema 支持说明
- [OPENAPI.md](OPENAPI.md) - OpenAPI 测试数据生成文档
- [examples/](examples/) - 示例代码目录（包含新增的 OpenAPI 策略示例）
- [tests/](tests/) - 测试代码目录

