"""LLMStrategy._render_prompt 占位符缺失时的异常行为"""
import pytest

from data_builder import StrategyContext, LLMConfig
from data_builder.strategies.value.external import LLMStrategy


def _ctx(**kwargs):
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestRenderPromptMissingPlaceholder:
    @pytest.fixture
    def cfg(self):
        return LLMConfig(api_key="sk-test", model="test-model")

    def test_unknown_placeholder_raises_key_error(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="value={nonexistent_key}")
        with pytest.raises(KeyError, match="nonexistent_key"):
            strategy._render_prompt(_ctx())

    def test_valid_placeholders_ok(self, cfg):
        strategy = LLMStrategy(
            config=cfg,
            prompt="{field_path}|{index}|{field_schema}",
        )
        result = strategy._render_prompt(_ctx(field_path="a.b", index=3))
        assert "a.b" in result
        assert "3" in result

    def test_root_data_dict_access(self, cfg):
        """通过 {root_data[key]} 访问已生成数据"""
        strategy = LLMStrategy(config=cfg, prompt="name={root_data[name]}")
        result = strategy._render_prompt(_ctx(root_data={"name": "Alice"}))
        assert result == "name=Alice"

    def test_root_data_dict_access_missing_key(self, cfg):
        """root_data 中不存在的 key"""
        strategy = LLMStrategy(config=cfg, prompt="val={root_data[missing]}")
        with pytest.raises(KeyError, match="missing"):
            strategy._render_prompt(_ctx(root_data={}))

    def test_partial_placeholder_not_interpolated(self, cfg):
        """不完整的占位符保持原样"""
        strategy = LLMStrategy(config=cfg, prompt="text with {field_path} and {{literal}}")
        result = strategy._render_prompt(_ctx())
        # {{ }} 是 format_map 的转义语法，输出 {literal}
        assert "{literal}" in result
