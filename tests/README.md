# tests/

## 目录结构

```text
tests/
├── conftest.py               # 全局 fixtures
├── core/                     # 核心模块测试
│   ├── test_builder.py       # DataBuilder 测试（21个测试）
│   ├── test_combination_builder.py  # CombinationBuilder 测试（24个测试）
│   ├── test_combinations.py  # 数据类测试（20个测试）
│   ├── test_generators.py    # SchemaResolver/ValueGenerator 测试（56个测试）
│   ├── test_manager.py       # APITestDataManager 测试（41个测试）
│   ├── test_models.py        # OpenAPI 数据模型测试（9个测试）
│   └── test_parser.py        # OpenAPIParser 测试（22个测试）
├── primitive/                # 基本类型默认生成
│   ├── test_primitive_types.py
│   └── test_example_keyword.py
├── strategies/               # 策略单元测试
│   ├── test_strategies.py
│   ├── test_concat_strategy.py
│   ├── test_strategy_values.py
│   ├── test_invalid_values.py
│   ├── test_schema_aware_strategy.py
│   ├── test_array_count_strategy.py
│   ├── test_structure_strategies.py
│   ├── test_llm_strategy.py
│   ├── test_registry.py
│   ├── test_edge_cases.py
│   ├── test_match_path.py
│   ├── test_password_strategy.py
│   ├── test_llm_render_prompt.py
│   ├── test_enum_strategy.py
│   ├── test_id_card.py       # 身份证号策略测试（12个测试）
│   ├── test_bank_card.py     # 银行卡号策略测试（9个测试）
│   ├── test_phone.py         # 手机号策略测试（9个测试）
│   ├── test_username.py      # 用户名策略测试（25个测试）
│   ├── test_token_strategy.py # 认证令牌策略测试（33个测试）
│   └── test_metric_strategy.py # 系统监控指标策略测试（80个测试）
├── composite/                # 复合结构测试
│   ├── test_composite_types.py
│   ├── test_array_count_integration.py
│   ├── test_structure_integration.py
│   ├── test_structure_advanced.py
│   ├── test_schema_keywords.py
│   ├── test_schema_logic.py
│   └── test_recursive_structure.py
├── bulk/                     # 批量生成测试
│   ├── test_bulk.py
│   └── test_builder_config_count.py
├── combination/              # 组合生成测试
│   ├── test_combination_engine.py
│   ├── test_combination_integration.py
│   ├── test_filters.py
│   ├── test_tag_rows.py
│   ├── test_post_filters.py
│   ├── test_invalid_combination.py
│   ├── test_nested_combination.py
│   ├── test_scoped_combination.py
│   └── test_filter_edge_cases.py
├── config_loader/            # 配置加载测试
│   ├── __init__.py
│   ├── test_config_from_dict.py
│   ├── test_config_from_file.py
│   ├── test_env_vars.py
│   ├── test_param_aliases.py
│   └── test_combinations_and_filters.py
├── openapi/                  # OpenAPI 模块测试
│   ├── test_converter.py     # Schema 转换器测试
│   ├── test_integration.py   # 集成功能测试（40+个测试）
│   ├── test_response_generator.py  # 响应生成器测试
│   └── test_exceptions.py    # 异常处理测试
└── utils/                    # 工具模块测试
    └── test_invalid_data.py  # InvalidDataGenerator 测试（14个测试）
```

---

## conftest.py

全局 pytest fixtures，提供三个常用 schema 供多个测试模块复用：

| Fixture | 说明 |
| --- | --- |
| `simple_string_schema` | 含 `name: string` 的单字段对象 |
| `simple_int_schema` | 含 `age: integer [0, 100]` 的单字段对象 |
| `nested_order_schema` | 含 `user` 对象和 `orders` 数组（2-5 项）的嵌套结构 |

---

## core/

核心模块单元测试，包含 data_builder 核心类和 OpenAPI 核心组件的测试。

### test_builder.py

`DataBuilder` 核心类测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestDataBuilderInit` | 初始化（仅 schema、schema+config、config_from_dict） |
| `TestDataBuilderBuild` | build() 方法（单个对象、多个对象、count 覆盖、字段策略、组合模式） |
| `TestFindStrategy` | _find_strategy() 方法（精确匹配、user.*、*.field、[*] 通配符、无匹配） |
| `TestMatchPath` | _match_path() 方法（各种通配符模式） |
| `TestDataBuilderEdgeCases` | 边界情况（空 schema、嵌套对象、数组、后置过滤器） |

**测试数量**：21 个

### test_combination_builder.py

`CombinationBuilder` 组合构建器测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestCombinationBuilderInit` | 初始化 |
| `TestCombinationBuilderBuild` | build() 方法（笛卡尔积、成对组合、count 限制/扩展、无组合配置） |
| `TestGroupFieldsByScope` | _group_fields_by_scope() 方法（显式字段、scope 分组） |
| `TestMatchScope` | _match_scope() 方法（顶层字段、嵌套 scope） |
| `TestCollectDomains` | _collect_domains() 方法（枚举策略、边界值） |
| `TestCartesianMergeGroups` | _cartesian_merge_groups() 方法（单组、多组、空组） |
| `TestDiscoverSchemaFields` | _discover_schema_fields() 方法（顶层字段、嵌套字段） |
| `TestResolveFieldSchema` | _resolve_field_schema() 方法（顶层、嵌套、不存在字段） |

