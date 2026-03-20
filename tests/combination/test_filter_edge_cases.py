"""后置过滤器过滤掉全部数据的边界场景"""
import pytest

from data_builder import DataBuilder, BuilderConfig, FieldPolicy, fixed
from data_builder.filters import constraint_filter, deduplicate, limit


class TestFilterAllRemoved:
    """所有数据被过滤掉的边界情况"""

    def _schema(self):
        return {
            "type": "object",
            "properties": {"x": {"type": "integer", "minimum": 1, "maximum": 5}},
        }

    def test_single_object_filtered_returns_none(self):
        """单对象模式，过滤掉唯一对象返回 None"""
        config = BuilderConfig(
            policies=[FieldPolicy("x", fixed(1))],
            post_filters=[constraint_filter(lambda r: r["x"] > 100)],
        )
        result = DataBuilder(self._schema(), config).build()
        assert result is None

    def test_batch_all_filtered_returns_empty_list(self):
        """批量模式，全部过滤掉返回空列表"""
        config = BuilderConfig(
            policies=[FieldPolicy("x", fixed(1))],
            post_filters=[constraint_filter(lambda r: r["x"] > 100)],
        )
        result = DataBuilder(self._schema(), config).build(count=5)
        assert result == []

    def test_limit_zero(self):
        """limit(0) 截断全部"""
        config = BuilderConfig(
            policies=[FieldPolicy("x", fixed(1))],
            post_filters=[limit(0)],
        )
        result = DataBuilder(self._schema(), config).build(count=3)
        assert result == []

    def test_deduplicate_all_same(self):
        """全部相同值去重后只剩 1 条"""
        config = BuilderConfig(
            policies=[FieldPolicy("x", fixed(42))],
            post_filters=[deduplicate(["x"])],
        )
        result = DataBuilder(self._schema(), config).build(count=5)
        assert len(result) == 1
        assert result[0]["x"] == 42

    def test_chained_filters_all_removed(self):
        """多过滤器链式全部过滤"""
        config = BuilderConfig(
            policies=[FieldPolicy("x", fixed(1))],
            post_filters=[
                deduplicate(["x"]),
                constraint_filter(lambda r: r["x"] > 100),
            ],
        )
        result = DataBuilder(self._schema(), config).build(count=5)
        assert result == []
