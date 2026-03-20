"""组合模式与 DataBuilder 集成测试"""

from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    CombinationMode,
    CombinationSpec,
    Constraint,
    FixedStrategy,
    EnumStrategy,
    RangeStrategy,
    deduplicate,
    constraint_filter,
    limit,
    fixed,
    enum,
    range_int,
    range_float,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "method": {"type": "string"},
        "currency": {"type": "string"},
        "amount": {"type": "integer"},
        "note": {"type": "string"},
    },
}


# ── 无 combination 时行为不变 ──────────────────────────────────


class TestNoCombination:
    def test_single_object(self):
        config = BuilderConfig(policies=[FieldPolicy("method", fixed("card"))])
        result = DataBuilder(SCHEMA, config).build()
        assert isinstance(result, dict)
        assert result["method"] == "card"

    def test_count_returns_list(self):
        config = BuilderConfig(policies=[FieldPolicy("method", fixed("card"))])
        results = DataBuilder(SCHEMA, config).build(count=3)
        assert len(results) == 3

    def test_random_mode_is_noop(self):
        """CombinationMode.RANDOM 应走原逻辑"""
        config = BuilderConfig(
            policies=[FieldPolicy("method", fixed("card"))],
            combinations=[CombinationSpec(mode=CombinationMode.RANDOM)],
        )
        result = DataBuilder(SCHEMA, config).build()
        assert isinstance(result, dict)
        assert result["method"] == "card"


# ── 笛卡尔积集成 ──────────────────────────────────────────────


class TestCartesianIntegration:
    def test_basic_cartesian(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["alipay", "wechat"])),
                FieldPolicy("currency", enum(["CNY", "USD"])),
                FieldPolicy("amount", fixed(100)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["method", "currency"],
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) == 4
        pairs = {(r["method"], r["currency"]) for r in results}
        assert pairs == {
            ("alipay", "CNY"), ("alipay", "USD"),
            ("wechat", "CNY"), ("wechat", "USD"),
        }
        # 非组合字段 amount 应由 fixed 策略生成
        assert all(r["amount"] == 100 for r in results)

    def test_auto_fields(self):
        """fields=None 时自动选取所有可枚举字段"""
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b"])),
                FieldPolicy("currency", enum(["X", "Y"])),
                FieldPolicy("amount", fixed(1)),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build()
        # method(2) * currency(2) * amount(1) = 4
        assert len(results) == 4

    def test_non_enumerable_fields_excluded(self):
        """不可枚举字段（values()=None）不参与组合"""
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b"])),
                FieldPolicy("amount", range_float(0.0, 100.0)),  # values()=None
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build()
        # 只有 method 可枚举
        assert len(results) == 2


# ── 成对组合集成 ──────────────────────────────────────────────


class TestPairwiseIntegration:
    def test_pairwise_all_pairs_covered(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["alipay", "wechat", "card"])),
                FieldPolicy("currency", enum(["CNY", "USD", "EUR"])),
                FieldPolicy("amount", enum([100, 200])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.PAIRWISE)],
        )
        results = DataBuilder(SCHEMA, config).build()
        # 验证 method×currency 对全覆盖
        mc_pairs = {(r["method"], r["currency"]) for r in results}
        assert mc_pairs == set(
            (m, c) for m in ["alipay", "wechat", "card"] for c in ["CNY", "USD", "EUR"]
        )
        # 行数应远小于全组合 3*3*2=18
        assert len(results) < 18


# ── 边界值集成 ────────────────────────────────────────────────


