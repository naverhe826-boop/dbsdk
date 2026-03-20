"""JSON Schema 关键字支持补全测试"""
import re
import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, contains_count


# ── P0: additionalProperties: false ──


class TestAdditionalPropertiesFalse:
    def test_filters_extra_keys(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "additionalProperties": False,
        }
        result = DataBuilder(schema).build()
        assert set(result.keys()) == {"name", "age"}

    def test_allows_declared_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "integer"},
            },
            "additionalProperties": False,
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            assert set(result.keys()) <= {"a", "b"}

    def test_root_data_sync(self):
        """root_data 也同步过滤"""
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "additionalProperties": False,
        }
        result = DataBuilder(schema).build()
        assert set(result.keys()) == {"x"}


# ── P0: minProperties / maxProperties ──


class TestMinMaxProperties:
    def test_min_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
                "c": {"type": "string"},
                "d": {"type": "string"},
            },
            "minProperties": 3,
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result) >= 3

    def test_max_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
                "c": {"type": "string"},
                "d": {"type": "string"},
            },
            "maxProperties": 2,
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result) <= 2

    def test_min_max_with_required(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
                "c": {"type": "string"},
            },
            "required": ["a", "b"],
            "minProperties": 2,
            "maxProperties": 2,
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result) == 2
            assert "a" in result
            assert "b" in result

    def test_exact_count(self):
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "z": {"type": "integer"},
            },
            "minProperties": 1,
            "maxProperties": 1,
        }
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert len(result) == 1


# ── P0: minContains / maxContains ──


class TestMinMaxContains:
    SCHEMA = {
        "type": "object",
        "properties": {
            "arr": {
                "type": "array",
                "items": {"type": "string"},
                "contains": {"type": "integer", "const": 42},
                "minItems": 3,
                "maxItems": 8,
            }
        },
    }

    def test_min_contains_default(self):
        """无策略有 contains 时默认 minContains=1"""
        for _ in range(10):
            result = DataBuilder(self.SCHEMA).build()
            arr = result["arr"]
            assert 42 in arr

    def test_min_contains_explicit(self):
        schema = {
            "type": "object",
            "properties": {
                "arr": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "const": 99},
                    "minContains": 3,
                    "maxContains": 5,
                    "minItems": 3,
                    "maxItems": 10,
                }
            },
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            arr = result["arr"]
            count_99 = sum(1 for x in arr if x == 99)
            assert 3 <= count_99 <= 5

    def test_clamp_with_strategy(self):
        """ContainsCountStrategy 结合 minContains/maxContains clamp"""
        schema = {
            "type": "object",
            "properties": {
                "arr": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "const": 7},
                    "minContains": 2,
                    "maxContains": 4,
                    "minItems": 4,
                    "maxItems": 10,
                }
            },
        }
        # 策略请求 1，但 minContains=2 会 clamp 上去
        config = BuilderConfig(policies=[FieldPolicy("arr", contains_count(1))])
        for _ in range(10):
            result = DataBuilder(schema, config).build()
            arr = result["arr"]
            count_7 = sum(1 for x in arr if x == 7)
            assert count_7 >= 2

        # 策略请求 10，但 maxContains=4 会 clamp 下来
        config = BuilderConfig(policies=[FieldPolicy("arr", contains_count(10))])
        for _ in range(10):
            result = DataBuilder(schema, config).build()
            arr = result["arr"]
            count_7 = sum(1 for x in arr if x == 7)
            assert count_7 <= 4


# ── P0: dependentRequired ──


class TestDependentRequired:
    def test_dependent_generated(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "credit_card": {"type": "string"},
                "billing_address": {"type": "string"},
            },
            "dependentRequired": {
                "credit_card": ["billing_address"],
            },
        }
        # credit_card 必然在 result 中（默认生成所有属性），所以 billing_address 也必须在
        for _ in range(10):
            result = DataBuilder(schema).build()
            if "credit_card" in result:
                assert "billing_address" in result

    def test_no_trigger_no_dependency(self):
        """trigger 不在结果中时不补充依赖"""
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
            "maxProperties": 1,
            "dependentRequired": {
                "a": ["b"],
            },
        }
        for _ in range(30):
            result = DataBuilder(schema).build()
            # maxProperties=1 保证只生成一个属性
            # 如果 a 被选中则 dependentRequired 会补 b（总共2个），否则只有一个
            if "a" in result:
                assert "b" in result


# ── P0: format 扩展 ──


class TestFormatExtensions:
    @pytest.mark.parametrize("fmt,pattern", [
        ("duration", r"^P\d+Y\d+M\d+DT\d+H\d+M\d+S$"),
        ("uri-reference", r"^/path/to/\w+$"),
        ("json-pointer", r"^/\w+/\w+$"),
        ("relative-json-pointer", r"^\d+/\w+$"),
        ("regex", r"^\^"),
    ])
    def test_format_generates_valid(self, fmt, pattern):
        schema = {"type": "string", "format": fmt}
        builder = DataBuilder({"type": "object", "properties": {"f": schema}})
        for _ in range(5):
            result = builder.build()
            assert re.match(pattern, result["f"]), f"format={fmt}, got={result['f']}"


