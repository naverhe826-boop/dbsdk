"""StructureStrategy 高级场景补充测试：策略组合、依赖、边界"""
import pytest
from data_builder import (
    DataBuilder, BuilderConfig, FieldPolicy,
    property_count, property_selection, contains_count, schema_selection,
    array_count, fixed, range_int, enum, seq, ref,
    callable_strategy,
    CombinationMode, CombinationSpec,
)
from data_builder.exceptions import StrategyNotFoundError


# ── P1: PropertyCountStrategy + 子字段 FieldPolicy ──────────

class TestPropertyCountWithChildPolicy:
    """PropertyCountStrategy 与子字段值策略共存"""

    def test_property_count_respects_child_policy(self):
        """property_count 控制数量，子字段 FieldPolicy 控制值"""
        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "email": {"type": "string"},
                    },
                    "required": ["name"],
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("profile", property_count(2)),
            FieldPolicy("profile.name", fixed("Alice")),
            FieldPolicy("profile.age", fixed(30)),
        ])
        for _ in range(20):
            result = DataBuilder(schema, config).build()
            assert len(result["profile"]) == 2
            assert result["profile"]["name"] == "Alice"  # required + FieldPolicy
            if "age" in result["profile"]:
                assert result["profile"]["age"] == 30

    def test_property_count_all_with_child_policies(self):
        """所有属性都有 FieldPolicy 时，值全部由策略控制"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                        "b": {"type": "integer"},
                    },
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("obj", property_count(2)),
            FieldPolicy("obj.a", fixed("X")),
            FieldPolicy("obj.b", fixed(99)),
        ])
        result = DataBuilder(schema, config).build()
        assert result["obj"] == {"a": "X", "b": 99}


# ── P1: prefixItems + ArrayCountStrategy ────────────────────

class TestPrefixItemsWithArrayCount:
    """prefixItems 与 ArrayCountStrategy 组合"""

    def test_array_count_extends_prefix_items(self):
        """array_count 设置总数 > prefixItems 数量时，额外位用 items schema"""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "first"},
                    ],
                    "items": {"type": "integer", "minimum": 1, "maximum": 1},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("data", array_count(4))])
        result = DataBuilder(schema, config).build()
        assert len(result["data"]) == 4
        assert result["data"][0] == "first"
        assert all(result["data"][i] == 1 for i in range(1, 4))

    def test_array_count_less_than_prefix_items(self):
        """array_count < prefixItems 长度时，只生成 count 个 prefixItems 元素"""
        schema = {
            "type": "object",
            "properties": {
                "t": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "a"},
                        {"type": "string", "const": "b"},
                        {"type": "string", "const": "c"},
                    ],
                    "items": {"type": "integer"},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("t", array_count(2))])
        result = DataBuilder(schema, config).build()
        assert len(result["t"]) == 2
        assert result["t"][0] == "a"
        assert result["t"][1] == "b"

    def test_array_count_with_items_false(self):
        """array_count + items:false 时总数不超过 prefixItems"""
        schema = {
            "type": "object",
            "properties": {
                "pair": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "x"},
                        {"type": "string", "const": "y"},
                    ],
                    "items": False,
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("pair", array_count(10))])
        result = DataBuilder(schema, config).build()
        assert len(result["pair"]) == 2  # clamped to prefixItems


# ── P1: PropertySelectionStrategy + required 字段行为 ────────

class TestPropertySelectionWithRequired:
    """PropertySelectionStrategy 不自动合并 required（by design）"""

    def test_selection_without_required_omits_required(self):
        """精确选择不含 required 字段时，required 字段不出现"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "city": {"type": "string"},
                    },
                    "required": ["name"],
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("obj", property_selection(["age", "city"])),
        ])
        result = DataBuilder(schema, config).build()
        # by design: PropertySelectionStrategy 精确控制，不自动合并 required
        assert set(result["obj"].keys()) == {"age", "city"}

    def test_selection_including_required_works(self):
        """选择中包含 required 字段时正常生成"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("obj", property_selection(["name"])),
            FieldPolicy("obj.name", fixed("Bob")),
        ])
        result = DataBuilder(schema, config).build()
        assert result["obj"] == {"name": "Bob"}


# ── P2: ContainsCountStrategy vs ArrayCountStrategy 同字段 ──

class TestContainsVsArrayCountConflict:
    """同一字段绑定 ContainsCountStrategy 优先于 ArrayCountStrategy"""

    def test_contains_count_takes_priority_on_same_field(self):
        """FieldPolicy 只允许一个策略，后者覆盖前者"""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "minimum": 42, "maximum": 42},
                    "minItems": 3,
                    "maxItems": 5,
                }
            },
        }
        # 两个 FieldPolicy 绑定同路径，后者覆盖前者（dict 行为）
        config = BuilderConfig(policies=[
            FieldPolicy("items", array_count(3)),
            FieldPolicy("items", contains_count(2)),
        ])
        result = DataBuilder(schema, config).build()
        arr = result["items"]
        int_count = sum(1 for x in arr if isinstance(x, int) and x == 42)
        assert int_count == 2


# ── P2: SchemaSelectionStrategy + 嵌套 FieldPolicy ──────────

class TestSchemaSelectionWithNestedPolicy:
    """SchemaSelectionStrategy 选择分支后，嵌套 FieldPolicy 生效"""

    def test_field_policy_in_selected_branch(self):
        schema = {
            "type": "object",
            "properties": {
                "payment": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string"},
                                "card_no": {"type": "string"},
                            },
                        },
                        {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string"},
                                "account": {"type": "string"},
                            },
                        },
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("payment", schema_selection(0)),
            FieldPolicy("payment.method", fixed("card")),
            FieldPolicy("payment.card_no", fixed("1234-5678")),
        ])
        result = DataBuilder(schema, config).build()
        assert result["payment"]["method"] == "card"
        assert result["payment"]["card_no"] == "1234-5678"

    def test_dynamic_branch_with_field_policies(self):
        """动态分支选择时子字段策略仍然生效"""
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "oneOf": [
                        {"type": "object", "properties": {"tag": {"type": "string"}}},
                        {"type": "object", "properties": {"tag": {"type": "string"}}},
                    ]
                }
            },
        }
        config = BuilderConfig(
            count=2,
            policies=[
                FieldPolicy("v", schema_selection(
                    callable_strategy(lambda ctx: ctx.index % 2)
                )),
                FieldPolicy("v.tag", fixed("TAGGED")),
            ],
        )
        results = DataBuilder(schema, config).build()
        assert results[0]["v"]["tag"] == "TAGGED"
        assert results[1]["v"]["tag"] == "TAGGED"


# ── P2: StructureStrategy + CombinationSpec ──────────────────

class TestStructureWithCombination:
    """结构策略与组合生成共存"""

    def test_property_count_with_cartesian(self):
        """property_count 控制属性数量，同时字段参与笛卡尔积组合"""
        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "role": {"type": "string"},
                        "extra": {"type": "string"},
                    },
                    "required": ["level", "role"],
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("profile", property_count(2)),
                FieldPolicy("profile.level", enum(["vip", "normal"])),
                FieldPolicy("profile.role", enum(["admin", "user"])),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["profile.level", "profile.role"],
            )],
        )
        results = DataBuilder(schema, config).build()
        assert len(results) == 4  # 2×2
        for r in results:
            assert len(r["profile"]) == 2
            assert "level" in r["profile"]
            assert "role" in r["profile"]

    def test_array_count_with_combination(self):
        """array_count 控制数组长度，顶层字段参与组合"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 1, "maximum": 1},
                    "minItems": 1,
                    "maxItems": 10,
                },
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["A", "B"])),
                FieldPolicy("items", array_count(2)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.CARTESIAN,
                fields=["status"],
            )],
        )
        results = DataBuilder(schema, config).build()
        assert len(results) == 2  # 2 个 status 值
        for r in results:
            assert len(r["items"]) == 2  # array_count 生效

    def test_schema_selection_with_boundary(self):
        """schema_selection 固定分支 + 其他字段边界值组合"""
        schema = {
            "type": "object",
            "properties": {
                "mode": {
                    "oneOf": [
                        {"type": "string", "const": "fast"},
                        {"type": "string", "const": "slow"},
                    ]
                },
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
            },
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("mode", schema_selection(0)),
                FieldPolicy("score", range_int(0, 100)),
            ],
            combinations=[CombinationSpec(
                mode=CombinationMode.BOUNDARY,
                fields=["score"],
            )],
        )
        results = DataBuilder(schema, config).build()
        assert all(r["mode"] == "fast" for r in results)
        scores = [r["score"] for r in results]
        assert 0 in scores  # 边界值
        assert 100 in scores


