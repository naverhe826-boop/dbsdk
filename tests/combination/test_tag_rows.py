"""tag_rows 过滤器测试"""

from data_builder.filters import tag_rows


class TestTagRows:
    def test_basic(self):
        rows = [{"a": 1}, {"a": 2}]
        result = tag_rows("_tag", "invalid")(rows)
        assert result == [{"a": 1, "_tag": "invalid"}, {"a": 2, "_tag": "invalid"}]

    def test_default_params(self):
        rows = [{"x": 1}]
        result = tag_rows()(rows)
        assert result == [{"x": 1, "_tag": ""}]

    def test_empty_input(self):
        assert tag_rows("_tag", "test")([]) == []

    def test_custom_field_name(self):
        rows = [{"a": 1}]
        result = tag_rows("source", "boundary")(rows)
        assert result == [{"a": 1, "source": "boundary"}]

    def test_overwrites_existing_field(self):
        rows = [{"a": 1, "_tag": "old"}]
        result = tag_rows("_tag", "new")(rows)
        assert result[0]["_tag"] == "new"

    def test_mutates_in_place(self):
        """tag_rows 修改原始行"""
        rows = [{"a": 1}]
        tag_rows("_tag", "x")(rows)
        assert rows[0]["_tag"] == "x"
