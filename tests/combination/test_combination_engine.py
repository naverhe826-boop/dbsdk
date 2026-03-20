"""CombinationEngine 各模式测试"""

import itertools

from data_builder.combinations import (
    CombinationEngine,
    CombinationMode,
    CombinationSpec,
    Constraint,
)


def _engine():
    return CombinationEngine()


# ── 笛卡尔积 ──────────────────────────────────────────────────


class TestCartesian:
    def test_basic(self):
        domains = {"a": [1, 2], "b": ["x", "y"]}
        spec = CombinationSpec(mode=CombinationMode.CARTESIAN)
        rows = _engine().generate(domains, spec)
        assert len(rows) == 4
        pairs = {(r["a"], r["b"]) for r in rows}
        assert pairs == {(1, "x"), (1, "y"), (2, "x"), (2, "y")}

    def test_single_field(self):
        domains = {"a": [1, 2, 3]}
        spec = CombinationSpec(mode=CombinationMode.CARTESIAN)
        rows = _engine().generate(domains, spec)
        assert len(rows) == 3
        assert [r["a"] for r in rows] == [1, 2, 3]

    def test_three_fields(self):
        domains = {"a": [1, 2], "b": ["x", "y"], "c": [True, False]}
        spec = CombinationSpec(mode=CombinationMode.CARTESIAN)
        rows = _engine().generate(domains, spec)
        assert len(rows) == 8

    def test_empty_domains(self):
        rows = _engine().generate({}, CombinationSpec(mode=CombinationMode.CARTESIAN))
        assert rows == []


# ── 成对组合 ──────────────────────────────────────────────────


class TestPairwise:
    def test_covers_all_pairs(self):
        domains = {"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [True, False]}
        spec = CombinationSpec(mode=CombinationMode.PAIRWISE)
        rows = _engine().generate(domains, spec)

        # 行数应少于全组合 3*3*2=18
        assert len(rows) < 18

        # 验证所有二元组都被覆盖
        keys = list(domains.keys())
        for i, j in itertools.combinations(range(len(keys)), 2):
            ki, kj = keys[i], keys[j]
            covered = {(r[ki], r[kj]) for r in rows}
            expected = set(itertools.product(domains[ki], domains[kj]))
            assert covered == expected, f"pair ({ki},{kj}) not fully covered"

    def test_two_fields_equals_cartesian(self):
        """两字段的 pairwise 等价于笛卡尔积"""
        domains = {"a": [1, 2], "b": ["x", "y"]}
        spec = CombinationSpec(mode=CombinationMode.PAIRWISE)
        rows = _engine().generate(domains, spec)
        pairs = {(r["a"], r["b"]) for r in rows}
        assert pairs == {(1, "x"), (1, "y"), (2, "x"), (2, "y")}

    def test_single_field(self):
        domains = {"a": [1, 2, 3]}
        spec = CombinationSpec(mode=CombinationMode.PAIRWISE)
        rows = _engine().generate(domains, spec)
        assert {r["a"] for r in rows} == {1, 2, 3}


# ── 正交数组 (t-way) ──────────────────────────────────────────


class TestOrthogonal:
    def test_strength_3(self):
        """strength=3 时应覆盖所有三元组"""
        domains = {"a": [1, 2], "b": ["x", "y"], "c": [True, False], "d": [0, 1]}
        spec = CombinationSpec(mode=CombinationMode.ORTHOGONAL, strength=3)
        rows = _engine().generate(domains, spec)

        keys = list(domains.keys())
        for combo_keys in itertools.combinations(range(len(keys)), 3):
            ks = [keys[i] for i in combo_keys]
            covered = {tuple(r[k] for k in ks) for r in rows}
            expected = set(itertools.product(*(domains[k] for k in ks)))
            assert covered == expected

    def test_strength_exceeds_fields(self):
        """strength 大于字段数时退化为全组合"""
        domains = {"a": [1, 2], "b": ["x", "y"]}
        spec = CombinationSpec(mode=CombinationMode.ORTHOGONAL, strength=5)
        rows = _engine().generate(domains, spec)
        pairs = {(r["a"], r["b"]) for r in rows}
        assert pairs == {(1, "x"), (1, "y"), (2, "x"), (2, "y")}


# ── 约束过滤 ──────────────────────────────────────────────────


class TestConstraints:
    def test_single_constraint(self):
        domains = {"a": [1, 2, 3], "b": ["x", "y"]}
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=[
                Constraint(predicate=lambda r: r["a"] != 2, description="排除 a=2"),
            ],
        )
        rows = _engine().generate(domains, spec)
        assert all(r["a"] != 2 for r in rows)
        assert len(rows) == 4  # 6 - 2

    def test_multiple_constraints(self):
        domains = {"a": [1, 2, 3], "b": [10, 20]}
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=[
                Constraint(predicate=lambda r: r["a"] > 1),
                Constraint(predicate=lambda r: r["b"] == 20),
            ],
        )
        rows = _engine().generate(domains, spec)
        assert all(r["a"] > 1 and r["b"] == 20 for r in rows)
        assert len(rows) == 2

    def test_all_filtered_returns_empty(self):
        domains = {"a": [1]}
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=[Constraint(predicate=lambda r: False)],
        )
        rows = _engine().generate(domains, spec)
        assert rows == []


# ── 等价类 / 边界值模式（值域由调用方传入，引擎做笛卡尔积）───


class TestEquivalenceAndBoundary:
    def test_equivalence_mode_is_cartesian(self):
        domains = {"a": [0, 50, 100], "b": ["low", "high"]}
        spec = CombinationSpec(mode=CombinationMode.EQUIVALENCE)
        rows = _engine().generate(domains, spec)
        assert len(rows) == 6

    def test_boundary_mode_is_cartesian(self):
        domains = {"a": [1, 2, 99, 100], "b": ["x", "y"]}
        spec = CombinationSpec(mode=CombinationMode.BOUNDARY)
        rows = _engine().generate(domains, spec)
        assert len(rows) == 8
