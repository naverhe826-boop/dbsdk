# dbsdk

A Python data generation framework based on the strategy pattern for generating structured test data in bulk from JSON Schema and OpenAPI documents.

## Installation

```bash
./install.sh setup          # Install current version
./install.sh setup 0.3.0    # Install specific version
./install.sh list           # View version and installation status
./install.sh remove         # Uninstall
```

### Dependency Notes

**Core Dependencies** (automatically installed):
- `faker` - Virtual data generation library
- `exrex` - Regular expression data generation
- `python-dotenv` - Environment variable loading
- `pyyaml` - YAML file parsing
- `idna` - Internationalized domain name support

**Optional Dependencies**:
- `openai` - Required for LLMStrategy (`pip install dbsdk[llm]`)
- `pytest` - Test framework (`pip install dbsdk[dev]`)

## Quick Start

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

### Dynamic Configuration via dict

Supports building configuration dynamically from dictionary without explicit `BuilderConfig` import:

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

# Build configuration via dict
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

Also supports `params` nested syntax:

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

## Usage Overview

dbsdk supports two main approaches for test data generation: **JSON Schema** and **OpenAPI** documentation.

### 1. JSON Schema Approach

Suitable for scenarios where you have JSON Schema definitions and need to generate structured test data.

```python
from data_builder import DataBuilder, BuilderConfig, FieldPolicy

schema = {"type": "object", "properties": {...}}
builder = DataBuilder(schema, config=BuilderConfig(policies=[...]))
data = builder.build(count=5)
```

**Core Features**:
- 20+ built-in strategies: fixed, enum, range, seq, faker, datetime, email, password, ipv4/ipv6, domain, url, mac, cidr, regex, etc.
- Combination generation: supports CARTESIAN, PAIRWISE, ORTHOGONAL, EQUIVALENCE, BOUNDARY, INVALID modes
- Smart inference: automatically generates data based on schema's format, enum, pattern, and field name semantics
- Dynamic configuration: supports loading configuration from dict/JSON/YAML files
- Advanced features: field references (ref), custom functions (callable_strategy), LLM generation (llm), union types, nullable

### 2. OpenAPI Approach

Suitable for automatically generating API test data from OpenAPI 3.x documentation.

```python
from data_builder.openapi import APITestDataManager

manager = APITestDataManager(openapi_document="api.json")
requests = manager.generate_for_endpoint("get_user")
```

**Core Features**:
- Document parsing: supports JSON/YAML, automatically parses $ref references (including circular references)
- Schema conversion: OpenAPI Schema → JSON Schema, handles nullable, examples
- Multi-mode generation: RANDOM, BOUNDARY, EQUIVALENCE, CARTESIAN, PAIRWISE, INVALID, supports multi-mode mixing
- Endpoint filtering: filter by tags, operationId, path patterns
- Response generation: supports generating Mock response data, including response headers, multiple status codes, example completion
- Field policies: supports field_policies to override automatic generation strategies
- Data persistence: supports saving/loading configuration and data

**Response Mock Data Generation**:
```python
# Method 1: Unified generation via manager
manager = APITestDataManager(openapi_document="api.json")
manager.configure_response_generator({
    "include_headers": True,
    "count": 2,
    "field_policies": [{"path": "price", "strategy": {"type": "fixed", "value": 99.9}}]
})
responses = manager.generate_response_for_endpoint("get_user", status_codes=["200", "404"])

# Method 2: Independent response generator
from data_builder.openapi import ResponseDataGenerator, OpenAPIParser
parser = OpenAPIParser(openapi_document="api.json")
generator = ResponseDataGenerator(ref_resolver=parser, include_headers=True)
responses = generator.generate_for_endpoint(endpoint, status_codes=["200"])
```

Data generation priority: field policies > examples > Schema automatic generation.

### Agent Usage (Skill)

dbsdk provides AI Agent skill definitions for automatic test data script generation with Claude, Cline, and other AI programming assistants.

