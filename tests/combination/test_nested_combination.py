"""嵌套对象组合生成测试"""

from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    CombinationMode,
    CombinationSpec,
    enum,
    range_int,
)


# ── 多层嵌套（3 层）──────────────────────────────────────────


class TestMultiLevelNesting:
    def test_three_level_nesting(self):
        """测试 3 层嵌套路径的组合生成"""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "db": {
                            "type": "object",
                            "properties": {
                                "host": {"type": "string"},
                                "port": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("config.db.host", enum(["localhost", "remote"])),
                FieldPolicy("config.db.port", enum([3306, 5432])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["config.db.host", "config.db.port"]
            )],
        )
        results = DataBuilder(schema, config).build()

        assert len(results) == 4
        pairs = {(r["config"]["db"]["host"], r["config"]["db"]["port"]) for r in results}
        assert pairs == {
            ("localhost", 3306), ("localhost", 5432),
            ("remote", 3306), ("remote", 5432),
        }


# ── 同一嵌套对象内多字段组合 ──────────────────────────────────


class TestSameObjectMultiFields:
    def test_two_fields_in_nested_object(self):
        """测试同一嵌套对象内多个字段的组合"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "region": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("user.level", enum(["vip", "normal"])),
                FieldPolicy("user.region", enum(["cn", "us"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["user.level", "user.region"]
            )],
        )
        results = DataBuilder(schema, config).build()

        assert len(results) == 4
        pairs = {(r["user"]["level"], r["user"]["region"]) for r in results}
        assert pairs == {
            ("vip", "cn"), ("vip", "us"),
            ("normal", "cn"), ("normal", "us"),
        }
        # 验证非组合字段正常生成
        assert all(isinstance(r["user"]["name"], str) and len(r["user"]["name"]) > 0 for r in results)


# ── 跨层级字段组合 ────────────────────────────────────────────


class TestCrossLevelCombination:
    def test_root_and_nested_field(self):
        """测试顶层字段与嵌套字段的组合"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "id": {"type": "integer"},
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("user.level", enum(["vip", "normal"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["status", "user.level"]
            )],
        )
        results = DataBuilder(schema, config).build()

        assert len(results) == 4
        pairs = {(r["status"], r["user"]["level"]) for r in results}
        assert pairs == {
            ("active", "vip"), ("active", "normal"),
            ("inactive", "vip"), ("inactive", "normal"),
        }
        # 验证非组合字段正常生成
        assert all(isinstance(r["user"]["id"], int) for r in results)


# ── 嵌套 + 数组混合 ───────────────────────────────────────────


class TestNestedWithArray:
    def test_nested_object_with_array_field(self):
        """测试嵌套对象包含数组字段的场景"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("user.level", enum(["vip", "normal"])),
                FieldPolicy("user.tags[*]", enum(["a", "b"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["user.level", "user.tags[0]", "user.tags[1]"]
            )],
        )
        results = DataBuilder(schema, config).build()

        # user.level (2) × user.tags[0] (2) × user.tags[1] (2) = 8
        assert len(results) == 8

        levels = {r["user"]["level"] for r in results}
        assert levels == {"vip", "normal"}

        # 验证数组元素按策略生成
        for r in results:
            assert len(r["user"]["tags"]) == 2
            assert all(tag in ("a", "b") for tag in r["user"]["tags"])


# ── 边界值模式 + 嵌套 ─────────────────────────────────────────


class TestNestedBoundaryMode:
    def test_boundary_values_in_nested_fields(self):
        """测试嵌套字段的边界值组合"""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "integer"},
                        "retries": {"type": "integer"},
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("config.timeout", range_int(1, 100)),
                FieldPolicy("config.retries", range_int(0, 5)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.BOUNDARY,
                fields=["config.timeout", "config.retries"]
            )],
        )
        results = DataBuilder(schema, config).build()

        # timeout 边界 [1,2,99,100] × retries 边界 [0,1,4,5] = 16
        assert len(results) == 16

        timeout_values = {r["config"]["timeout"] for r in results}
        assert timeout_values == {1, 2, 99, 100}

        retries_values = {r["config"]["retries"] for r in results}
        assert retries_values == {0, 1, 4, 5}

        # 验证笛卡尔积完整性
        pairs = {(r["config"]["timeout"], r["config"]["retries"]) for r in results}
        assert len(pairs) == 16


# ── 等价类模式 + 嵌套 ─────────────────────────────────────────


class TestNestedEquivalenceMode:
    def test_equivalence_classes_in_nested_fields(self):
        """测试嵌套字段的等价类组合"""
        schema = {
            "type": "object",
            "properties": {
                "settings": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "integer"},
                        "mode": {"type": "string"},
                    },
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("settings.priority", range_int(0, 100)),
                FieldPolicy("settings.mode", enum(["fast", "normal", "slow"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.EQUIVALENCE,
                fields=["settings.priority", "settings.mode"]
            )],
        )
        results = DataBuilder(schema, config).build()

        # priority 等价类 [0, 50, 100] × mode 等价类 [fast, normal, slow] = 9
        assert len(results) == 9

        priority_values = {r["settings"]["priority"] for r in results}
        assert priority_values == {0, 50, 100}

        mode_values = {r["settings"]["mode"] for r in results}
        assert mode_values == {"fast", "normal", "slow"}
