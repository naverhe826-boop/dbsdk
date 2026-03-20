"""INVALID 组合模式测试"""

from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    CombinationMode,
    CombinationSpec,
    range_int,
    range_float,
    enum,
    fixed,
)
from data_builder.combinations import CombinationEngine


# ── 引擎层：_one_invalid_at_a_time ───────────────────────────


class TestOneInvalidAtATime:
    def test_basic(self):
        """每行只有一个字段是非法值"""
        domains = {"a": [None, "bad"], "b": [-1, "x"]}
        normal = {"a": 1, "b": 2}
        spec = CombinationSpec(mode=CombinationMode.INVALID)
        rows = CombinationEngine().generate(domains, spec, normal_values=normal)
        # a 有 2 个非法值 + b 有 2 个 = 4 行
        assert len(rows) == 4
        # 前两行：a 是非法值，b 是正常值
        assert rows[0] == {"a": None, "b": 2}
        assert rows[1] == {"a": "bad", "b": 2}
        # 后两行：b 是非法值，a 是正常值
        assert rows[2] == {"a": 1, "b": -1}
        assert rows[3] == {"a": 1, "b": "x"}

    def test_single_field(self):
        domains = {"a": [None, -1]}
        normal = {"a": 50}
        spec = CombinationSpec(mode=CombinationMode.INVALID)
        rows = CombinationEngine().generate(domains, spec, normal_values=normal)
        assert len(rows) == 2
        assert rows[0]["a"] is None
        assert rows[1]["a"] == -1

    def test_empty_domains(self):
        spec = CombinationSpec(mode=CombinationMode.INVALID)
        rows = CombinationEngine().generate({}, spec, normal_values={})
        assert rows == []

    def test_with_constraints(self):
        """INVALID 模式也支持约束过滤"""
        from data_builder.combinations import Constraint
        domains = {"a": [None, -1, "bad"], "b": [None]}
        normal = {"a": 1, "b": 2}
        spec = CombinationSpec(
            mode=CombinationMode.INVALID,
            constraints=[Constraint(predicate=lambda r: r["a"] is not None)],
        )
        rows = CombinationEngine().generate(domains, spec, normal_values=normal)
        assert all(r["a"] is not None for r in rows)

    def test_no_normal_values_uses_none(self):
        """未提供 normal_values 时字段值为 None"""
        domains = {"a": ["bad"]}
        spec = CombinationSpec(mode=CombinationMode.INVALID)
        rows = CombinationEngine().generate(domains, spec, normal_values={})
        assert rows == [{"a": "bad"}]


# ── DataBuilder 集成：有策略字段 ──────────────────────────────


SCHEMA = {
    "type": "object",
    "properties": {
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "score": {"type": "number", "minimum": 0.0, "maximum": 100.0},
    },
}


class TestInvalidIntegration:
    def test_with_strategy_fields(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("age", range_int(0, 150)),
                FieldPolicy("score", range_float(0.0, 100.0)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID,
                fields=["age", "score"],
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        # age: 4 个非法值, score: 4 个非法值 → 8 行
        assert len(results) == 8
        # 每行都是完整对象
        assert all("age" in r and "score" in r for r in results)

    def test_one_field_invalid_others_normal(self):
        """验证轮流非法：每行最多一个字段是非法的"""
        config = BuilderConfig(
            policies=[
                FieldPolicy("age", range_int(0, 150)),
                FieldPolicy("score", range_float(0.0, 100.0)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID,
                fields=["age", "score"],
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        # 前 4 行：age 非法，score 正常
        for r in results[:4]:
            assert r["score"] == 50.0  # 等价类中间值

        # 后 4 行：score 非法，age 正常
        for r in results[4:]:
            assert r["age"] == 75  # (0+150)//2

    def test_custom_normal_values(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("age", range_int(0, 150)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID,
                fields=["age"],
                normal_values={"age": 25},
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        # 非法值行，其他字段无需检查
        assert len(results) == 4  # [-1, 151, "not_a_number", None]

    def test_with_count(self):
        config = BuilderConfig(
            policies=[FieldPolicy("age", range_int(0, 150))],
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID, fields=["age"],
            )],
        )
        results = DataBuilder(SCHEMA, config).build(count=2)
        assert len(results) == 2


# ── DataBuilder 集成：无策略字段（SchemaAware 回退）────────────


class TestInvalidSchemaAwareFallback:
    def test_schema_only_fields(self):
        """字段无策略时通过 schema 推导非法值"""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 1, "maximum": 10},
            },
        }
        config = BuilderConfig(
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID, fields=["count"],
            )],
        )
        results = DataBuilder(schema, config).build()
        # SchemaAwareStrategy integer invalid: [0, 11, "not_int", 3.14, None]
        assert len(results) == 5
        counts = [r["count"] for r in results]
        assert 0 in counts
        assert 11 in counts

    def test_mixed_strategy_and_schema(self):
        """有策略字段 + 无策略字段混合"""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 100},
                "name": {"type": "string", "minLength": 1, "maxLength": 20},
            },
        }
        config = BuilderConfig(
            policies=[FieldPolicy("age", range_int(0, 100))],
            combinations=[CombinationSpec(
                mode=CombinationMode.INVALID, fields=["age", "name"],
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) > 0
        # 每行都是完整对象
        assert all(isinstance(r, dict) for r in results)


# ── BOUNDARY/EQUIVALENCE 自动发现 schema 字段 ─────────────────


class TestAutoDiscoverSchemaFields:
    def test_boundary_auto_discover(self):
        """BOUNDARY 模式自动发现 schema 基本类型字段"""
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "minimum": 1, "maximum": 3},
                "y": {"type": "boolean"},
            },
        }
        config = BuilderConfig(
            combinations=[CombinationSpec(mode=CombinationMode.BOUNDARY)],
        )
        results = DataBuilder(schema, config).build()
        # x 边界值: [1,2,3], y 边界值: [True, False]
        assert len(results) > 0
        xs = {r["x"] for r in results}
        ys = {r["y"] for r in results}
        assert 1 in xs
        assert 3 in xs
        assert True in ys
        assert False in ys

    def test_equivalence_auto_discover(self):
        schema = {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 10},
            },
        }
        config = BuilderConfig(
            combinations=[CombinationSpec(mode=CombinationMode.EQUIVALENCE)],
        )
        results = DataBuilder(schema, config).build()
        levels = {r["level"] for r in results}
        # 等价类代表值：0, 5, 10
        assert levels == {0, 5, 10}

    def test_invalid_auto_discover(self):
        """INVALID 模式自动发现并生成非法值"""
        schema = {
            "type": "object",
            "properties": {
                "flag": {"type": "boolean"},
            },
        }
        config = BuilderConfig(
            combinations=[CombinationSpec(mode=CombinationMode.INVALID)],
        )
        results = DataBuilder(schema, config).build()
        flags = [r["flag"] for r in results]
        # boolean invalid: ["not_bool", 0, None]
        assert "not_bool" in flags
        assert 0 in flags
        assert None in flags

    def test_cartesian_no_auto_discover(self):
        """CARTESIAN 模式不自动发现 schema 字段"""
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "minimum": 0, "maximum": 10},
            },
        }
        config = BuilderConfig(
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        # 无策略字段，CARTESIAN 不自动发现 → 退化为普通生成
        results = DataBuilder(schema, config).build(count=2)
        assert len(results) == 2
