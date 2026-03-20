---
name: gen-data
description: "分析 JSON Schema 生成测试数据的 Python 脚本"
---

# 测试数据生成脚本生成器

分析用户提供的 JSON Schema，输出可直接运行的 Python 脚本使用 `data_builder` SDK 生成测试数据。

## 输入方式

- 内联粘贴 JSON Schema
- 提供文件路径（Read 工具读取）
- 提供 URL（WebFetch 获取）
- 未提供则要求用户提供

## 输出模板

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

## 核心 API

### 类

```python
FieldPolicy(path: str, strategy: Strategy)  # path 支持 user.*, items[*].id

BuilderConfig(
    policies: List[FieldPolicy] = [],
    strict_mode: bool = False,
    null_probability: float = 0.0,
    count: Optional[int] = None,
    combinations: List[CombinationSpec] = [],
    post_filters: List[Callable] = [],
    union_type_priority: Optional[List[str]] = None,  # 联合类型优先级（如 ["string", "integer"]）
    max_depth: Optional[int] = None,  # 递归结构最大深度
)

DataBuilder(schema: dict, config: Optional[BuilderConfig] = None)
builder.build(count: Optional[int] = None) -> Union[dict, List[dict]]
```

### 策略工厂函数

```python
fixed(value)                     # 固定值
random_string(length=10)         # 随机字符串
range_int(min_val=0, max_val=100)              # 整数范围
range_float(min_val=0.0, max_val=100.0, precision=2)  # 浮点范围
enum(choices, weights=None)     # 枚举选择
regex(pattern)                   # 正则生成
seq(start=1, step=1, prefix="", suffix="", padding=0)  # 自增序列
faker(method, locale="zh_CN")   # Faker 数据
callable_strategy(func)          # 自定义函数 func(ctx)
ref(path)                        # 引用其他字段
datetime(start=None, end=None, format="%Y-%m-%d %H:%M:%S", anchor=None, offset=None, date_range=None, time_range=None, specific_date=None, specific_time=None, timezone=None)  # 日期时间
password(length=12, use_digits=True, use_uppercase=True, use_lowercase=True, use_special=True)  # 密码
email(email_type="random", locale="zh_CN", domains=None)  # 邮箱
concat(strategies, separators=None)  # 级联合并
array_count(source)              # 数组元素数量
property_count(source)           # 对象属性数量
property_selection(properties)   # 对象属性选择
contains_count(source)           # contains 元素数量
schema_selection(source)         # oneOf/anyOf 分支选择
llm(config, prompt, json_output=False)  # LLM 生成（需 openai）
id_card(min_age=18, max_age=65, gender="random", region=None)  # 身份证号
bank_card(bank="random", card_type="debit")  # 银行卡号
phone(carrier="random", number_type="normal")  # 手机号
username(min_length=6, max_length=20, charset="alphanumeric_underscore", reserved_words=None, allow_uppercase=True)  # 用户名
```

### 动态配置

```python
# 从字典加载
config = BuilderConfig.from_dict({
    "policies": [{"path": "id", "strategy": {"type": "sequence", "start": 1001}}],
    "combinations": [{"mode": "PAIRWISE", "fields": ["status", "type"]}],
    "union_type_priority": ["string", "integer"],  # 联合类型优先级
    "null_probability": 0.1,  # null 值概率
})

# 从文件加载
config = BuilderConfig.from_file("policy.yaml")

# 环境变量插值
{"path": "id", "strategy": {"type": "sequence", "start": "${START_ID:-1}"}}
```

### 参数别名

| 配置参数 | 映射到 | 适用策略 |
| --- | --- | --- |
| `values` | `choices` | `enum` |
| `min`/`max` | `min_val`/`max_val` | `range` |
| `count` | `source` | `array_count`, `property_count` |
| `date` | `date_range` | `datetime` |
| `time` | `time_range` | `datetime` |
| `pwd_len` | `length` | `password` |

### 组合生成

```python
from data_builder import CombinationMode, CombinationSpec

CombinationSpec(
    mode=CombinationMode.PAIRWISE,  # CARTESIAN/PAIRWISE/ORTHOGONAL/EQUIVALENCE/BOUNDARY/INVALID
    fields=["status", "type"],
    strength=2,  # ORTHOGONAL 覆盖强度
)
```

### 后置过滤器