# ── P3: StructureStrategy + strict_mode ──────────────────────

class TestStructureWithStrictMode:
    """strict_mode + StructureStrategy 组合"""

    def test_strict_mode_with_property_count(self):
        """strict_mode 时 property_count 控制的子字段无策略应抛异常"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                    },
                }
            },
        }
        config = BuilderConfig(
            strict_mode=True,
            policies=[
                FieldPolicy("obj", property_count(1)),
                # obj.a 无策略 → strict_mode 抛异常
            ],
        )
        with pytest.raises(StrategyNotFoundError):
            DataBuilder(schema, config).build()

    def test_strict_mode_with_full_policies_passes(self):
        """strict_mode 时所有字段都有策略则正常"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                        "b": {"type": "integer"},
                    },
                }
            },
        }
        config = BuilderConfig(
            strict_mode=True,
            policies=[
                FieldPolicy("obj", property_count(2)),
                FieldPolicy("obj.a", fixed("x")),
                FieldPolicy("obj.b", fixed(1)),
            ],
        )
        result = DataBuilder(schema, config).build()
        assert result["obj"] == {"a": "x", "b": 1}


# ── P3: StructureStrategy + null_probability ─────────────────

class TestStructureWithNullProbability:
    """null_probability 与结构策略"""

    def test_null_probability_on_nullable_child(self):
        """property_count 选出的子字段如果 nullable 且概率=1.0 则返回 None"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "nullable": True},
                    },
                }
            },
        }
        config = BuilderConfig(
            null_probability=1.0,
            policies=[
                FieldPolicy("obj", property_count(1)),
            ],
        )
        result = DataBuilder(schema, config).build()
        assert "name" in result["obj"]
        assert result["obj"]["name"] is None


# ── P4: RefStrategy + StructureStrategy ──────────────────────

class TestRefWithStructure:
    """RefStrategy 引用结构策略控制的字段"""

    def test_ref_field_after_property_count(self):
        """ref 引用的字段在 property_count 控制的对象内"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "copy_id": {"type": "integer"},
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("id", seq(start=100)),
            FieldPolicy("copy_id", ref("id")),
        ])
        results = DataBuilder(schema, config).build(count=3)
        for r in results:
            assert r["copy_id"] == r["id"]