**测试数量**：24 个

### test_combinations.py

数据类测试（CombinationMode、Constraint、CombinationSpec）。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestCombinationMode` | 枚举值、枚举数量、从字符串创建 |
| `TestConstraint` | 创建约束、默认描述、谓词执行 |
| `TestCombinationSpec` | 默认值、指定模式/字段/scope/约束/强度/正常值、完整配置 |
| `TestCombinationSpecUsage` | 实际使用场景（成对组合、正交组合、非法值模式、约束过滤） |
| `TestCombinationSpecEdgeCases` | 边界情况（空列表、None 值、大量字段/约束、嵌套 scope） |

**测试数量**：20 个

### test_generators.py

`SchemaResolver` 和 `ValueGenerator` 测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestSchemaResolverInit` | 初始化 |
| `TestSchemaResolverResolve` | resolve() 方法（简单 schema、$ref、allOf、if/then/else、not、循环引用） |
| `TestSchemaResolverResolveRef` | _resolve_ref() 方法（definitions、components/schemas、无效格式、不存在路径） |
| `TestSchemaResolverMergeSchemas` | _merge_schemas() 方法（properties、required、其他字段覆盖） |
| `TestValueGeneratorInit` | 初始化 |
| `TestValueGeneratorGenerateValue` | generate_value() 方法（简单对象、深度限制） |
| `TestValueGeneratorGenerateObject` | _generate_object() 方法（必需字段、example、min/maxProperties、additionalProperties、patternProperties） |
| `TestValueGeneratorGenerateArray` | _generate_array() 方法（简单数组、min/maxItems、uniqueItems、prefixItems、contains） |
| `TestValueGeneratorGeneratePrimitive` | _generate_primitive() 方法（enum、const、default、examples、example、pattern、范围、倍数、布尔、null） |
| `TestValueGeneratorValidateExample` | _validate_example() 方法（类型验证、enum、const、范围、字符串长度） |
| `TestValueGeneratorCheckType` | _check_type() 方法（null、boolean、integer、number、string、array、object） |
| `TestValueGeneratorMakeHashable` | _make_hashable() 方法（基本类型、字典、列表、嵌套结构） |

**测试数量**：56 个

### test_manager.py

`APITestDataManager` API 测试数据管理器测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestAPITestDataManagerInit` | 初始化（从文件、从字典、无效输入） |
| `TestAPITestDataManagerConfig` | 配置方法（configure_generator、configure_response_generator） |
| `TestAPITestDataManagerEndpoints` | 端点查询（全部、按标签、按 operationId、按 path+method） |
| `TestAPITestDataManagerGenerateRequests` | 请求数据生成（单端点、按 path+method、按标签、全部） |
| `TestAPITestDataManagerGenerateResponses` | 响应数据生成（单端点、按 path+method、按标签、全部） |
| `TestAPITestDataManagerStorage` | 数据存储和检索 |
| `TestAPITestDataManagerSaveLoad` | 保存和加载配置 |
| `TestAPITestDataManagerSummary` | 摘要信息 |

**测试数量**：41 个

### test_models.py

OpenAPI 数据模型测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestOpenAPIParameter` | 创建参数、字符串位置转换为枚举、to_dict 转换 |
| `TestOpenAPIRequestBody` | 创建请求体、获取 schema、获取 example |
| `TestOpenAPIEndpoint` | 创建端点、按位置获取参数、获取必需参数、to_dict 转换 |
| `TestGeneratedRequest` | 创建请求、构建 URL、to_dict 转换、resolved_path 实例化 |

**测试数量**：9 个

### test_parser.py

