# Examples 示例文件分类指南

本文档将 `examples/` 目录下的示例文件按**作用范围**、**用法复杂度**和**应用场景**三个维度进行分类，帮助用户快速找到所需的示例。

---

## 目录结构

```
examples/
├── basic/                    # 基础值策略示例
│   ├── gen_enum.py          # 枚举策略
│   ├── gen_email.py         # 邮箱策略
│   ├── gen_password.py      # 密码策略
│   ├── gen_datetime.py      # 日期时间策略
│   ├── gen_regex.py         # 正则表达式策略
│   ├── gen_network.py       # 网络数据策略
│   ├── gen_id_card.py       # 身份证号策略
│   ├── gen_bank_card.py     # 银行卡号策略
│   ├── gen_phone.py         # 手机号策略
│   └── gen_username.py      # 用户名策略
│
├── advanced/                 # 高级值策略示例
│   ├── gen_concat.py        # 字段拼接策略
│   ├── gen_llm.py           # LLM 生成策略
│   └── gen_custom_strategy.py # 自定义策略
│
├── structure/                # 结构策略示例
│   ├── gen_structure.py     # 结构策略（property_count 等）
│   └── gen_post_filters.py  # 后置过滤器
│
├── schema_features/          # JSON Schema 特性示例
│   ├── gen_combination.py   # 组合生成模式
│   ├── gen_recursive.py     # 递归树结构
│   ├── gen_schema_combinators.py # allOf/anyOf/oneOf
│   ├── gen_prefix_items.py  # prefixItems（元组验证）
│   └── gen_union_type.py    # 联合类型和 nullable
│
├── integration/              # 综合场景示例
│   ├── gen_order.py         # 订单数据生成
│   ├── gen_boundary_test.py # 边界值测试
│   └── gen_error_handling.py # 错误处理
│
├── config/                   # 配置相关
│   ├── gen_from_config.py   # 从配置文件加载
│   └── policy.yaml          # YAML 配置示例
│
├── openapi/                  # OpenAPI 测试数据生成
│   ├── gen_openapi_request.py
│   ├── gen_openapi_response.py
│   ├── openapi_quickstart.py
│   ├── openapi_advanced.py
│   └── openapi_field_policies.py
│
├── run_all.py               # 总控脚本
└── README.md                # 本文档
```

---

## 一、按作用范围分类

### 🔹 基础值策略（basic/）

针对单个字段的基础数据生成策略。

文件 | 策略 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`basic/gen_enum.py` | enum | ⭐ | 从预定义列表随机选择，支持权重 |
`basic/gen_email.py` | email | ⭐ | 生成各类邮箱(qq/gmail/163/outlook等) |
`basic/gen_password.py` | password | ⭐ | 生成随机密码，支持自定义字符集 |
`basic/gen_datetime.py` | datetime | ⭐⭐ | 日期时间生成，支持锚点/偏移/时区 |
`basic/gen_regex.py` | regex | ⭐⭐ | 按正则表达式模式生成 |
`basic/gen_network.py` | ipv4/ipv6/domain/url/mac/cidr/ip_range | ⭐⭐ | 网络数据生成（IP地址、域名、URL、MAC地址等） |
`basic/gen_id_card.py` | id_card | ⭐ | 身份证号生成，支持年龄、性别、地区配置 |
`basic/gen_bank_card.py` | bank_card | ⭐ | 银行卡号生成，支持主流银行BIN，Luhn校验 |
`basic/gen_phone.py` | phone | ⭐ | 手机号生成，支持三大运营商和虚拟运营商 |
`basic/gen_username.py` | username | ⭐ | 用户名生成，支持长度、字符集、保留字过滤 |

### 🔹 高级值策略（advanced/）

高级字段值生成策略。

文件 | 策略 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`advanced/gen_concat.py` | concat | ⭐⭐ | 多策略值按顺序连接 |
`advanced/gen_llm.py` | llm | ⭐⭐⭐ | 调用大模型生成内容 |
`advanced/gen_custom_strategy.py` | 自定义策略 | ⭐⭐⭐ | 从 Strategy 基类继承创建自定义策略 |

### 🔹 结构策略（structure/）

控制数据结构和数组/对象的生成。

文件 | 策略 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`structure/gen_structure.py` | property_count / property_selection / schema_selection | ⭐⭐ | 控制对象属性数量/选择 |
`structure/gen_post_filters.py` | limit / deduplicate / constraint_filter / tag_rows | ⭐⭐ | 后置过滤/去重/条件过滤 |

### 🔹 JSON Schema 特性（schema_features/）

处理 JSON Schema 的高级特性。