# ── P4: SequenceStrategy 连续性 ──────────────────────────────

class TestSeqContinuityWithStructure:
    """seq 策略在结构策略控制下保持连续性"""

    def test_seq_in_array_count_controlled_array(self):
        """array_count 固定数组长度，seq 仍然连续递增"""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                    },
                    "minItems": 1,
                    "maxItems": 10,
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("items", array_count(3)),
            FieldPolicy("items[*].id", seq(start=1, prefix="ID-", padding=3)),
        ])
        result = DataBuilder(schema, config).build()
        assert len(result["items"]) == 3
        assert result["items"][0]["id"] == "ID-001"
        assert result["items"][1]["id"] == "ID-002"
        assert result["items"][2]["id"] == "ID-003"


# ── P4: prefixItems + uniqueItems ────────────────────────────

class TestPrefixItemsWithUniqueItems:
    """prefixItems + uniqueItems 组合"""

    def test_prefix_items_unique(self):
        """uniqueItems + prefixItems 时 prefixItems 的不同位置值不同即可"""
        schema = {
            "type": "object",
            "properties": {
                "t": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "a"},
                        {"type": "string", "const": "b"},
                    ],
                    "items": False,
                    "uniqueItems": True,
                }
            },
        }
        result = DataBuilder(schema).build()
        arr = result["t"]
        assert len(arr) == len(set(arr))