`OpenAPIParser` 解析器测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestOpenAPIParserInit` | 初始化和文档加载 |
| `TestOpenAPIParserParse` | 文档解析（端点、参数、请求体、响应） |
| `TestOpenAPIParserRef` | $ref 引用解析（包括循环引用） |
| `TestOpenAPIParserHelpers` | 辅助方法 |
| `TestOpenAPIParserEdgeCases` | 边界情况 |

**测试数量**：22 个

**core/ 目录总测试数**：193 个

---

## primitive/

### test_primitive_types.py

无策略时，schema 类型驱动的默认值生成逻辑。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestStringType` | 默认随机字符串、`minLength/maxLength`、`format`（email/uri/uuid/date/date-time/time/ipv4/ipv6/hostname） |
| `TestIntegerType` | 默认范围、`minimum/maximum`、`exclusiveMinimum/exclusiveMaximum` |
| `TestNumberType` | 浮点数生成、边界相等时的固定值 |
| `TestBooleanType` | 随机布尔值的两值覆盖 |
| `TestNullType` | 返回 `None` |
| `TestPatternKeyword` | `pattern` 正则生成、pattern 优先于 format、pattern 忽略 minLength/maxLength |
| `TestSchemaConstraints` | `enum`、`const`、`default` 关键字优先级 |
| `TestMultipleOf` | 整数 `multipleOf`（含偏移范围）、浮点数 `multipleOf`（0.5 步长、整数步长） |

### test_example_keyword.py

JSON Schema `example` / `examples` 关键字支持，及与其他关键字的优先级。

**优先级顺序**：`enum` > `const` > `default` > `examples`（随机选一个）> `example`（固定值）> 类型兜底

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestExampleKeyword` | `example` 单值（string/integer/number/boolean/null）、`examples` 随机选取、空列表/非列表兜底、完整优先级链验证、`FieldPolicy` 覆盖 example、混合字段场景 |

---

## strategies/

### test_strategies.py

各内置策略的 `generate()` 方法功能测试。

| 测试类 | 策略 | 覆盖场景 |
| --- | --- | --- |
| `TestFixedStrategy` | `FixedStrategy` | int/str/dict/list/None 固定值 |
| `TestRandomStringStrategy` | `RandomStringStrategy` | 默认长度、自定义长度、自定义字符集 |
| `TestRangeStrategy` | `RangeStrategy` | 整数/浮点范围、精度、min=max |
| `TestEnumStrategy` | `EnumStrategy` | 无权重均匀分布、权重偏差 |
| `TestRegexStrategy` | `RegexStrategy` | 数字模式、大写字母模式 |
| `TestSequenceStrategy` | `SequenceStrategy` | 递增步长、前缀、后缀、补零、重置 |
| `TestFakerStrategy` | `FakerStrategy` | 中文姓名、电话号码、邮箱（zh_CN） |
| `TestCallableStrategy` | `CallableStrategy` | 访问 `ctx.field_path`、`ctx.index` 计算 |
| `TestRefStrategy` | `RefStrategy` | 同级字段引用、转换函数 |
| `TestDateTimeStrategy` | `DateTimeStrategy` | 默认格式、自定义格式、时间范围约束 |

### test_strategy_values.py

策略值域方法接口：`values()`、`boundary_values()`、`equivalence_classes()`。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestFixedValues` | `FixedStrategy` 三个接口均返回包含固定值的列表 |
| `TestEnumValues` | 返回全部选项、副本隔离、首尾边界值、空列表处理、等价类 |
| `TestRangeIntValues` | 小范围枚举（≤1000）、大范围返回 None、边界值（min/min+1/max-1/max）、等价类（低/中/高） |
| `TestRangeFloatValues` | `values()` 返回 None、边界值（含 min+ε/max-ε 增强）、等价类 |
| `TestUnsupportedValues` | `RandomStringStrategy` 三个接口非 None（已补全）、`FakerStrategy` 三个接口均返回 None |

### test_invalid_values.py

各策略 `invalid_values()` 接口及增强的 `boundary_values()`/`equivalence_classes()` 测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestRangeInvalidValues` | 整数/浮点非法值、不同 precision、min=max 边界 |
| `TestRangeFloatBoundaryEnhanced` | 浮点边界值增强（precision=1/2/3、min=max、极小范围） |
| `TestRandomStringBoundary` | 边界值（normal/length=0/length=1） |
| `TestRandomStringEquivalence` | 等价类（字母+数字/纯数字/纯字母/特殊字符集） |
| `TestRandomStringInvalid` | 非法值（空串、超长串、类型错误、None） |
| `TestDateTimeBoundary` | 边界值（正常范围、start=end、1 秒范围） |
| `TestDateTimeEquivalence` | 等价类（start/mid/end 三类） |
| `TestDateTimeInvalid` | 非法值（范围外日期、非日期字符串、类型错误、None） |
| `TestEnumInvalidValues` | 字符串/数值/混合 choices 的非法值生成 |
| `TestFixedInvalidValues` | 各类型固定值的类型不匹配非法值 |
| `TestUnsupportedInvalid` | FakerStrategy 返回 None |

### test_schema_aware_strategy.py

`SchemaAwareStrategy` 根据 schema 约束自动推导值域的测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestSchemaAwareGenerate` | `generate()` 抛 NotImplementedError |
| `TestSchemaAwareInteger` | boundary/equivalence/invalid、小范围/单值/默认范围 |
| `TestSchemaAwareNumber` | 浮点 boundary/equivalence/invalid |
| `TestSchemaAwareString` | minLength=0/正值的 boundary/equivalence/invalid |
| `TestSchemaAwareBoolean` | boundary/equivalence/invalid |
| `TestSchemaAwareUnsupported` | array/object 类型返回 None |

