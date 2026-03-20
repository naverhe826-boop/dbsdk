import pytest
from data_builder import DataBuilder, BuilderConfig, fixed


class TestExampleKeyword:
    """schema example / examples 关键字支持"""

    def _build(self, props, count=1):
        schema = {"type": "object", "properties": props}
        results = DataBuilder(schema, BuilderConfig()).build(count=count)
        return results if count > 1 else results[0]

    # ------------------------------------------------------------------
    # example 单值
    # ------------------------------------------------------------------

    def test_example_string_fixed(self):
        result = self._build({"code": {"type": "string", "example": "CN"}})
        assert result["code"] == "CN"

    def test_example_integer_fixed(self):
        result = self._build({"level": {"type": "integer", "example": 42}})
        assert result["level"] == 42

    def test_example_number_fixed(self):
        result = self._build({"price": {"type": "number", "example": 9.99}})
        assert result["price"] == 9.99

    def test_example_boolean_fixed(self):
        result = self._build({"active": {"type": "boolean", "example": True}})
        assert result["active"] is True

    def test_example_null_fixed(self):
        result = self._build({"deleted_at": {"type": "null", "example": None}})
        assert result["deleted_at"] is None

    # ------------------------------------------------------------------
    # examples 数组
    # ------------------------------------------------------------------

    def test_examples_value_in_list(self):
        allowed = [1, 2, 3]
        results = self._build({"level": {"type": "integer", "examples": allowed}}, count=30)
        for r in results:
            assert r["level"] in allowed

    def test_examples_covers_all_values(self):
        """多次生成后应能覆盖到 examples 中的所有值"""
        allowed = {"a", "b", "c"}
        results = self._build({"tag": {"type": "string", "examples": ["a", "b", "c"]}}, count=100)
        seen = {r["tag"] for r in results}
        assert seen == allowed

    def test_examples_empty_list_falls_through(self):
        """examples 为空列表时退回到类型兜底逻辑（生成随机字符串）"""
        result = self._build({"name": {"type": "string", "examples": []}})
        assert isinstance(result["name"], str)

    def test_examples_non_list_falls_through(self):
        """examples 不是 list 时退回到类型兜底逻辑"""
        result = self._build({"name": {"type": "string", "examples": "oops"}})
        assert isinstance(result["name"], str)

    # ------------------------------------------------------------------
    # 优先级
    # ------------------------------------------------------------------

    def test_enum_takes_priority_over_examples(self):
        """enum 优先级 > examples"""
        result = self._build({
            "status": {"type": "string", "enum": ["ok"], "examples": ["fail"]}
        })
        assert result["status"] == "ok"

    def test_const_takes_priority_over_examples(self):
        """const 优先级 > examples"""
        result = self._build({
            "ver": {"type": "string", "const": "v1", "examples": ["v2", "v3"]}
        })
        assert result["ver"] == "v1"

    def test_default_takes_priority_over_examples(self):
        """default 优先级 > examples"""
        result = self._build({
            "flag": {"type": "string", "default": "yes", "examples": ["no"]}
        })
        assert result["flag"] == "yes"

    def test_examples_takes_priority_over_example(self):
        """examples 优先级 > example"""
        allowed = [10, 20, 30]
        results = self._build({
            "n": {"type": "integer", "examples": allowed, "example": 99}
        }, count=30)
        for r in results:
            assert r["n"] in allowed

    def test_example_takes_priority_over_type_fallback(self):
        """无 enum/const/default/examples 时，example 优先于类型兜底"""
        result = self._build({"code": {"type": "string", "example": "ZZ"}})
        assert result["code"] == "ZZ"

    # ------------------------------------------------------------------
    # FieldPolicy 覆盖
    # ------------------------------------------------------------------

    def test_field_policy_overrides_example(self):
        """显式 FieldPolicy 应覆盖 example，不走 example 路径"""
        from data_builder import FieldPolicy
        schema = {"type": "object", "properties": {
            "code": {"type": "string", "example": "CN"}
        }}
        config = BuilderConfig(policies=[FieldPolicy("code", fixed("US"))])
        result = DataBuilder(schema, config).build()
        assert result["code"] == "US"

    # ------------------------------------------------------------------
    # 无 example 字段走正常兜底
    # ------------------------------------------------------------------

    def test_no_example_falls_through_to_type(self):
        result = self._build({"name": {"type": "string"}})
        assert isinstance(result["name"], str)
        assert len(result["name"]) >= 1

    # ------------------------------------------------------------------
    # 混合场景
    # ------------------------------------------------------------------

    def test_mixed_fields(self):
        """部分字段有 example，部分没有，各自独立生效"""
        results = self._build({
            "code": {"type": "string", "example": "CN"},
            "level": {"type": "integer", "examples": [1, 2, 3]},
            "name": {"type": "string"},
        }, count=10)
        for r in results:
            assert r["code"] == "CN"
            assert r["level"] in [1, 2, 3]
            assert isinstance(r["name"], str)

    # ------------------------------------------------------------------
    # example 验证 (BUG-009)
    # ------------------------------------------------------------------

    def test_invalid_example_with_warning(self):
        """不符合 schema 的 example 应该触发警告但仍被使用 (BUG-009)"""
        import warnings
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "example": 5  # 小于 minimum
                }
            }
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self._build({"value": {"type": "integer", "minimum": 10, "maximum": 100, "example": 5}})
            # 应该仍然使用 example 值（向后兼容），但触发警告
            assert result["value"] == 5
            assert any("可能不符合 schema 约束" in str(warning.message) for warning in w)

    def test_valid_example_accepted(self):
        """符合 schema 的 example 应该直接使用 (BUG-009)"""
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "example": 50
                }
            }
        }
        result = self._build({"value": {"type": "integer", "minimum": 10, "maximum": 100, "example": 50}})
        assert result["value"] == 50