**Skill Name**: `gen-data`

**Input Methods**:
- Inline paste JSON Schema
- Provide file path (via Read tool)
- Provide URL (via WebFetch)

**Output Template**:
```python
import json
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, ...

schema = { ... }

config = BuilderConfig(
    policies=[
        FieldPolicy("field_path", strategy()),  # Strategy selection rationale
    ]
)

builder = DataBuilder(schema, config)
data = builder.build(count=N)
print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
```

**Constraint Rules**:
1. Do not use LLMStrategy unless explicitly requested by user
2. Output using `json.dumps(data, ensure_ascii=False, indent=2, default=str)`
3. Add inline comments for each FieldPolicy explaining strategy selection rationale
4. Fields referenced by `ref()` must be listed before the referencing field
5. Structure strategies bind to parent path (e.g., `"items"` not `"items[*].id"`)
6. Default generate `count=5`
7. Prioritize strategy configuration for `required` fields

## Core Concepts

### FieldPolicy

Binds field paths with generation strategies, `path` supports wildcards:

| Path Syntax | Description |
| --- | --- |
| `"user.name"` | Exact path |
| `"user.*"` | All fields under user |
| `"orders[*].id"` | id field of array elements |

### DataBuilder Configuration

```python
builder = DataBuilder(schema)
builder.config(
    FieldPolicy("field1", strategy1),
    FieldPolicy("field2", strategy2),
)
# Or use configuration dictionary
builder.config_from_dict({
    "policies": [...],
    "combinations": [...],
    "post_filters": [...],
    "strict_mode": False,
    "null_probability": 0.0,
    "max_depth": None,
})
```

### DataBuilder Usage

```python
builder.build()          # Generate single object
builder.build(count=50)  # Generate list of 50 objects
```

### Union Types

Supports JSON Schema union types with configurable type priority:

```python
from data_builder import DataBuilder, BuilderConfig

# Union type schema
schema = {
    "type": ["string", "integer", "number"],
    "minLength": 5
}

# Configure priority, prefer string type
builder = DataBuilder(
    schema,
    config=BuilderConfig(
        union_type_priority=["string", "integer", "number"]
    )
)
result = builder.build(count=5)  # All return string type
```

### nullable Keyword

Supports Draft 7+ `nullable` keyword and Draft 4-6 union type null:

```python
# Draft 7+ style
schema1 = {
    "type": "string",
    "nullable": True
}

# Draft 4-6 style (union type)
schema2 = {
    "type": ["string", "null"]
}

# Configure null probability
builder = DataBuilder(
    schema1,
    config=BuilderConfig(null_probability=0.2)  # 20% probability of null
)
result = builder.build(count=10)
```

Configuration Parameters:
- `policies` - FieldPolicy list
- `strict_mode` - If True, throw exception when no policy
- `null_probability` - Probability of generating null (0~1)
- `union_type_priority` - Union type priority (e.g., `["string", "integer"]`), select types in configured order
- `combinations` - CombinationSpec list, supports layered combinations
- `post_filters` - Post-filter list
- `max_depth` - Recursion depth limit, None throws exception on circular reference, >=1 enables recursive generation

## Built-in Strategies