### test_array_count_strategy.py

`ArrayCountStrategy`（`StructureStrategy` 子类）的行为测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestStructureStrategyHierarchy` | 继承链：`ArrayCountStrategy` → `StructureStrategy` → `Strategy` |
| `TestArrayCountStrategy` | 整数/策略/零/负数截断/浮点截断/范围/callable 作为 source |
| `TestArrayCountFactory` | `array_count()` 工厂函数 |

### test_structure_strategies.py

`PropertyCountStrategy`、`PropertySelectionStrategy`、`ContainsCountStrategy`、`SchemaSelectionStrategy` 的单元测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestPropertyCountStrategyHierarchy` | 继承链验证 |
| `TestPropertyCountStrategy` | 整数/策略/零/负数截断/浮点截断/范围/callable 作为 source |
| `TestPropertyCountFactory` | `property_count()` 工厂函数 |
| `TestPropertySelectionStrategyHierarchy` | 继承链验证 |
| `TestPropertySelectionStrategy` | 列表/策略/空列表 |
| `TestPropertySelectionFactory` | `property_selection()` 工厂函数 |
| `TestContainsCountStrategyHierarchy` | 继承链验证 |
| `TestContainsCountStrategy` | 整数/策略/零/负数截断/浮点截断 |
| `TestContainsCountFactory` | `contains_count()` 工厂函数 |
| `TestSchemaSelectionStrategyHierarchy` | 继承链验证 |
| `TestSchemaSelectionStrategy` | 整数/策略/负数索引 |
| `TestSchemaSelectionFactory` | `schema_selection()` 工厂函数 |

### test_llm_strategy.py

`LLMStrategy` 测试，通过 mock 隔离 OpenAI 调用。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestLLMConfig` | 默认参数值、自定义参数 |
| `TestLLMStrategy` | 纯文本生成、prompt 模板占位符渲染、JSON 输出解析（含 markdown fence）、system_prompt 透传、LLMConfig 参数传递、openai 未安装时抛 ImportError、工厂函数、批量生成时 index 递增、parent_data 上下文序列化 |

### test_registry.py

`StrategyRegistry` 的 `register/get/has/reset` 方法及内置策略注册完整性。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestRegistryRegister` | 注册并获取、覆盖注册 |
| `TestRegistryGet` | 获取内置策略、未知策略抛 `StrategyNotFoundError` |
| `TestRegistryHas` | 内置策略存在、未知策略不存在、注册后存在 |
| `TestRegistryBuiltins` | 参数化验证 16 个内置策略（含结构策略）均已注册 |
| `TestRegistryReset` | `reset()` 清除自定义策略、保留内置策略、autouse fixture 实现测试间隔离 |

### test_edge_cases.py

异常路径：`RefStrategy` 引用不存在路径、`EnumStrategy` 空列表、`DateTimeStrategy` start > end。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestRefStrategyPathErrors` | 顶层 key 缺失、嵌套 key 缺失、数组索引越界、遍历非 dict、空 root_data，均抛 `FieldPathError` |
| `TestEnumStrategyEmpty` | `generate()` 抛 `StrategyError`、构造时不报错、`boundary_values()` 返回 None |
| `TestDateTimeStrategyInvalid` | start > end 抛 `StrategyError`、start == end 正常生成 |

### test_match_path.py

`_match_path` 的 `fnmatch` 通用通配符分支（第三条分支）。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestFnmatchFallback` | `?` 单字符、`*` 任意串、`[seq]` 字符集、`[!seq]` 取反、精确匹配 |
| `TestFnmatchIntegration` | `?` 通配符通过 FieldPolicy 实际生效、`*` 前缀匹配多字段 |

### test_llm_render_prompt.py