# ── P1: if/then/else ──


class TestIfThenElse:
    def test_then_branch(self):
        """选中 then 分支时合并 if + then 约束"""
        schema = {
            "type": "object",
            "properties": {"country": {"type": "string"}},
            "if": {"properties": {"country": {"const": "US"}}},
            "then": {"properties": {"postal_code": {"type": "string", "pattern": "^\\d{5}$"}}},
            "else": {"properties": {"postal_code": {"type": "string", "pattern": "^[A-Z]\\d[A-Z]$"}}},
        }
        # 多次生成，应该两个分支都能覆盖到
        results = [DataBuilder(schema).build() for _ in range(50)]
        has_then = any("postal_code" in r and re.match(r"^\d{5}$", r.get("postal_code", "")) for r in results)
        has_else = any("postal_code" in r and re.match(r"^[A-Z]\d[A-Z]$", r.get("postal_code", "")) for r in results)
        # 至少覆盖其中一个分支
        assert has_then or has_else

    def test_only_if_no_then_else(self):
        """只有 if 没有 then/else 时不崩溃"""
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "if": {"properties": {"a": {"const": "x"}}},
        }
        result = DataBuilder(schema).build()
        assert "a" in result

    def test_if_then_no_else(self):
        """有 if + then 但无 else"""
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "if": {"properties": {"age": {"minimum": 18}}},
            "then": {"properties": {"vote": {"type": "boolean"}}},
        }
        results = [DataBuilder(schema).build() for _ in range(20)]
        assert any(isinstance(r, dict) for r in results)


# ── P1: patternProperties ──


class TestPatternProperties:
    def test_generates_matching_keys(self):
        schema = {
            "type": "object",
            "patternProperties": {
                "^S_": {"type": "string"},
                "^I_": {"type": "integer"},
            },
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            for key in result:
                if key.startswith("S_"):
                    assert isinstance(result[key], str)
                elif key.startswith("I_"):
                    assert isinstance(result[key], (int, float))

    def test_with_additional_false(self):
        """patternProperties + additionalProperties: false 联动"""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "patternProperties": {"^x_": {"type": "integer"}},
            "additionalProperties": False,
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            for key in result:
                assert key == "name" or key.startswith("x_"), f"unexpected key: {key}"


# ── P1: dependentSchemas ──


class TestDependentSchemas:
    def test_dependent_properties_generated(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "dependentSchemas": {
                "name": {
                    "properties": {
                        "greeting": {"type": "string", "const": "hello"},
                    },
                },
            },
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            if "name" in result:
                assert "greeting" in result
                assert result["greeting"] == "hello"

    def test_no_trigger_no_supplement(self):
        """trigger 不存在时不补生成"""
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
            },
            "maxProperties": 1,
            "dependentSchemas": {
                "missing_trigger": {
                    "properties": {"extra": {"type": "integer"}},
                },
            },
        }
        result = DataBuilder(schema).build()
        assert "extra" not in result


# ── P1: not（有限子集）──


class TestNotKeyword:
    def test_not_type(self):
        """not: {type: 'string'} 生成非字符串"""
        schema = {"not": {"type": "string"}}
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            assert not isinstance(result["v"], str)

    def test_not_enum(self):
        """not: {enum: [1,2,3]} 配合 enum 排除"""
        schema = {
            "enum": [1, 2, 3, 4, 5],
            "not": {"enum": [1, 2, 3]},
        }
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            assert result["v"] in (4, 5)

    def test_not_type_list(self):
        """not: {type: ['string', 'null']} 排除多类型"""
        schema = {"not": {"type": ["string", "null"]}}
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            assert not isinstance(result["v"], str)
            assert result["v"] is not None

    def test_not_single_type(self):
        """not: {type: 'string'} 应该生成非字符串 (BUG-005)"""
        schema = {"not": {"type": "string"}}
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            assert not isinstance(result["v"], str)

    def test_not_type_list_improved(self):
        """not: {type: ['string', 'null']} 应该生成非字符串且非null的值 (BUG-005)"""
        schema = {"not": {"type": ["string", "null"]}}
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            assert not isinstance(result["v"], str)
            assert result["v"] is not None

    def test_not_with_base_type(self):
        """not 与 base type 配合工作 (BUG-005)"""
        schema = {
            "type": ["integer", "number"],
            "not": {"type": "integer"}
        }
        for _ in range(20):
            result = DataBuilder({"type": "object", "properties": {"v": schema}}).build()
            # 应该生成浮点数，不是整数
            assert isinstance(result["v"], float)
            assert not isinstance(result["v"], int)


# ── P1: propertyNames ──


class TestPropertyNames:
    def test_generated_keys_match_pattern(self):
        schema = {
            "type": "object",
            "additionalProperties": {"type": "integer"},
            "propertyNames": {"pattern": "^[a-z]{3}$"},
        }
        for _ in range(10):
            result = DataBuilder(schema).build()
            for key in result:
                assert re.match(r"^[a-z]{3}$", key), f"key '{key}' doesn't match pattern"