```python
from data_builder import deduplicate, constraint_filter, limit, tag_rows

deduplicate(key_fields=["id"])
constraint_filter(lambda row: row["age"] > 18)
limit(max_count=100)
tag_rows(tag_field="_tag", tag_value="test")
```

## 策略选择算法（优先级链）

### 第 1 级：Schema 关键字

| Schema 特征 | 策略 |
| --- | --- |
| `"enum": [...]` | `enum(choices)` |
| `"const": value` | `fixed(value)` |
| `"pattern": "..."` | `regex(pattern)` |
| `"examples": [...]` | `enum(examples)` |
| `"example": value` | `fixed(value)` |

### 第 2 级：format 映射

| format | 策略 |
| --- | --- |
| `email` | `faker("email")` |
| `uri`/`url` | `faker("uri")` |
| `uuid` | `faker("uuid4")` |
| `date` | `datetime(format="%Y-%m-%d")` |
| `date-time` | `datetime()` |

### 第 3 级：字段名语义

| 字段名模式 | 策略 |
| --- | --- |
| `id`, `*_id` (integer) | `seq()` |
| `uuid`, `*_uuid` | `faker("uuid4")` |
| `name`, `*_name` | `faker("name")` |
| `email`, `*_email` | `email()` |
| `phone`, `mobile` | `faker("phone_number")` |
| `address`, `*_address` | `faker("address")` |
| `city`, `province`, `country` | `faker("city")`/`faker("province")`/`faker("country")` |
| `created_at`, `updated_at`, `*_at` | `datetime()` |
| `*_date`, `birthday` | `datetime(format="%Y-%m-%d")` |
| `price`, `amount`, `cost` | `range_float(0.01, 9999.99, precision=2)` |
| `score`, `rating` | `range_float(0, 5.0, precision=1)` |
| `count`, `quantity`, `age` | `range_int(1, 100)` |
| `status` | `enum(["active", "inactive", "pending"])` |
| `type`, `category` | `enum(["type_A", "type_B", "type_C"])` |
| `is_*`, `has_*` | `enum([True, False])` |
| `gender` | `enum(["male", "female"])` |
| `role` | `enum(["admin", "user", "guest"])` |
| `order_no`, `code`, `sku` | `seq(prefix="ORD-", padding=6)` |
| `password`, `passwd` | `password(length=12)` |
| `token`, `api_key`, `secret` | `random_string(length=32)` |
| `description`, `content` | `faker("text", max_nb_chars=200)` |
| `url`, `website` | `url()` |
| `ip`, `ip_address` | `ipv4()` |
| `id_card`, `id_number`, `identity_card` | `id_card()` |
| `bank_card`, `card_number` | `bank_card()` |
| `phone`, `mobile`, `cellphone` | `phone()` |
| `username`, `user_name`, `login_name` | `username()` |

### 第 4 级：type 兜底

| type | 策略 |
| --- | --- |
| `integer` | `range_int(minimum, maximum)` |
| `number` | `range_float(minimum, maximum)` |
| `string` | `random_string(length)` |
| `boolean` | `enum([True, False])` |

### SDK 自动处理

- `multipleOf`：自动生成倍数值
- `uniqueItems`：数组自动去重
- `additionalProperties`：根据 schema 生成属性
- `$ref`、`allOf`、`anyOf`、`oneOf`：自动处理
- `prefixItems`：自动按位置生成

## 复杂结构

### 嵌套/数组

```python
FieldPolicy("user.name", faker("name"))
FieldPolicy("items[*].id", seq(start=100))
FieldPolicy("items", array_count(3))      # 精确长度
FieldPolicy("items", array_count(lambda ctx: random.randint(2, 5)))  # 随机长度
FieldPolicy("profile", property_count(2)) # 属性数量
FieldPolicy("profile", property_selection(["name", "email"]))  # 属性选择
```

### 字段引用

```python
# 被引用字段必须在前
FieldPolicy("id", seq(start=1001)),
FieldPolicy("updated_by", ref("id")),
```

### oneOf/anyOf 分支

```python
FieldPolicy("payment", schema_selection(0))  # 固定分支
FieldPolicy("payment", schema_selection(callable_strategy(lambda ctx: ctx.index % 2)))  # 动态
```

## 约束规则