`LLMStrategy._render_prompt` 占位符缺失及边界行为。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestRenderPromptMissingPlaceholder` | 不存在的占位符抛 `KeyError`、合法占位符正常渲染、`{root_data[key]}` dict 访问、dict 中不存在 key 抛 `KeyError`、`{{literal}}` 转义保持原样 |

### test_metric_strategy.py

`MetricStrategy` 系统监控指标策略测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestMetricStrategyInit` | 初始化（默认参数、有效指标类型、有效数据模式、有效单位、无效参数校验） |
| `TestMetricStrategyGenerate` | 数据生成（内存/交换分区/磁盘/CPU 单点和趋势、自定义范围、不同单位） |
| `TestMetricStrategyBoundaryValues` | 边界值生成（容量指标边界、速率指标边界） |
| `TestMetricStrategyEquivalenceClasses` | 等价类生成（容量指标等价类、速率指标等价类） |
| `TestMetricStrategyInvalidValues` | 非法值生成（容量指标非法值、速率指标非法值） |
| `TestMetricStrategyTimestamps` | 时间戳生成（时间顺序、时间间隔） |
| `TestMetricStrategyValues` | values() 方法返回 None |
| `TestMetricStrategyRegistry` | 策略注册和工厂函数 |
| `TestMetricStrategyTrendInit` | 趋势模式初始化（默认模式、有效趋势模式、有效趋势字段、无效参数校验） |
| `TestMetricStrategyTrendModes` | 趋势模式生成（increase/decrease/stable/increase_decrease/decrease_increase、自定义范围、CPU 趋势） |
| `TestMetricStrategyOutputFields` | 输出字段控制（默认字段、选择性输出、时间戳控制、单字段输出、参数验证、free 字段计算、趋势模式字段过滤） |

**测试数量**：80 个

---

## composite/

### test_composite_types.py

嵌套对象、数组结构、通配符路径、跨字段引用的集成测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestNestedObjects` | 单层嵌套、多层嵌套（`a.b.c`） |
| `TestArrayTypes` | 字符串/整数/对象数组、`minItems/maxItems` 约束 |
| `TestMixedStructure` | 嵌套对象内含数组（使用 `nested_order_schema` fixture） |
| `TestWildcardPaths` | `user.*` 通配符、`orders[*].id` 数组元素通配符 |
| `TestRefCrossLevel` | 同级字段引用（`owner_id = user_id`）、引用+转换（折扣价） |
| `TestUniqueItems` | `uniqueItems: true` 整数/字符串去重、`uniqueItems: false` 不影响生成 |
| `TestUnionType` | 联合 type `["string", "null"]` 生成、`["integer", "string"]` 多类型、`["null"]` 只返回 None |
| `TestAdditionalProperties` | 无 properties 时根据 additionalProperties schema 生成属性、有 properties 时不额外生成、布尔值忽略 |

### test_array_count_integration.py

`ArrayCountStrategy` 与 `DataBuilder` 的集成行为，及 `StructureStrategy` 的路由逻辑。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestArrayCountIntegration` | `array_count` 覆盖 schema min/max、生成空数组、范围控制、callable 按 index 变化、无 `array_count` 时使用 schema 约束 |
| `TestStructureStrategyRouting` | `StructureStrategy` 绑定数组/对象/基础类型的路由行为、值策略绑定数组、通配符路径 |

### test_structure_integration.py

`prefixItems`、`PropertyCountStrategy`、`PropertySelectionStrategy`、`ContainsCountStrategy`、`SchemaSelectionStrategy` 与 `DataBuilder` 的集成测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestPrefixItems` | 基本 prefixItems、附加 items 填充、`items: false` 限制长度、minItems 默认值、无 prefixItems 不变 |
| `TestPropertyCountIntegration` | 固定数量、required 保底、超出 additionalProperties 补充、范围控制、全属性、无策略默认 |
| `TestPropertySelectionIntegration` | 子集选择、单属性、空列表、additionalProperties 补充、未定义属性跳过、callable 动态选择 |
| `TestContainsCountIntegration` | 固定 contains 数量、零、等于总数、无 contains schema 回退 |
| `TestSchemaSelectionIntegration` | oneOf 第一/二分支、anyOf 分支、越界 clamp、负数 clamp、无分支 fallthrough、callable 动态选择 |
| `TestStrategyCoexistence` | PropertyCount+ArrayCount 共存、SchemaSelection+PropertySelection 共存、ContainsCount+prefixItems 独立 |

### test_structure_advanced.py

StructureStrategy 高级场景：策略组合、依赖、边界、错误绑定。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestPropertyCountWithChildPolicy` | PropertyCountStrategy + 子字段 FieldPolicy 共存：数量控制 + 值策略同时生效 |
| `TestPrefixItemsWithArrayCount` | prefixItems + ArrayCountStrategy 组合：扩展/缩减/items:false 限制 |
| `TestPropertySelectionWithRequired` | PropertySelectionStrategy 不自动合并 required（by design）、包含 required 时正常 |
| `TestContainsVsArrayCountConflict` | 同字段绑定两个策略时后者覆盖前者 |
| `TestSchemaSelectionWithNestedPolicy` | SchemaSelectionStrategy 选择分支后嵌套 FieldPolicy 生效、动态分支 + 子字段策略 |
| `TestStructureWithCombination` | PropertyCount + CARTESIAN、ArrayCount + 组合、SchemaSelection + BOUNDARY |
| `TestStructureWithStrictMode` | strict_mode 下子字段无策略抛异常、全策略正常通过 |
| `TestStructureWithNullProbability` | null_probability + nullable 子字段返回 None |
| `TestRefWithStructure` | RefStrategy 引用结构策略控制的字段 |
| `TestSeqContinuityWithStructure` | seq 在 array_count 控制的数组内保持连续递增 |
| `TestPrefixItemsWithUniqueItems` | prefixItems + uniqueItems 组合去重 |
| `TestFieldPolicyOnPrefixItemsPositions` | FieldPolicy 通过 `[*]` 通配符控制 prefixItems 各位置元素 |
| `TestBulkWithStructureStrategy` | 批量生成（100-500 条）PropertyCount/SchemaSelection/ContainsCount/prefixItems 稳定性 |
| `TestWrongTypeBinding` | 错误绑定类型时 fall through：array_count→string、property_count→array、contains_count→object |