class TestBoundaryIntegration:
    def test_boundary_values_used(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("amount", range_int(1, 100)),
                FieldPolicy("method", enum(["a", "b"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.BOUNDARY, fields=["amount", "method"])],
        )
        results = DataBuilder(SCHEMA, config).build()
        amounts = {r["amount"] for r in results}
        # range_int(1,100) 的边界值：1, 2, 99, 100
        assert amounts == {1, 2, 99, 100}
        methods = {r["method"] for r in results}
        assert methods == {"a", "b"}
        # 4 * 2 = 8
        assert len(results) == 8


# ── 等价类集成 ────────────────────────────────────────────────


class TestEquivalenceIntegration:
    def test_equivalence_representatives(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("amount", range_int(0, 100)),
                FieldPolicy("method", enum(["a", "b"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.EQUIVALENCE, fields=["amount", "method"])],
        )
        results = DataBuilder(SCHEMA, config).build()
        amounts = {r["amount"] for r in results}
        # 等价类代表值：0, 50, 100
        assert amounts == {0, 50, 100}
        # 3 * 2 = 6
        assert len(results) == 6


# ── count 控制 ────────────────────────────────────────────────


class TestCombinationCount:
    def test_count_less_than_total(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b", "c"])),
                FieldPolicy("currency", enum(["X", "Y", "Z"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build(count=3)
        assert len(results) == 3

    def test_count_greater_than_total(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build(count=5)
        assert len(results) == 5
        assert all(r["method"] in ("a", "b") for r in results)

    def test_count_none_returns_all(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b"])),
                FieldPolicy("currency", enum(["X", "Y"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) == 4


# ── 约束集成 ──────────────────────────────────────────────────


class TestConstraintIntegration:
    def test_constraint_filters_rows(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["alipay", "wechat", "card"])),
                FieldPolicy("currency", enum(["CNY", "USD"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                constraints=[
                    Constraint(
                        predicate=lambda r: not (r["method"] == "card" and r["currency"] == "CNY")
                    ),
                ],
            )],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) == 5
        assert not any(r["method"] == "card" and r["currency"] == "CNY" for r in results)


# ── 后置过滤集成 ──────────────────────────────────────────────


class TestPostFilters:
    def test_limit_filter(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b", "c"])),
                FieldPolicy("currency", enum(["X", "Y"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
            post_filters=[limit(3)],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) == 3

    def test_constraint_filter_post(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b", "c"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
            post_filters=[constraint_filter(lambda r: r["method"] != "b")],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert all(r["method"] != "b" for r in results)
        assert len(results) == 2

    def test_deduplicate_filter(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "a", "b"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
            post_filters=[deduplicate(["method"])],
        )
        results = DataBuilder(SCHEMA, config).build()
        methods = [r["method"] for r in results]
        assert methods == ["a", "b"]

    def test_chained_filters(self):
        config = BuilderConfig(
            policies=[
                FieldPolicy("method", enum(["a", "b", "c", "d"])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
            post_filters=[
                constraint_filter(lambda r: r["method"] != "a"),
                limit(2),
            ],
        )
        results = DataBuilder(SCHEMA, config).build()
        assert len(results) == 2
        assert all(r["method"] != "a" for r in results)

    def test_post_filters_on_random_mode(self):
        """非组合模式也支持后置过滤"""
        config = BuilderConfig(
            policies=[FieldPolicy("amount", fixed(99))],
            post_filters=[limit(2)],
        )
        results = DataBuilder(SCHEMA, config).build(count=5)
        assert len(results) == 2


# ── 嵌套 schema 集成 ──────────────────────────────────────────


class TestNestedCombination:
    def test_nested_field_override(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "status": {"type": "string"},
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("user.level", enum(["vip", "normal"])),
                FieldPolicy("status", enum(["active", "inactive"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["user.level", "status"]
            )],
        )
        results = DataBuilder(schema, config).build()
        assert len(results) == 4
        pairs = {(r["user"]["level"], r["status"]) for r in results}
        assert pairs == {
            ("vip", "active"), ("vip", "inactive"),
            ("normal", "active"), ("normal", "inactive"),
        }


# ── 无可枚举字段退化 ──────────────────────────────────────────


class TestFallback:
    def test_no_enumerable_fields_fallback(self):
        """所有策略都不可枚举时退化为普通生成"""
        config = BuilderConfig(
            policies=[FieldPolicy("amount", range_float(0.0, 100.0))],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(SCHEMA, config).build(count=3)
        assert len(results) == 3
        assert all(isinstance(r["amount"], float) for r in results)
