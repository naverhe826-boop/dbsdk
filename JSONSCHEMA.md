# JSON Schema Draft 2020-12 数据生成支持矩阵

## 说明

- 基于规范: JSON Schema Draft 2020-12 (json-schema-core + json-schema-validation)
- ✅ 支持 — 数据生成器已完整实现该关键字的数据生成语义
- ⚠️ 部分支持 — 仅实现部分场景或有限制
- ❌ 不支持 — 未实现
- 🔵 不适用 — 该关键字为元信息/注解，对数据生成无直接影响

## 按词汇表(Vocabulary)分类的关键字清单

### 1. Core 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| $schema | 🔵 不适用 | 元信息，标识方言 |
| $vocabulary | 🔵 不适用 | 元模式声明 |
| $id | 🔵 不适用 | 模式资源标识 |
| $anchor | ❌ 不支持 | 未实现锚点引用 |
| $dynamicAnchor | ❌ 不支持 | 未实现动态锚点 |
| $ref | ⚠️ 部分支持 | 仅支持内部引用(`#/definitions/*`, `#/$defs/*`)，不支持外部URI引用；通过 `max_depth` 参数支持递归结构生成 |
| $dynamicRef | ❌ 不支持 | 未实现动态引用 |
| $defs | ✅ 支持 | 作为`$ref`引用仓库，同时支持旧版`definitions` |
| $comment | 🔵 不适用 | 注释，无需处理 |

### 2. Applicator 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| allOf | ✅ 支持 | 递归合并所有子schema，`properties`/`required`深度合并 |
| anyOf | ✅ 支持 | 随机选分支或`SchemaSelectionStrategy`控制 |
| oneOf | ✅ 支持 | 随机选分支或`SchemaSelectionStrategy`控制 |
| not | ⚠️ 部分支持 | 支持`not:{type:X}`类型排除和`not:{enum:[...]}`枚举排除；复杂`not`忽略 |
| if | ✅ 支持 | 随机选then或else分支，合并对应约束 |
| then | ✅ 支持 | 配合`if`使用 |
| else | ✅ 支持 | 配合`if`使用 |
| dependentSchemas | ✅ 支持 | trigger属性存在时补生成依赖schema中的属性 |
| prefixItems | ✅ 支持 | 元组定位schema，配合`items:false`限制长度 |
| items | ✅ 支持 | 包括`items:false`语义 |
| contains | ✅ 支持 | 配合`ContainsCountStrategy`控制匹配元素数 |
| properties | ✅ 支持 | |
| patternProperties | ✅ 支持 | 用exrex为每个pattern生成匹配键名并生成值 |
| additionalProperties | ✅ 支持 | schema形式(dict)生成额外属性；`false`过滤非声明属性；与patternProperties联动 |
| propertyNames | ✅ 支持 | 读取`propertyNames.pattern`用exrex生成匹配键名 |

### 3. Unevaluated 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| unevaluatedItems | ❌ 不支持 | |
| unevaluatedProperties | ❌ 不支持 | |

### 4. Validation 词汇表

#### 4.1 类型

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| type | ✅ 支持 | 全部7种类型 + 联合类型数组(如`["string","null"]`)；支持`union_type_priority`配置优先级 |
| enum | ✅ 支持 | 随机选取枚举值；当无`type`时自动从`enum`推导类型 |
| const | ✅ 支持 | 返回固定值；当无`type`时自动从`const`推导类型 |

#### 4.2 数值约束

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| multipleOf | ✅ 支持 | integer/number均支持 |
| maximum | ✅ 支持 | |
| exclusiveMaximum | ✅ 支持 | |
| minimum | ✅ 支持 | |
| exclusiveMinimum | ✅ 支持 | |

#### 4.3 字符串约束

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| maxLength | ✅ 支持 | |
| minLength | ✅ 支持 | |
| pattern | ✅ 支持 | 通过exrex生成匹配值 |

#### 4.4 数组约束

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| maxItems | ✅ 支持 | |
| minItems | ✅ 支持 | |
| uniqueItems | ✅ 支持 | 重试去重(最多`count*3`次重试) |
| maxContains | ✅ 支持 | 配合contains使用，clamp策略值或推导默认值 |
| minContains | ✅ 支持 | 配合contains使用，clamp策略值或推导默认值 |

#### 4.5 对象约束

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| maxProperties | ✅ 支持 | 控制生成属性数量上限 |
| minProperties | ✅ 支持 | 控制生成属性数量下限，required优先 |
| required | ✅ 支持 | |
| dependentRequired | ✅ 支持 | trigger属性存在时自动补生成依赖属性 |

### 5. Meta-Data 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| title | 🔵 不适用 | 注解 |
| description | 🔵 不适用 | 注解 |
| default | ✅ 支持 | 作为回退值生成 |
| deprecated | 🔵 不适用 | 注解 |
| readOnly | 🔵 不适用 | 注解 |
| writeOnly | 🔵 不适用 | 注解 |
| examples | ✅ 支持 | 随机选取示例值 |

### 6. Format 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| format | ⚠️ 部分支持 | 支持24种: `email`/`idn-email`/`uri`/`uuid`/`date`/`date-time`/`time`/`ipv4`/`ipv6`/`hostname`/`idn-hostname`/`mac`/`cidr`/`ip-range`/`duration`/`uri-reference`/`json-pointer`/`relative-json-pointer`/`regex`/`iri`/`iri-reference`/`idn-hostname`/`iri`/`iri-reference`; 不支持: `uri-template` |

### 7. Content 词汇表

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| contentMediaType | ❌ 不支持 | |
| contentEncoding | ❌ 不支持 | |
| contentSchema | ❌ 不支持 | |

### 扩展支持（非标准）

| 关键字 | 状态 | 说明 |
| --- | --- | --- |
| nullable (OpenAPI) | ✅ 支持 | 支持布尔值形式(`true/false`)和数组形式(`["null","string"]`)；配合`null_probability`使用 |
| example (OpenAPI) | ✅ 支持 | 单值示例回退 |
| definitions (Draft-07) | ✅ 支持 | 旧版`$defs`等价 |

## 统计汇总

| 状态 | 数量 | 关键字 |
| --- | --- | --- |
| ✅ 支持 | 35 | `$defs` `allOf` `anyOf` `oneOf` `if` `then` `else` `dependentSchemas` `prefixItems` `items` `contains` `properties` `patternProperties` `additionalProperties` `propertyNames` `type` `enum` `const` `multipleOf` `maximum` `exclusiveMaximum` `minimum` `exclusiveMinimum` `maxLength` `minLength` `pattern` `maxItems` `minItems` `uniqueItems` `maxContains` `minContains` `maxProperties` `minProperties` `required` `dependentRequired` `default` `examples` |
| ⚠️ 部分支持 | 3 | `$ref` `format` `not` |
| ❌ 不支持 | 7 | `$anchor` `$dynamicAnchor` `$dynamicRef` `unevaluatedItems` `unevaluatedProperties` `contentMediaType` `contentEncoding` `contentSchema` `uri-template`(format子项) |
| 🔵 不适用 | 9 | `$schema` `$vocabulary` `$id` `$comment` `title` `description` `deprecated` `readOnly` `writeOnly` |