| `TestWrongTypeBinding` | 错误绑定类型时 fall through：array_count→string、property_count→array、contains_count→object |

### test_schema_keywords.py

JSON Schema 关键字测试：`additionalProperties` / `minProperties` / `maxProperties` / `dependentRequired` / `format` / `if-then-else` / `patternProperties` / `dependentSchemas` / `not` / `propertyNames`。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestAdditionalPropertiesFalse` | 过滤额外属性、additionalProperties=true/对象 schema |
| `TestMinMaxProperties` | minProperties 生成、maxProperties 截断 |
| `TestMinMaxContains` | minContains/maxContains 控制包含匹配元素数量 |
| `TestDependentRequired` | 依赖字段生成（dependentRequired） |
| `TestFormatExtensions` | email/uuid/uri/date-time/hostname 等格式扩展 |
| `TestIfThenElse` | if-then-else 条件分支选择 |
| `TestPatternProperties` | 正则匹配属性生成 |
| `TestDependentSchemas` | 依赖 schema 条件生成（dependentSchemas） |
| `TestNotKeyword` | not 排除类型 |
| `TestPropertyNames` | propertyNames 验证生成键名 |

### test_schema_logic.py

JSON Schema 逻辑关键字测试：`$ref` / `definitions` / `$defs` / `allOf` / `anyOf` / `oneOf`。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestRef` | $ref + definitions/$defs 解析、嵌套引用、循环引用检测、非法路径/外部引用、ref+field_policy、ref+兄弟关键字 |
| `TestAllOf` | allOf 合并 properties/required、ref+allOf、base properties 保留 |
| `TestOneOf` | oneOf 基本选择、原始类型多态、oneOf+ref、覆盖度验证 |
| `TestAnyOf` | anyOf 基本选择、对象多态、覆盖度验证 |
| `TestIntegration` | 完整 schema 综合、ref 在数组 items 中、allOf 在根节点、bulk+ref |

### test_recursive_structure.py

递归树结构生成测试：支持 `max_depth` 参数控制递归深度。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestMaxDepthParameter` | max_depth 配置参数解析、dict 配置方式 |
| `TestRecursiveSchema1` | 标准树结构（$defs 定义的递归节点）、多级子节点生成 |
| `TestRecursiveSchema2` | 根节点直接使用 $ref 的递归结构 |
| `TestDefaultBehavior` | max_depth=None 时循环引用抛出 SchemaError |
| `TestDepthCutoff` | 深度达到 max_depth 时返回默认值（空对象/空数组/null） |
| `TestMultipleGeneration` | 多次生成一致性、相同种子稳定性 |
| `TestEdgeCases` | max_depth=0/max_depth=1、嵌套数组+对象混合、字段策略在递归节点 |

---

## bulk/

### test_bulk.py

高数量生成（count=1000）的稳定性与正确性验证。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestBulkCount` | 返回数量正确、所有项均为字典 |
| `TestBulkSeqStrategy` | 1000 条序列 ID 连续无重复 |
| `TestBulkEnumCoverage` | 1000 条生成后覆盖所有枚举选项 |
| `TestBulkNested` | 嵌套 schema 1000 条无异常、复杂多层嵌套+数组 1000 条完成 |

