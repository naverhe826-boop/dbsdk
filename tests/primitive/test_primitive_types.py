import pytest
from data_builder import DataBuilder


class TestStringType:
    def test_default_random_string(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = DataBuilder(schema).build()
        assert isinstance(result["name"], str)
        assert len(result["name"]) >= 5

    def test_min_max_length(self):
        schema = {"type": "object", "properties": {
            "code": {"type": "string", "minLength": 3, "maxLength": 3}
        }}
        result = DataBuilder(schema).build()
        assert len(result["code"]) == 3

    def test_format_email(self):
        schema = {"type": "object", "properties": {
            "email": {"type": "string", "format": "email"}
        }}
        result = DataBuilder(schema).build()
        assert "@" in result["email"]

    def test_format_uri(self):
        schema = {"type": "object", "properties": {
            "url": {"type": "string", "format": "uri"}
        }}
        result = DataBuilder(schema).build()
        assert result["url"].startswith("http://") or result["url"].startswith("https://")

    def test_format_uuid(self):
        import re
        schema = {"type": "object", "properties": {
            "id": {"type": "string", "format": "uuid"}
        }}
        result = DataBuilder(schema).build()
        assert re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", result["id"])

    def test_format_date(self):
        schema = {"type": "object", "properties": {
            "date": {"type": "string", "format": "date"}
        }}
        result = DataBuilder(schema).build()
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result["date"])

    def test_format_datetime(self):
        schema = {"type": "object", "properties": {
            "ts": {"type": "string", "format": "date-time"}
        }}
        result = DataBuilder(schema).build()
        assert "T" in result["ts"]

    def test_format_time(self):
        import re
        schema = {"type": "object", "properties": {
            "t": {"type": "string", "format": "time"}
        }}
        result = DataBuilder(schema).build()
        assert re.match(r"^\d{2}:\d{2}:\d{2}$", result["t"])

    def test_format_ipv4(self):
        import re
        schema = {"type": "object", "properties": {
            "ip": {"type": "string", "format": "ipv4"}
        }}
        result = DataBuilder(schema).build()
        assert re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", result["ip"])

    def test_format_ipv6(self):
        schema = {"type": "object", "properties": {
            "ip": {"type": "string", "format": "ipv6"}
        }}
        result = DataBuilder(schema).build()
        assert ":" in result["ip"]

    def test_format_hostname(self):
        schema = {"type": "object", "properties": {
            "host": {"type": "string", "format": "hostname"}
        }}
        result = DataBuilder(schema).build()
        assert "." in result["host"]

    def test_format_idn_email(self):
        """测试 idn-email format 生成"""
        schema = {"type": "object", "properties": {
            "email": {"type": "string", "format": "idn-email"}
        }}
        for _ in range(10):
            result = DataBuilder(schema).build()
            email = result["email"]
            # 验证生成的是 IDN 邮箱格式（包含 Unicode 域名）
            assert "@" in email
            local, domain = email.rsplit("@", 1)
            # 验证域名包含 Unicode 字符（国际化域名）
            is_unicode = any(ord(c) > 127 for c in domain)
            assert is_unicode, f"Expected IDN email with Unicode domain, got: {email}"


class TestIntegerType:
    def test_default_range(self):
        schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert isinstance(result["n"], int)
            assert 0 <= result["n"] <= 100

    def test_minimum_maximum(self):
        schema = {"type": "object", "properties": {
            "n": {"type": "integer", "minimum": 10, "maximum": 20}
        }}
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert 10 <= result["n"] <= 20

    def test_exclusive_minimum(self):
        schema = {"type": "object", "properties": {
            "n": {"type": "integer", "exclusiveMinimum": 5, "maximum": 10}
        }}
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert result["n"] > 5

    def test_exclusive_maximum(self):
        schema = {"type": "object", "properties": {
            "n": {"type": "integer", "minimum": 0, "exclusiveMaximum": 5}
        }}
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert result["n"] < 5