文件 | 功能 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`schema_features/gen_combination.py` | cartesian / pairwise / boundary / equivalence | ⭐⭐⭐ | 多字段组合生成模式 |
`schema_features/gen_recursive.py` | 递归树结构 | ⭐⭐⭐ | 通过 max_depth 控制递归深度，生成组织架构/评论嵌套等 |
`schema_features/gen_schema_combinators.py` | allOf / anyOf / oneOf | ⭐⭐⭐ | 复杂 schema 组合处理 |
`schema_features/gen_prefix_items.py` | prefixItems | ⭐⭐ | 控制元组数组固定位置 |
`schema_features/gen_union_type.py` | 联合类型 (Union Type) 和 nullable | ⭐⭐ | 处理 type: [\"string\", \"integer\"] 和 nullable 关键字 |

### 🔹 综合场景（integration/）

完整业务场景的综合示例。

文件 | 功能 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`integration/gen_order.py` | 综合业务数据 | ⭐⭐⭐ | 完整订单数据结构生成 |
`integration/gen_boundary_test.py` | 边界值测试 | ⭐⭐⭐ | 边界值测试数据生成 |
`integration/gen_error_handling.py` | 错误处理 | ⭐⭐ | 异常捕获和错误处理示例 |

### 🔹 配置管理（config/）

配置文件加载和管理。

文件 | 功能 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`config/gen_from_config.py` | 配置文件加载 | ⭐⭐ | 从 YAML/JSON 文件加载策略 |
`config/policy.yaml` | 策略配置示例 | ⭐ | YAML 格式配置示例 |

### 🔹 OpenAPI 测试数据生成（openapi/）

基于 OpenAPI 文档的 API 测试数据生成。

文件 | 功能 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`openapi/gen_openapi_request.py` | 请求数据生成 | ⭐⭐ | 完整功能演示（端点筛选/多模式生成/持久化） |
`openapi/gen_openapi_response.py` | 响应数据 Mock | ⭐⭐ | 响应数据生成，支持字段策略优先和 schema 自动生成 |
`openapi/openapi_quickstart.py` | 快速入门 | ⭐ | 8 步快速上手指南 |
`openapi/openapi_advanced.py` | 高级用法 | ⭐⭐⭐ | 测试套件/自定义策略/批量测试/Mock响应/请求-响应对 |
`openapi/openapi_field_policies.py` | **新增**：策略示例 | ⭐⭐ | field_policies 策略使用示例（enum、range、random_string 等策略） |

### 🔹 系统级别

总控脚本。

文件 | 功能 | 复杂度 | 说明 |
------ | ------ | :------: | ------ |
`run_all.py` | 总控脚本 | ⭐ | 运行所有示例脚本 |

---

## 二、按用法复杂度分类

### ⭐ 入门级（基础用法）

适合初学者，了解基本API和使用方式。

- `basic/gen_enum.py` - 枚举选择
- `basic/gen_email.py` - 邮箱生成  
- `basic/gen_password.py` - 密码生成
- `basic/gen_id_card.py` - 身份证号生成
- `basic/gen_bank_card.py` - 银行卡号生成
- `basic/gen_phone.py` - 手机号生成
- `basic/gen_username.py` - 用户名生成
- `config/policy.yaml` - 策略配置示例

### ⭐⭐ 进阶级（组合与配置）

掌握后可处理大多数业务场景。

- `advanced/gen_concat.py` - 字符串连接组合
- `basic/gen_datetime.py` - 日期时间处理
- `basic/gen_regex.py` - 正则表达式生成
- `basic/gen_network.py` - 网络数据生成
- `structure/gen_structure.py` - 结构控制
- `schema_features/gen_prefix_items.py` - 元组数组
- `config/gen_from_config.py` - 配置加载
- `structure/gen_post_filters.py` - 后置过滤
- `integration/gen_order.py` - 订单数据生成

### ⭐⭐⭐ 高级（复杂场景）

处理复杂测试数据和边缘情况。

- `schema_features/gen_combination.py` - 多字段组合（笛卡尔积/成对组合/边界值/等价类）
- `advanced/gen_llm.py` - 大模型集成生成
- `advanced/gen_custom_strategy.py` - 自定义策略扩展
- `schema_features/gen_recursive.py` - 递归树结构
- `schema_features/gen_schema_combinators.py` - 复杂 schema 组合
- `schema_features/gen_union_type.py` - 联合类型和 nullable 处理
- `integration/gen_boundary_test.py` - 边界值测试

---

## 三、按应用场景分类

应用场景 | 推荐文件 |
---------- | ---------- |
**用户数据生成** | `basic/gen_enum.py`, `basic/gen_email.py`, `basic/gen_password.py`, `basic/gen_id_card.py`, `basic/gen_bank_card.py`, `basic/gen_phone.py`, `basic/gen_username.py`, `advanced/gen_concat.py` |
**时间相关数据** | `basic/gen_datetime.py` |
**网络数据生成** | `basic/gen_network.py` (IP地址、域名、URL、MAC地址等) |
**账户类数据生成** | `basic/gen_id_card.py`, `basic/gen_bank_card.py`, `basic/gen_phone.py`, `basic/gen_username.py` (身份证号、银行卡号、手机号、用户名) |
**业务订单数据** | `integration/gen_order.py` |
**测试用例生成** | `schema_features/gen_combination.py` (成对组合、边界值、等价类) |
**格式验证数据** | `basic/gen_regex.py` |
**数据过滤处理** | `structure/gen_post_filters.py` |
**复杂JSON结构** | `structure/gen_structure.py`, `schema_features/gen_prefix_items.py` |
**AI内容生成** | `advanced/gen_llm.py` |
**配置管理** | `config/gen_from_config.py`, `config/policy.yaml` |
**递归树结构** | `schema_features/gen_recursive.py` (组织架构、评论嵌套、菜单树) |
**自定义策略** | `advanced/gen_custom_strategy.py` |
**错误处理** | `integration/gen_error_handling.py` |
**联合类型处理** | `schema_features/gen_union_type.py` (处理 type: ["string", "integer"] 和 nullable 关键字) |
**API 测试数据生成** | `openapi/gen_openapi_request.py`, `openapi/gen_openapi_response.py`, `openapi/openapi_quickstart.py`, `openapi/openapi_advanced.py` |

---

## 四、推荐学习路径

```text
入门（basic/）→ 进阶（structure/）→ 高级（schema_features/）
       │               │                    │
       ▼               ▼                    ▼
     enum          structure          combination
     email         post_filters       recursive
     password                         schema_combinators
                                       union_type
       
       │               │                    │
       ▼               ▼                    ▼
   advanced/       config/            integration/
     concat        from_config           order
     llm                                 boundary_test
     custom
```

### 快速入门建议

1. **首先学习**：`basic/gen_enum.py` → 理解基本策略配置
2. **然后实践**：`basic/gen_email.py` 或 `basic/gen_password.py` → 掌握字段级策略
3. **进阶学习**：`advanced/gen_concat.py` → 学会策略组合
4. **深入理解**：`integration/gen_order.py` → 综合应用

---

## 五、运行所有示例

使用总控脚本 `run_all.py` 可以运行所有示例：

```bash
# 运行所有示例（默认不包含 gen_llm.py）
python run_all.py

# 运行所有示例（包含 gen_llm.py）
python run_all.py -a

# 不运行 openapi 子目录中的脚本
python run_all.py --no-openapi
```

---

## 文件清单

文件名 | 策略类型 | 作用范围 | 复杂度 |
-------- | ---------- | ---------- | :------: |
`basic/gen_enum.py` | enum | 字段级 | ⭐ |
`basic/gen_email.py` | email | 字段级 | ⭐ |
`basic/gen_password.py` | password | 字段级 | ⭐ |
`basic/gen_id_card.py` | id_card | 字段级 | ⭐ |
`basic/gen_bank_card.py` | bank_card | 字段级 | ⭐ |
`basic/gen_phone.py` | phone | 字段级 | ⭐ |
`basic/gen_username.py` | username | 字段级 | ⭐ |
`basic/gen_datetime.py` | datetime | 字段级 | ⭐⭐ |
`basic/gen_regex.py` | regex | 字段级 | ⭐⭐ |
`basic/gen_network.py` | ipv4/ipv6/domain/url/mac/cidr/ip_range | 字段级 | ⭐⭐ |
`advanced/gen_concat.py` | concat | 字段级 | ⭐⭐ |
`advanced/gen_llm.py` | llm | 字段级 | ⭐⭐⭐ |
`advanced/gen_custom_strategy.py` | 自定义策略 | 字段级 | ⭐⭐⭐ |
`structure/gen_structure.py` | property_count/selection | 结构级 | ⭐⭐ |
`structure/gen_post_filters.py` | limit/deduplicate/constraint/tag_rows | 结果级 | ⭐⭐ |
`schema_features/gen_combination.py` | cartesian/pairwise/boundary/equivalence | 字段组合 | ⭐⭐⭐ |
`schema_features/gen_recursive.py` | 递归树结构 | 高级结构 | ⭐⭐⭐ |
`schema_features/gen_schema_combinators.py` | allOf/anyOf/oneOf | 高级结构 | ⭐⭐⭐ |
`schema_features/gen_prefix_items.py` | prefixItems | 结构级 | ⭐⭐ |
`schema_features/gen_union_type.py` | 联合类型和 nullable | 高级结构 | ⭐⭐ |
`integration/gen_order.py` | 综合示例 | 系统级 | ⭐⭐⭐ |
`integration/gen_boundary_test.py` | 边界值测试 | 系统级 | ⭐⭐⭐ |
`integration/gen_error_handling.py` | 错误处理 | 系统级 | ⭐⭐ |
`config/gen_from_config.py` | 配置加载 | 系统级 | ⭐⭐ |
`config/policy.yaml` | 配置示例 | 系统级 | ⭐ |
`run_all.py` | 总控脚本 | 系统级 | ⭐ |
`openapi/gen_openapi_request.py` | 请求数据生成 | OpenAPI 级 | ⭐⭐ |
`openapi/gen_openapi_response.py` | 响应数据 Mock | OpenAPI 级 | ⭐⭐ |
`openapi/openapi_quickstart.py` | 快速入门 | OpenAPI 级 | ⭐ |
`openapi/openapi_advanced.py` | 高级用法 | OpenAPI 级 | ⭐⭐⭐ |
`openapi/openapi_field_policies.py` | field_policies 策略示例 | OpenAPI 级 | ⭐⭐ |
