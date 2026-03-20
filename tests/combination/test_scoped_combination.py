"""测试分层组合模式（Scoped Combination）"""
import pytest
from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    CombinationSpec,
    CombinationMode,
    enum,
)


class TestScopedCombination:
    def test_root_pairwise_nested_cartesian(self):
        """顶层 PAIRWISE + 嵌套 CARTESIAN"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "priority": {"type": "integer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "region": {"type": "string"}
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("priority", enum([1, 2, 3])),
                FieldPolicy("user.level", enum(["vip", "normal"])),
                FieldPolicy("user.region", enum(["cn", "us"])),
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.PAIRWISE, scope=None),
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope="user"),
            ],
        )
        results = DataBuilder(schema, config).build()

        # 顶层 PAIRWISE：status(2) × priority(3) 覆盖所有对 ≈ 3 行
        # 嵌套 CARTESIAN：user.level(2) × user.region(2) = 4 行
        # 跨组笛卡尔积：3 × 4 = 12 行
        assert len(results) >= 12  # PAIRWISE 可能生成更多行

        # 验证数据结构
        for item in results:
            assert item["status"] in ["active", "inactive"]
            assert item["priority"] in [1, 2, 3]
            assert item["user"]["level"] in ["vip", "normal"]
            assert item["user"]["region"] in ["cn", "us"]

        # 验证嵌套字段是笛卡尔积（所有组合都应出现）
        user_combos = set()
        for item in results:
            user_combos.add((item["user"]["level"], item["user"]["region"]))
        assert len(user_combos) == 4  # 2 × 2

    def test_multi_level_scopes(self):
        """多层嵌套不同 scope"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {
                    "type": "object",
                    "properties": {
                        "db": {
                            "type": "object",
                            "properties": {
                                "host": {"type": "string"},
                                "port": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["on", "off"])),
                FieldPolicy("config.db.host", enum(["localhost", "remote"])),
                FieldPolicy("config.db.port", enum([3306, 5432])),
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope=None),
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope="config.db"),
            ],
        )
        results = DataBuilder(schema, config).build()

        # status(2) × [config.db 笛卡尔积(2×2)] = 2 × 4 = 8
        assert len(results) == 8

        # 验证所有组合
        combos = set()
        for item in results:
            combos.add((
                item["status"],
                item["config"]["db"]["host"],
                item["config"]["db"]["port"]
            ))
        assert len(combos) == 8

    def test_single_spec_backward_compatible(self):
        """单个 CombinationSpec"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "priority": {"type": "integer"},
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("priority", enum([1, 2])),
            ],
            combinations=[CombinationSpec(mode=CombinationMode.CARTESIAN)],
        )
        results = DataBuilder(schema, config).build()

        # 笛卡尔积：2 × 2 = 4
        assert len(results) == 4

    def test_scope_none_matches_top_level_only(self):
        """scope=None 只匹配顶层字段（多 spec 场景）"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["a", "b"])),
                FieldPolicy("user.level", enum(["1", "2"])),
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope=None),
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope="user"),  # 添加第二个 spec
            ],
        )
        results = DataBuilder(schema, config).build()

        # 顶层 status(2) × 嵌套 user.level(2) = 4
        # 但 scope=None 只匹配 status，scope="user" 匹配 user.level
        # 实际：status(2) × user.level(2) = 4
        assert len(results) == 4
        statuses = [r["status"] for r in results]
        assert set(statuses) == {"a", "b"}
        levels = [r["user"]["level"] for r in results]
        assert set(levels) == {"1", "2"}

    def test_explicit_fields_override_scope(self):
        """显式 fields 覆盖 scope 自动选择"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "priority": {"type": "integer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "region": {"type": "string"},
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["a", "b"])),
                FieldPolicy("priority", enum([1, 2])),
                FieldPolicy("user.level", enum(["vip", "normal"])),
                FieldPolicy("user.region", enum(["cn", "us"])),
            ],
            combinations=[
                CombinationSpec(
                    mode=CombinationMode.CARTESIAN,
                    scope="user",
                    fields=["user.level"]  # 只选 level，忽略 region
                ),
            ],
        )
        results = DataBuilder(schema, config).build()

        # 只有 user.level 参与组合（2 个值）
        assert len(results) == 2
        levels = [r["user"]["level"] for r in results]
        assert set(levels) == {"vip", "normal"}

    def test_boundary_mode_with_scope(self):
        """边界值模式 + scope"""
        from data_builder import range_int

        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "integer"},
                        "retries": {"type": "integer"},
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["on", "off"])),
                FieldPolicy("config.timeout", range_int(1, 10)),
                FieldPolicy("config.retries", range_int(0, 3)),
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope=None),
                CombinationSpec(mode=CombinationMode.BOUNDARY, scope="config"),
            ],
        )
        results = DataBuilder(schema, config).build()

        # status(2) × [config 边界值组合]
        # timeout 边界：[1, 2, 9, 10]，retries 边界：[0, 1, 2, 3]
        # 边界组合：4 × 4 = 16
        # 总计：2 × 16 = 32
        assert len(results) == 32

        # 验证边界值
        timeouts = set(r["config"]["timeout"] for r in results)
        retries = set(r["config"]["retries"] for r in results)
        assert timeouts == {1, 2, 9, 10}
        assert retries == {0, 1, 2, 3}

    def test_empty_scope_group(self):
        """某个 scope 没有匹配字段"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["a", "b"])),
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope=None),
                CombinationSpec(mode=CombinationMode.CARTESIAN, scope="user"),  # 无匹配字段
            ],
        )
        results = DataBuilder(schema, config).build()

        # user scope 无字段，只有顶层 status 参与
        assert len(results) == 2