| Factory Function | Description |
| --- | --- |
| `fixed(value)` | Fixed value |
| `random_string(length, charset)` | Random string |
| `range_int(min, max)` | Random integer |
| `range_float(min, max, precision)` | Random floating-point number |
| `enum(choices, weights)` | Enum random selection, supports weights |
| `regex(pattern)` | Generate string by regex |
| `seq(start, step, prefix, suffix, padding)` | Auto-increment sequence |
| `concat(strategies, separators)` | Concatenate multiple strategy values |
| `faker(method, locale, **kwargs)` | Call Faker method, default `zh_CN` |
| `ref(ref_path, transform)` | Reference other field's value |
| `datetime(start, end, format, timezone, anchor, offset, date_range, time_range, specific_date, specific_time)` | Random datetime, supports anchor/offset/date_range/time_range/specific_date/specific_time/timezone |
| `password(length, use_digits, use_uppercase, use_lowercase, use_special, special_chars)` | Password generation, compliant with Linux/Windows password policies, length 8-32 |
| `email(email_type, locale, domains)` | Email generation, supports qq/gmail/163/outlook/custom/safe/idn/random types, domains can specify domain list |
| `ipv4(ip_class, ip_address_type, ip_subnet_mask, ip_multicast_groups)` | IPv4 address generation, supports A/B/C/D/E classes, private addresses, multicast addresses, specified subnets, etc. |
| `ipv6(ip_class, ip_address_type, ip_scope)` | IPv6 address generation, supports global unicast, link-local, unique local, multicast, loopback addresses, etc. |
| `domain(domain_type, tld_list, max_level)` | Domain name generation, supports IDN/Punycode, custom TLD, multi-level domains |
| `url(protocol, host_type, path_type, query_type)` | URL/URI generation, supports scheme, host, port, path, query, fragment |
| `mac(oui, address_type, administration_type, broadcast_address)` | MAC address generation, supports OUI, unicast/multicast, global/local admin bits |
| `cidr(ip_version, prefix_length, network_class)` | CIDR notation generation, supports IPv4/IPv6 |
| `ip_range(ip_version, ip_class)` | IP range generation, supports IPv4/IPv6 |
| `id_card(min_age, max_age, gender, region)` | ID card number generation, supports age range, gender, region code configuration |
| `bank_card(bank, card_type)` | Bank card number generation, supports 15 mainstream bank BINs, Luhn algorithm verification |
| `phone(carrier, number_type)` | Phone number generation, supports three major carriers and virtual carrier number segments |
| `username(min_length, max_length, charset, reserved_words, allow_uppercase)` | Username generation, supports length, character set, reserved word filtering |
| `array_count(source)` | Control array element count |
| `property_count(source)` | Control object property count |
| `property_selection(properties)` | Control which properties object generates |
| `contains_count(source)` | Control array contains element count |
| `schema_selection(source)` | Control oneOf/anyOf branch selection |
| `llm(config, prompt, system_prompt, json_output)` | Call LLM to generate, `config` is `LLMConfig` instance |
| `callable_strategy(func)` | Custom function `func(ctx) -> Any` |

## Combination Generation

Generate combination-covered test datasets across fields via `CombinationSpec`, behavior unchanged when not configured.

### Combination Modes

| Mode | Description |
| --- | --- |
| `RANDOM` | Default, follows original random generation logic |
| `CARTESIAN` | Cartesian product, enumerate all combinations |
| `PAIRWISE` | Pairwise combination, cover all binary pairs |
| `ORTHOGONAL` | Orthogonal array, cover t-tuples (`strength` controls t) |
| `EQUIVALENCE` | Full combination of equivalence class representative values |
| `BOUNDARY` | Full combination of boundary values |
| `INVALID` | Invalid value injection (each row has only one field with invalid value, others with normal values) |

### Basic Usage

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

# Cartesian product: 3×2=6 items
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

### Invalid Value Testing (INVALID Mode)

Rotating invalid: each row has only one field with invalid value, other fields take normal values (equivalence class median values).

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
# Each row has only amount or name as invalid value
```

Fields without policies in BOUNDARY/EQUIVALENCE/INVALID modes automatically derive value ranges from schema constraints (minimum/maximum/minLength/maxLength, etc.).

### Constraint Filtering

```python
{
    "mode": "CARTESIAN",
    "constraints": [
        {
            "predicate": "not (row['method'] == 'card' and row['currency'] == 'CNY')",
            "description": "card does not support CNY",
        },
    ],
}
```

### Layered Combination (Scoped Combination)

Configure different combination modes for fields at different levels via multiple `CombinationSpec`:

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
# Result: top-level PAIRWISE combination × nested CARTESIAN combination
```