# ── P4: FieldPolicy 指向 prefixItems 位置 ───────────────────

class TestFieldPolicyOnPrefixItemsPositions:
    """FieldPolicy 可控制 prefixItems 位置的值"""

    def test_policy_on_array_index(self):
        """通过 [*] 通配符控制 prefixItems 各位置元素的子字段"""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "object", "properties": {"val": {"type": "integer"}}},
                        {"type": "object", "properties": {"val": {"type": "integer"}}},
                    ],
                    "items": False,
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("data[*].val", fixed(42)),
        ])
        result = DataBuilder(schema, config).build()
        for item in result["data"]:
            assert item["val"] == 42


# ── P4: 批量生成 + StructureStrategy ────────────────────────

class TestBulkWithStructureStrategy:
    """大批量生成时结构策略稳定性"""

    def test_bulk_property_count(self):
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "minimum": 1, "maximum": 1},
                        "b": {"type": "integer", "minimum": 2, "maximum": 2},
                        "c": {"type": "integer", "minimum": 3, "maximum": 3},
                    },
                    "required": ["a"],
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("obj", property_count(2))])
        results = DataBuilder(schema, config).build(count=500)
        assert len(results) == 500
        for r in results:
            assert len(r["obj"]) == 2
            assert "a" in r["obj"]

    def test_bulk_schema_selection(self):
        schema = {
            "type": "object",
            "properties": {
                "v": {
                    "oneOf": [
                        {"type": "string", "const": "A"},
                        {"type": "string", "const": "B"},
                    ]
                }
            },
        }
        config = BuilderConfig(policies=[
            FieldPolicy("v", schema_selection(
                callable_strategy(lambda ctx: ctx.index % 2)
            )),
        ])
        results = DataBuilder(schema, config).build(count=200)
        assert len(results) == 200
        for i, r in enumerate(results):
            assert r["v"] == ("A" if i % 2 == 0 else "B")

    def test_bulk_contains_count(self):
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "integer", "minimum": 1, "maximum": 1},
                    "minItems": 3,
                    "maxItems": 5,
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("items", contains_count(2))])
        results = DataBuilder(schema, config).build(count=100)
        assert len(results) == 100
        for r in results:
            int_count = sum(1 for x in r["items"] if isinstance(x, int))
            assert int_count == 2

    def test_bulk_prefix_items(self):
        schema = {
            "type": "object",
            "properties": {
                "t": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string", "const": "H"},
                        {"type": "integer", "minimum": 1, "maximum": 1},
                    ],
                    "items": False,
                }
            },
        }
        results = DataBuilder(schema).build(count=200)
        assert len(results) == 200
        for r in results:
            assert r["t"][0] == "H"
            assert r["t"][1] == 1


# ── P4: 错误绑定类型 ────────────────────────────────────────

class TestWrongTypeBinding:
    """StructureStrategy 绑定到不匹配的类型时 fall through"""

    def test_array_count_on_string_falls_through(self):
        """array_count 绑定到 string 字段时走默认生成"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("name", array_count(5))])
        result = DataBuilder(schema, config).build()
        assert isinstance(result["name"], str)

    def test_property_count_on_array_uses_as_structure_count(self):
        """property_count 绑定到 array 字段时作为 StructureStrategy 控制数量"""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 10,
                },
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("tags", property_count(3))])
        result = DataBuilder(schema, config).build()
        # property_count 是 StructureStrategy 子类，绑定到 array 时走 _generate_array
        assert len(result["tags"]) == 3

    def test_contains_count_on_object_generates_default(self):
        """contains_count 绑定到 object 字段时走 _generate_object 默认逻辑"""
        schema = {
            "type": "object",
            "properties": {
                "obj": {
                    "type": "object",
                    "properties": {"x": {"type": "integer", "minimum": 1, "maximum": 1}},
                }
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("obj", contains_count(2))])
        result = DataBuilder(schema, config).build()
        assert "x" in result["obj"]