class TestNumberType:
    def test_default_float(self):
        schema = {"type": "object", "properties": {"price": {"type": "number"}}}
        result = DataBuilder(schema).build()
        assert isinstance(result["price"], float)

    def test_minimum_maximum_boundary(self):
        schema = {"type": "object", "properties": {
            "price": {"type": "number", "minimum": 1.0, "maximum": 1.0}
        }}
        result = DataBuilder(schema).build()
        assert result["price"] == 1.0


class TestBooleanType:
    def test_only_true_or_false(self):
        schema = {"type": "object", "properties": {"flag": {"type": "boolean"}}}
        values = {DataBuilder(schema).build()["flag"] for _ in range(30)}
        assert values == {True, False}


class TestNullType:
    def test_returns_none(self):
        schema = {"type": "object", "properties": {"nothing": {"type": "null"}}}
        result = DataBuilder(schema).build()
        assert result["nothing"] is None


class TestPatternKeyword:
    def test_simple_pattern(self):
        import re
        schema = {"type": "object", "properties": {
            "code": {"type": "string", "pattern": "^[A-Z]{3}-\\d{4}$"}
        }}
        for _ in range(20):
            result = DataBuilder(schema).build()
            assert re.match(r"^[A-Z]{3}-\d{4}$", result["code"])

    def test_pattern_priority_over_format(self):
        """pattern 应优先于 format"""
        import re
        schema = {"type": "object", "properties": {
            "val": {"type": "string", "pattern": "^\\d{6}$", "format": "email"}
        }}
        result = DataBuilder(schema).build()
        assert re.match(r"^\d{6}$", result["val"])

    def test_pattern_ignores_min_max_length(self):
        """有 pattern 时不受 minLength/maxLength 影响"""
        import re
        schema = {"type": "object", "properties": {
            "pin": {"type": "string", "pattern": "^\\d{4}$", "minLength": 10}
        }}
        result = DataBuilder(schema).build()
        assert re.match(r"^\d{4}$", result["pin"])


class TestSchemaConstraints:
    def test_enum_constraint(self):
        schema = {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["a", "b", "c"]}
        }}
        for _ in range(20):
            assert DataBuilder(schema).build()["status"] in ["a", "b", "c"]

    def test_const_constraint(self):
        schema = {"type": "object", "properties": {
            "ver": {"type": "string", "const": "1.0.0"}
        }}
        assert DataBuilder(schema).build()["ver"] == "1.0.0"

    def test_default_constraint(self):
        schema = {"type": "object", "properties": {
            "lang": {"type": "string", "default": "zh"}
        }}
        assert DataBuilder(schema).build()["lang"] == "zh"


class TestMultipleOf:
    def test_integer_multiple_of(self):
        schema = {"type": "object", "properties": {
            "n": {"type": "integer", "multipleOf": 5, "minimum": 0, "maximum": 100}
        }}
        for _ in range(50):
            val = DataBuilder(schema).build()["n"]
            assert val % 5 == 0
            assert 0 <= val <= 100

    def test_integer_multiple_of_with_offset_range(self):
        """minimum 不是 multipleOf 的倍数时也能正确生成"""
        schema = {"type": "object", "properties": {
            "n": {"type": "integer", "multipleOf": 7, "minimum": 3, "maximum": 30}
        }}
        for _ in range(50):
            val = DataBuilder(schema).build()["n"]
            assert val % 7 == 0
            assert 3 <= val <= 30

    def test_number_multiple_of(self):
        schema = {"type": "object", "properties": {
            "price": {"type": "number", "multipleOf": 0.5, "minimum": 0.0, "maximum": 10.0}
        }}
        for _ in range(50):
            val = DataBuilder(schema).build()["price"]
            # 0.5 的倍数：2*val 应为整数
            assert abs(round(val / 0.5) * 0.5 - val) < 1e-9
            assert 0.0 <= val <= 10.0

    def test_number_multiple_of_integer_step(self):
        schema = {"type": "object", "properties": {
            "n": {"type": "number", "multipleOf": 3, "minimum": 1, "maximum": 15}
        }}
        for _ in range(50):
            val = DataBuilder(schema).build()["n"]
            assert abs(round(val / 3) * 3 - val) < 1e-9
            assert 1 <= val <= 15