`scope` parameter:

- `None`: Match top-level fields (without `.`)
- `"user"`: Match `user.*` fields

Combination results of different scopes will be merged via Cartesian product.

### Post-Filters

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

### Relationship between count and Combinations

```python
builder.build()         # Return all combination rows
builder.build(count=3)  # Randomly sample 3 items from combination results
builder.build(count=99) # Full set + randomly supplement to 99 items
```

## Schema format Keyword

When field schema has `format` keyword and `FieldPolicy` is not configured, `string` type fields automatically generate values in corresponding format:

| format | Example Output |
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

Unrecognized format values fall through to default random string generation (compliant with JSON Schema specification).

Priority: `FieldPolicy` > `enum`/`const`/`default` > `pattern` > `format` > Type fallback

## Schema example / examples Keywords

When field schema contains `example` or `examples` keywords and `FieldPolicy` is not configured, automatically uses example values to generate data.

Priority: `enum` > `const` > `default` > `examples` (randomly select one) > `example` (fixed value) > Type fallback

```python
schema = {
    "type": "object",
    "properties": {
        "code":  {"type": "string",  "example": "CN"},        # Always returns "CN"
        "level": {"type": "integer", "examples": [1, 2, 3]},  # Randomly select from list
        "name":  {"type": "string"},                           # Fall back to type
    }
}
DataBuilder(schema).build(count=3)
```

> Explicit `FieldPolicy` always takes priority and overrides `example`/`examples`.

## Example: Nested Order Data

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

Generate field values by calling LLM via OpenAI-compatible interface, requires additional installation of `openai` package:

```bash
pip install openai
```

Or install using optional dependencies:

```bash
pip install dbsdk[llm]
```

```python
from data_builder import DataBuilder

llm_config = {
    "api_key": "your-api-key",
    "model": "gpt-4o-mini",
    "base_url": "https://api.openai.com/v1",  # Can replace with any OpenAI-compatible address
}

DataBuilder(schema).config_from_dict({
    "policies": [
        {
            "path": "description",
            "strategy": {
                "type": "llm",
                "config": llm_config,
                "prompt": "Generate a realistic product description for field {field_path}, field schema: {field_schema}",
            }
        },
        {
            "path": "tags",
            "strategy": {
                "type": "llm",
                "config": llm_config,
                "prompt": "Generate 3 tags for the product, return JSON array",
                "json_output": True,
            }
        },
    ],
}).build()
```

`LLMConfig` parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `api_key` | Required | API key |
| `model` | Required | Model name |
| `base_url` | `https://api.openai.com/v1` | API address |
| `timeout` | `30` | Request timeout (seconds) |
| `max_tokens` | `256` | Maximum output token count |
| `temperature` | `0.7` | Generation temperature |
| `extra_headers` | `{}` | Additional request headers |

`prompt` template placeholders: `{field_path}`, `{field_schema}`, `{root_data_json}`, `{parent_data_json}`, `{index}`

Custom strategies can access full context via `ctx`:

```python
from data_builder import DataBuilder

def my_func(ctx):
    # ctx.field_path  - Current field path
    # ctx.field_schema - Current field schema
    # ctx.root_data   - Root data object (partially generated)
    # ctx.parent_data - Parent data object
    # ctx.index       - Current index during batch generation
    return f"custom-{ctx.index}"

DataBuilder(schema).config_from_dict({
    "policies": [
        {"path": "code", "strategy": {"type": "callable", "func": my_func}},
    ],
}).build()
```

## Related Documentation

- [README.md](README.md) - 中文文档
- [JSONSCHEMA.md](JSONSCHEMA.md) - JSON Schema support documentation
- [OPENAPI.md](OPENAPI.md) - OpenAPI test data generation documentation
- [examples/](examples/) - Example code directory (includes newly added OpenAPI strategy examples)
- [tests/](tests/) - Test code directory

![Architecture Design](design.png)
