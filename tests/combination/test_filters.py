"""后置过滤器测试"""

from data_builder.filters import deduplicate, constraint_filter, limit


class TestDeduplicate:
    def test_by_single_field(self):
        rows = [{"a": 1, "b": "x"}, {"a": 1, "b": "y"}, {"a": 2, "b": "z"}]
        result = deduplicate(["a"])(rows)
        assert len(result) == 2
        assert result[0] == {"a": 1, "b": "x"}
        assert result[1] == {"a": 2, "b": "z"}

    def test_by_multiple_fields(self):
        rows = [
            {"a": 1, "b": "x"},
            {"a": 1, "b": "x"},
            {"a": 1, "b": "y"},
        ]
        result = deduplicate(["a", "b"])(rows)
        assert len(result) == 2

    def test_empty_input(self):
        assert deduplicate(["a"])([]) == []

    def test_no_duplicates(self):
        rows = [{"a": 1}, {"a": 2}]
        assert deduplicate(["a"])(rows) == rows


class TestConstraintFilter:
    def test_basic(self):
        rows = [{"x": 1}, {"x": 2}, {"x": 3}]
        result = constraint_filter(lambda r: r["x"] > 1)(rows)
        assert result == [{"x": 2}, {"x": 3}]

    def test_all_pass(self):
        rows = [{"x": 1}]
        assert constraint_filter(lambda r: True)(rows) == rows

    def test_none_pass(self):
        rows = [{"x": 1}, {"x": 2}]
        assert constraint_filter(lambda r: False)(rows) == []

    def test_predicate_exception_ignored(self):
        """predicate 抛出异常的行应该被跳过 (BUG-024)"""
        rows = [
            {"value": 1},
            {"value": "invalid"},  # 这会导致 predicate 抛出异常
            {"value": 2}
        ]
        filter_fn = constraint_filter(lambda row: row["value"] > 1)
        result = filter_fn(rows)
        # 第一行会被过滤掉，第二行抛出异常被跳过，第三行保留
        assert result == [{"value": 2}]

    def test_predicate_non_bool_converted(self):
        """predicate 返回非布尔值应该被转换 (BUG-024)"""
        rows = [{"value": 0}, {"value": 1}, {"value": 2}]
        filter_fn = constraint_filter(lambda row: row["value"])
        result = filter_fn(rows)
        # 0 是假值，1 和 2 是真值
        assert len(result) == 2
        assert result == [{"value": 1}, {"value": 2}]


class TestLimit:
    def test_truncate(self):
        rows = [{"i": i} for i in range(10)]
        result = limit(3)(rows)
        assert len(result) == 3
        assert result == [{"i": 0}, {"i": 1}, {"i": 2}]

    def test_limit_greater_than_length(self):
        rows = [{"i": 0}, {"i": 1}]
        assert limit(5)(rows) == rows

    def test_limit_zero(self):
        assert limit(0)([{"i": 1}]) == []

    def test_negative_count_returns_empty(self):
        """负数 max_count 应该返回空列表 (BUG-025)"""
        rows = [{"a": 1}, {"a": 2}, {"a": 3}]
        result = limit(-5)(rows)
        assert result == []
