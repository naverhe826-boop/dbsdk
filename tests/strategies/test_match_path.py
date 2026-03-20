"""_match_path 的 fnmatch 通用通配符分支测试"""
import pytest

from data_builder import DataBuilder, BuilderConfig, FieldPolicy
from data_builder import fixed


class TestFnmatchFallback:
    """fnmatch 通配符（非 .* 和 [*] 的第三条分支）"""

    def _match(self, path, pattern):
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        builder = DataBuilder(schema, BuilderConfig())
        return builder._match_path(path, pattern)

    # 精确匹配（fnmatch 也能处理）
    def test_exact_match(self):
        assert self._match("user.name", "user.name")

    # ? 匹配单字符
    def test_question_mark_single_char(self):
        assert self._match("user.a", "user.?")

    def test_question_mark_no_match(self):
        assert not self._match("user.ab", "user.?")

    # * 匹配任意字符串（fnmatch 的 * 不跨 / 但路径中无 /）
    def test_star_wildcard(self):
        assert self._match("config.db_host", "config.db_*")

    def test_star_matches_empty(self):
        assert self._match("config.db_", "config.db_*")

    # [seq] 字符集匹配
    def test_char_set(self):
        assert self._match("field_a", "field_[abc]")

    def test_char_set_no_match(self):
        assert not self._match("field_z", "field_[abc]")

    # [!seq] 取反
    def test_char_set_negation(self):
        assert self._match("field_z", "field_[!abc]")

    def test_char_set_negation_no_match(self):
        assert not self._match("field_a", "field_[!abc]")


class TestFnmatchIntegration:
    """fnmatch 通配符通过 FieldPolicy 实际生效"""

    def test_question_mark_policy(self):
        schema = {
            "type": "object",
            "properties": {
                "v1": {"type": "string"},
                "v2": {"type": "string"},
                "vv": {"type": "string"},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("v?", fixed("hit"))])
        result = DataBuilder(schema, config).build()
        assert result["v1"] == "hit"
        assert result["v2"] == "hit"
        # vv 也只有两个字符，? 匹配单个字符
        assert result["vv"] == "hit"

    def test_star_prefix_policy(self):
        schema = {
            "type": "object",
            "properties": {
                "db_host": {"type": "string"},
                "db_port": {"type": "string"},
                "api_key": {"type": "string"},
            },
        }
        config = BuilderConfig(policies=[FieldPolicy("db_*", fixed("db_val"))])
        result = DataBuilder(schema, config).build()
        assert result["db_host"] == "db_val"
        assert result["db_port"] == "db_val"
        assert result["api_key"] != "db_val"