### test_builder_config_count.py

`BuilderConfig(count=N)` 参数行为。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestBuilderConfigCount` | config count 返回列表、count=0 返回空列表、显式 count 覆盖 config count、无 count 返回单字典、config count=None 时显式 count 有效、config count + policies |

---

## combination/

### test_combination_engine.py

`CombinationEngine` 各模式的算法正确性（不依赖 `DataBuilder`）。

| 测试类 | 模式 | 覆盖场景 |
| --- | --- | --- |
| `TestCartesian` | CARTESIAN | 2×2=4、单字段、3 字段 2³=8、空域 |
| `TestPairwise` | PAIRWISE | 所有二元对覆盖且行数 < 全组合、两字段等价于笛卡尔积、单字段 |
| `TestOrthogonal` | ORTHOGONAL | strength=3 覆盖所有三元组、strength > 字段数退化为全组合 |
| `TestConstraints` | — | 单约束过滤、多约束组合、全部过滤返回空 |
| `TestEquivalenceAndBoundary` | EQUIVALENCE / BOUNDARY | 两种模式本质均为笛卡尔积 |

### test_combination_integration.py

组合模式与 `DataBuilder.build()` 的端到端集成测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestNoCombination` | 无组合时单对象/列表/RANDOM 模式行为 |
| `TestCartesianIntegration` | 基本笛卡尔积、`fields=None` 自动选取、不可枚举字段排除 |
| `TestPairwiseIntegration` | 所有对覆盖、行数约减 |
| `TestBoundaryIntegration` | 边界值提取后笛卡尔积 |
| `TestEquivalenceIntegration` | 等价类代表值后笛卡尔积 |
| `TestCombinationCount` | count < 全集采样、count > 全集补充、count=None 返回全集 |
| `TestConstraintIntegration` | 约束过滤行数 |
| `TestPostFilters` | `limit`/`constraint_filter`/`deduplicate` 单独及链式，非组合模式也支持后置过滤 |
| `TestNestedCombination` | 嵌套字段路径 `"user.level"` 参与组合 |
| `TestFallback` | 无可枚举字段时退化为普通生成 |

### test_filters.py

`deduplicate`、`constraint_filter`、`limit` 三个后置过滤器的单元测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestDeduplicate` | 单字段去重、多字段联合去重、空输入、无重复直接返回 |
| `TestConstraintFilter` | 条件过滤、全通过、全过滤 |
| `TestLimit` | 截断、限制大于长度返回全部、限制为 0 |

### test_tag_rows.py

`tag_rows` 后置过滤器的单元测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestTagRows` | 基本标记、默认参数、空输入、自定义字段名、覆盖已有字段、原地修改 |

### test_post_filters.py

`post_filters` 在 `DataBuilder` 中的集成测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestPostFiltersIntegration` | limit/deduplicate/constraint_filter/tag_rows 在 DataBuilder 中的集成 |
| `TestPostFiltersConfigParsing` | post_filters 配置解析 |
| `TestPostFiltersEdgeCases` | limit(0)、过滤器移除所有结果、单结果等边界情况 |

### test_invalid_combination.py

`INVALID` 组合模式及 `SchemaAwareStrategy` 无策略字段回退的测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestOneInvalidAtATime` | 引擎层：轮流非法算法（基本/单字段/空域/约束过滤/无 normal_values） |
| `TestInvalidIntegration` | DataBuilder 集成：有策略字段非法值、轮流非法验证、自定义 normal_values、count 控制 |
| `TestInvalidSchemaAwareFallback` | 无策略字段通过 schema 推导非法值、有策略+无策略混合 |
| `TestAutoDiscoverSchemaFields` | BOUNDARY/EQUIVALENCE/INVALID 自动发现 schema 基本类型字段、CARTESIAN 不自动发现 |

### test_nested_combination.py

