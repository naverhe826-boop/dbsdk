"""SchemaAwareStrategy 测试"""

import pytest

from data_builder import SchemaAwareStrategy, StrategyContext


def _ctx(**kwargs):
    defaults = dict(field_path="x", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestSchemaAwareGenerate:
    def test_generate_raises(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 0, "maximum": 100})
        with pytest.raises(NotImplementedError):
            s.generate(_ctx())


# ── integer ───────────────────────────────────────────────────


class TestSchemaAwareInteger:
    def test_boundary(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 0, "maximum": 100})
        assert s.boundary_values() == [0, 1, 99, 100]

    def test_boundary_small_range(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 5, "maximum": 6})
        assert s.boundary_values() == [5, 6]

    def test_boundary_single(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 3, "maximum": 3})
        assert s.boundary_values() == [3]

    def test_equivalence(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 0, "maximum": 100})
        assert s.equivalence_classes() == [[0], [50], [100]]

    def test_invalid(self):
        s = SchemaAwareStrategy({"type": "integer", "minimum": 0, "maximum": 100})
        inv = s.invalid_values()
        assert inv == [-1, 101, "not_int", 3.14, None]

    def test_default_range(self):
        """无 minimum/maximum 时使用默认 0-100"""
        s = SchemaAwareStrategy({"type": "integer"})
        assert s.boundary_values() == [0, 1, 99, 100]


# ── number ────────────────────────────────────────────────────


class TestSchemaAwareNumber:
    def test_boundary(self):
        s = SchemaAwareStrategy({"type": "number", "minimum": 0.0, "maximum": 1.0})
        bv = s.boundary_values()
        assert bv[0] == 0.0
        assert bv[1] == 0.01
        assert bv[-1] == 1.0

    def test_equivalence(self):
        s = SchemaAwareStrategy({"type": "number", "minimum": 0.0, "maximum": 10.0})
        classes = s.equivalence_classes()
        assert classes == [[0.0], [5.0], [10.0]]

    def test_invalid(self):
        s = SchemaAwareStrategy({"type": "number", "minimum": 0.0, "maximum": 1.0})
        inv = s.invalid_values()
        assert inv[0] == -0.01
        assert inv[1] == 1.01
        assert inv[2] == "not_number"
        assert inv[3] is None


# ── string ────────────────────────────────────────────────────


class TestSchemaAwareString:
    def test_boundary_min_zero(self):
        s = SchemaAwareStrategy({"type": "string", "minLength": 0, "maxLength": 10})
        bv = s.boundary_values()
        assert bv[0] == ""
        assert len(bv[-1]) == 10

    def test_boundary_min_positive(self):
        s = SchemaAwareStrategy({"type": "string", "minLength": 3, "maxLength": 10})
        bv = s.boundary_values()
        assert len(bv[0]) == 3
        assert len(bv[-1]) == 10

    def test_equivalence_min_zero(self):
        s = SchemaAwareStrategy({"type": "string", "minLength": 0, "maxLength": 10})
        classes = s.equivalence_classes()
        assert len(classes) == 3
        assert classes[0] == [""]
        assert len(classes[1][0]) == 5  # mid
        assert len(classes[2][0]) == 10

    def test_equivalence_min_positive(self):
        s = SchemaAwareStrategy({"type": "string", "minLength": 4, "maxLength": 10})
        classes = s.equivalence_classes()
        assert len(classes[0][0]) == 4
        assert len(classes[1][0]) == 7  # (4+10)//2
        assert len(classes[2][0]) == 10

    def test_invalid_min_positive(self):
        s = SchemaAwareStrategy({"type": "string", "minLength": 3, "maxLength": 10})
        inv = s.invalid_values()
        assert len(inv[0]) == 2  # minLength - 1
        assert len(inv[1]) == 20  # maxLength + 10
        assert inv[2] == 12345
        assert inv[3] is None

    def test_invalid_min_zero(self):
        """minLength=0 时跳过 '比 minLen 短' 的值"""
        s = SchemaAwareStrategy({"type": "string", "minLength": 0, "maxLength": 10})
        inv = s.invalid_values()
        # 无 "比 0 短" 的值，所以 3 项
        assert len(inv) == 3
        assert inv[-1] is None


# ── boolean ───────────────────────────────────────────────────


class TestSchemaAwareBoolean:
    def test_boundary(self):
        s = SchemaAwareStrategy({"type": "boolean"})
        assert s.boundary_values() == [True, False]

    def test_equivalence(self):
        s = SchemaAwareStrategy({"type": "boolean"})
        assert s.equivalence_classes() == [[True], [False]]

    def test_invalid(self):
        s = SchemaAwareStrategy({"type": "boolean"})
        assert s.invalid_values() == ["not_bool", 0, None]


# ── 不支持的类型 ──────────────────────────────────────────────


class TestSchemaAwareUnsupported:
    def test_array_returns_none(self):
        s = SchemaAwareStrategy({"type": "array"})
        assert s.boundary_values() is None
        assert s.equivalence_classes() is None
        assert s.invalid_values() is None

    def test_object_returns_none(self):
        s = SchemaAwareStrategy({"type": "object"})
        assert s.boundary_values() is None
