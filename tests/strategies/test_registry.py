import pytest

from data_builder import (
    StrategyRegistry, FixedStrategy, EnumStrategy, RangeStrategy,
    RandomStringStrategy, RegexStrategy, SequenceStrategy,
    FakerStrategy, CallableStrategy, RefStrategy, DateTimeStrategy,
    ArrayCountStrategy, PropertyCountStrategy, PropertySelectionStrategy,
    ContainsCountStrategy, SchemaSelectionStrategy, SchemaAwareStrategy,
    StrategyNotFoundError,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    """每个测试结束后恢复内置策略"""
    yield
    StrategyRegistry.reset()


class TestRegistryRegister:
    def test_register_and_get(self):
        StrategyRegistry.register("custom", FixedStrategy)
        assert StrategyRegistry.get("custom") is FixedStrategy

    def test_register_overwrites(self):
        StrategyRegistry.register("tmp", FixedStrategy)
        StrategyRegistry.register("tmp", EnumStrategy)
        assert StrategyRegistry.get("tmp") is EnumStrategy


class TestRegistryGet:
    def test_get_builtin(self):
        assert StrategyRegistry.get("fixed") is FixedStrategy
        assert StrategyRegistry.get("enum") is EnumStrategy

    def test_get_unknown_raises(self):
        with pytest.raises(StrategyNotFoundError):
            StrategyRegistry.get("no_such_strategy")


class TestRegistryHas:
    def test_has_builtin(self):
        assert StrategyRegistry.has("fixed")
        assert StrategyRegistry.has("range")

    def test_has_unknown(self):
        assert not StrategyRegistry.has("no_such_strategy")

    def test_has_after_register(self):
        assert not StrategyRegistry.has("my_new")
        StrategyRegistry.register("my_new", FixedStrategy)
        assert StrategyRegistry.has("my_new")


class TestRegistryBuiltins:
    """验证所有内置策略已注册"""

    @pytest.mark.parametrize("name,cls", [
        ("fixed", FixedStrategy),
        ("random_string", RandomStringStrategy),
        ("range", RangeStrategy),
        ("enum", EnumStrategy),
        ("regex", RegexStrategy),
        ("sequence", SequenceStrategy),
        ("faker", FakerStrategy),
        ("callable", CallableStrategy),
        ("ref", RefStrategy),
        ("datetime", DateTimeStrategy),
        ("array_count", ArrayCountStrategy),
        ("property_count", PropertyCountStrategy),
        ("property_selection", PropertySelectionStrategy),
        ("contains_count", ContainsCountStrategy),
        ("schema_selection", SchemaSelectionStrategy),
        ("schema_aware", SchemaAwareStrategy),
    ])
    def test_builtin_registered(self, name, cls):
        assert StrategyRegistry.get(name) is cls


class TestRegistryReset:
    def test_reset_removes_custom(self):
        StrategyRegistry.register("temp", FixedStrategy)
        assert StrategyRegistry.has("temp")
        StrategyRegistry.reset()
        assert not StrategyRegistry.has("temp")

    def test_reset_preserves_builtin(self):
        StrategyRegistry.reset()
        assert StrategyRegistry.has("fixed")
        assert StrategyRegistry.has("array_count")

    def test_isolation_between_tests_a(self):
        """注册一个临时策略（autouse fixture 会清理）"""
        StrategyRegistry.register("isolation_check", FixedStrategy)
        assert StrategyRegistry.has("isolation_check")

    def test_isolation_between_tests_b(self):
        """上一个测试注册的策略应已被清理"""
        assert not StrategyRegistry.has("isolation_check")