嵌套字段参与组合生成的各类场景。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestMultiLevelNesting` | 3 层路径 `config.db.host` × `config.db.port` = 4 行 |
| `TestSameObjectMultiFields` | 同嵌套对象两字段 `user.level` × `user.region` = 4 行，非组合字段仍生成 |
| `TestCrossLevelCombination` | 顶层 `status` × 嵌套 `user.level` = 4 行 |
| `TestNestedWithArray` | 嵌套对象含数组字段的组合 = 8 行 |
| `TestNestedBoundaryMode` | 嵌套字段边界值模式 = 16 行 |
| `TestNestedEquivalenceMode` | 嵌套字段等价类模式 = 9 行 |

### test_scoped_combination.py

`CombinationSpec(scope=...)` 分层组合：不同层级字段使用不同组合模式。

| 测试方法 | 覆盖场景 |
| --- | --- |
| `test_root_pairwise_nested_cartesian` | 顶层 PAIRWISE + 嵌套 CARTESIAN 分层生效 |
| `test_multi_level_scopes` | 多 scope 各自独立组合后合并（笛卡尔积） |
| `test_single_spec_backward_compatible` | 单 spec 向后兼容（等同无 scope 的原有行为） |
| `test_scope_none_matches_top_level_only` | `scope=None` 只匹配顶层字段 |
| `test_explicit_fields_override_scope` | 显式 `fields` 覆盖 scope 的自动选取 |
| `test_boundary_mode_with_scope` | 边界值模式 + scope 分层 |
| `test_empty_scope_group` | scope 无匹配字段时退化为普通生成 |

### test_filter_edge_cases.py

后置过滤器过滤掉全部数据的边界场景。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestFilterAllRemoved` | 单对象被过滤返回 None、批量全过滤返回空列表、`limit(0)` 截断全部、全重复去重剩 1 条、链式过滤全部移除 |

---

## config_loader/

### test_config_from_dict.py

字典配置加载。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestConfigFromDict` | 空配置、仅 policies、仅 combinations、仅 post_filters、混合配置 |

### test_config_from_file.py

从文件加载配置，支持 JSON/YAML。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestConfigFromFile` | JSON 文件加载、YAML 文件加载、文件不存在异常、combinations 配置加载、post_filters 配置加载 |

### test_env_vars.py

环境变量插值 `${VAR}` 和 `${VAR:-default}` 格式。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestEnvVars` | 简单变量替换、带默认值替换、嵌套参数替换、多变量替换、空默认值、非字符串类型不替换 |

### test_param_aliases.py

参数别名映射（`PARAM_ALIASES`）简化配置。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestParamAliases` | enum.values→choices、range.min/max→min_val/max_val、array_count.count→source、property_selection.properties 直接映射、property_count.count→source、ref.ref_path、datetime 策略 |

### test_combinations_and_filters.py

combinations 和 post_filters 从配置加载。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestCombinationsAndFilters` | combinations 完整配置、post_filters 完整配置、完整配置组合 |

---

## openapi/

OpenAPI 文档解析和测试数据生成功能测试。

### test_converter.py

SchemaConverter 转换器测试，包括 nullable 转换边界情况。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestNullableConversion` | 简单类型 nullable、oneOf+nullable、anyOf+nullable、allOf+nullable |
| `TestSchemaConverter` | example 转换、参数 schema 提取、enum 字段检测、边界字段检测 |

### test_integration.py

OpenAPI 解析器和生成器的集成功能测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestOpenAPIParser` | 从字典解析、解析端点、解析 $ref 引用、解析真实文档 |
| `TestSchemaConverter` | nullable 字段转换、example 字段转换、参数 schema 提取、enum/边界字段检测 |
| `TestRequestDataGenerator` | 为端点生成数据、边界值模式生成、参数 example 使用、请求体 example 使用、schema example 使用、多模式 example 处理、field_policies 覆盖 example |
| `TestAPITestDataManager` | 创建管理器、获取端点、按 path+method 获取端点、按 path+method 生成数据、生成和保存数据 |
| `TestMultipleModes` | generation_mode 支持列表、多模式生成数据、去重功能、content_key 生成、summary 返回多模式、保存配置保留多模式 |
| `TestFieldPoliciesStrategies` | enum 策略在 field_policies 中使用、range 策略使用、random_string 策略使用 |
| `TestPathParamsNameFieldStrategy` | 路径参数 name 字段使用 username 策略（无空格，符合 URI 规范）、查询参数 name 可使用中文、路径参数支持自定义策略 |
| `TestFieldPoliciesWithStrategyRegistry` | faker 策略生成 UUID（Bug Fix）、datetime 策略支持、ipv4 策略支持、sequence 策略支持 |

### test_response_generator.py

ResponseDataGenerator 响应数据生成器测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestResponseDataGenerator` | 基本响应生成、多状态码生成、include_headers 配置、字段策略覆盖、ref_resolver 传递 |
| `TestResponseWithExamples` | 完整示例使用、部分示例合并补全、无示例 schema 自动生成 |
| `TestResponseDataModel` | GeneratedResponse 数据模型、to_dict 转换 |

### test_exceptions.py

OpenAPI 模块异常处理测试。

| 测试类 | 覆盖场景 |
| --- | --- |
| `TestOpenAPIParseErrors` | 无效 OpenAPI 文档、缺失必需字段、无效版本 |
| `TestEndpointNotFound` | operationId 不存在、path+method 不存在 |
| `TestRefResolutionErrors` | $ref 引用不存在、循环引用检测 |