1. 不使用 LLMStrategy，除非用户明确要求
2. 输出用 `json.dumps(data, ensure_ascii=False, indent=2, default=str)`
3. 为每个 FieldPolicy 添加行尾注释说明策略选择理由
4. **排序**：被 `ref()` 引用的字段必须排在引用者之前
5. **路径绑定**：结构策略绑定到父级路径（如 `"items"` 而非 `"items[*].id"`）
6. 默认生成 `count=5`
7. 优先为 `required` 字段配置策略
8. 根据 `minimum`/`maximum` 调整策略参数

## datetime 快速参考

```python
datetime()                                  # 默认过去一年
datetime(start="2024-01-01", end="2024-12-31")
datetime(format="%Y-%m-%d")
datetime(anchor="today", offset="-1d")      # 昨天
datetime(anchor="now", offset="+2h")        # 当前+2小时
datetime(date_range="2024-01-01,2024-12-31", time_range="09:00:00,17:00:00")
datetime(specific_date="2024-05-15", specific_time="14:30:00")
datetime(timezone="Asia/Shanghai")
```

## password 快速参考

```python
password()                      # 默认12位
password(length=16)
password(use_digits=True, use_uppercase=False, use_lowercase=False, use_special=False)
```

## email 快速参考

```python
email()                         # 随机类型
email(email_type="qq")          # QQ 邮箱
email(email_type="gmail")       # Gmail
email(email_type="163")         # 163 邮箱
email(email_type="outlook")     # Outlook
email(email_type="custom", domains=["example.com"])  # 自定义域名
email(email_type="safe")        # 安全随机邮箱
email(email_type="idn")         # IDN 国际化域名邮箱（支持 Unicode 域名）
email(email_type="random")      # 随机类型混合
email(locale="en_US")           # 英文 locale
```

## 账户类数据快速参考

```python
# 身份证号
id_card()                       # 默认18-65岁，随机性别和地区
id_card(min_age=25, max_age=35) # 指定年龄范围
id_card(gender="male")          # 指定性别（male/female/random）
id_card(region="110000")        # 指定地区码（6位）

# 银行卡号
bank_card()                     # 随机银行，借记卡
bank_card(bank="icbc")          # 指定银行（icbc/cbc/abc/boc等15家）
bank_card(card_type="credit")   # 指定卡类型（debit/credit）

# 手机号
phone()                         # 随机运营商，普通号码
phone(carrier="mobile")         # 指定运营商（mobile/unicom/telecom/random）
phone(number_type="virtual")    # 虚拟运营商号码

# 用户名
username()                      # 默认6-20位，字母数字下划线
username(min_length=8, max_length=16)  # 指定长度范围
username(charset="alphanumeric")        # 仅字母数字
username(reserved_words=["admin", "root"])  # 过滤保留字
username(allow_uppercase=False)         # 不允许大写字母
```

## 联合类型（Union Type）快速参考

```python
# 联合类型优先级配置
config = BuilderConfig(
    union_type_priority=["string", "integer", "number"]  # 按优先级顺序选择类型
)

# null 值概率配置
config = BuilderConfig(
    null_probability=0.1  # 10% 概率生成 null
)

# nullable 关键字（JSON Schema Draft 7+）
schema = {
    "type": "string",
    "nullable": true  # 可以生成 null
}

# 联合类型包含 null（JSON Schema Draft 4-6）
schema = {
    "type": ["string", "null"]  # 可以生成 string 或 null
}
```

## format 快速参考

JSON Schema 的 `format` 关键字支持以下值（自动生成对应格式数据）：

| format | 说明 |
| --- | --- |
| `email` | 普通邮箱 |
| `idn-email` | IDN 国际化域名邮箱 |
| `uri`/`url` | URI/URL |
| `uuid` | UUID v4 |
| `date` | 日期（YYYY-MM-DD） |
| `date-time` | 日期时间（ISO8601） |
| `time` | 时间（HH:MM:SS） |
| `ipv4` | IPv4 地址 |
| `ipv6` | IPv6 地址 |
| `hostname` | 主机名 |
| `idn-hostname` | IDN 主机名 |
| `mac` | MAC 地址 |
| `cidr` | CIDR 表示法 |
| `ip-range` | IP 范围 |
| `duration` | ISO8601 持续时间 |
| `uri-reference` | URI 引用 |
| `json-pointer` | JSON Pointer |
| `relative-json-pointer` | 相对 JSON Pointer |
| `regex` | 正则表达式模式 |
