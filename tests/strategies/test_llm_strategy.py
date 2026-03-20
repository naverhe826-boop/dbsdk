import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from data_builder import DataBuilder, BuilderConfig, FieldPolicy, LLMConfig, llm
from data_builder.strategies.value.external import LLMStrategy


# ------------------------------------------------------------------
# 工具函数：构造 openai ChatCompletion 响应 mock
# ------------------------------------------------------------------
def _make_completion(content: str):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig(api_key="sk-test", model="gpt-4o-mini")
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.timeout == 30
        assert cfg.max_tokens == 256
        assert cfg.temperature == 0.7
        assert cfg.extra_headers == {}

    def test_custom_values(self):
        cfg = LLMConfig(
            api_key="key",
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            timeout=60,
            max_tokens=512,
            temperature=0.3,
            extra_headers={"X-Org": "test"},
        )
        assert cfg.base_url == "https://api.deepseek.com/v1"
        assert cfg.timeout == 60
        assert cfg.extra_headers == {"X-Org": "test"}


class TestLLMStrategy:
    @pytest.fixture
    def cfg(self):
        return LLMConfig(api_key="sk-test", model="deepseek-v31")

    def _mock_client(self, strategy, content: str):
        """替换策略内部 _client，返回指定 content"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_completion(content)
        strategy._client = mock_client
        return mock_client

    # ------------------------------------------------------------------
    # 基础文本生成
    # ------------------------------------------------------------------
    def test_generate_plain_text(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="生成一个姓名")
        self._mock_client(strategy, "  张伟  ")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        config = BuilderConfig(policies=[FieldPolicy("name", strategy)])
        result = DataBuilder(schema, config).build()

        assert result["name"] == "张伟"

    # ------------------------------------------------------------------
    # prompt 模板占位符渲染
    # ------------------------------------------------------------------
    def test_prompt_template_rendering(self, cfg):
        strategy = LLMStrategy(
            config=cfg,
            prompt="path={field_path} index={index}",
        )
        mock_client = self._mock_client(strategy, "ok")

        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        config = BuilderConfig(policies=[FieldPolicy("x", strategy)])
        DataBuilder(schema, config).build()

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "path=x" in user_msg
        assert "index=0" in user_msg

    # ------------------------------------------------------------------
    # json_output=True 解析 JSON
    # ------------------------------------------------------------------
    def test_json_output_plain(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="生成标签", json_output=True)
        self._mock_client(strategy, '["A", "B", "C"]')

        schema = {"type": "object", "properties": {"tags": {"type": "array"}}}
        config = BuilderConfig(policies=[FieldPolicy("tags", strategy)])
        result = DataBuilder(schema, config).build()

        assert result["tags"] == ["A", "B", "C"]

    def test_json_output_with_markdown_fence(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="生成标签", json_output=True)
        self._mock_client(strategy, '```json\n["X", "Y"]\n```')

        schema = {"type": "object", "properties": {"tags": {"type": "array"}}}
        config = BuilderConfig(policies=[FieldPolicy("tags", strategy)])
        result = DataBuilder(schema, config).build()

        assert result["tags"] == ["X", "Y"]

    def test_json_output_object(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="生成对象", json_output=True)
        self._mock_client(strategy, '{"score": 5, "label": "好评"}')

        schema = {"type": "object", "properties": {"meta": {"type": "object"}}}
        config = BuilderConfig(policies=[FieldPolicy("meta", strategy)])
        result = DataBuilder(schema, config).build()

        assert result["meta"] == {"score": 5, "label": "好评"}

    # ------------------------------------------------------------------
    # 自定义 system_prompt
    # ------------------------------------------------------------------
    def test_custom_system_prompt(self, cfg):
        strategy = LLMStrategy(
            config=cfg,
            prompt="test",
            system_prompt="你是专业测试助手",
        )
        mock_client = self._mock_client(strategy, "result")

        schema = {"type": "object", "properties": {"v": {"type": "string"}}}
        config = BuilderConfig(policies=[FieldPolicy("v", strategy)])
        DataBuilder(schema, config).build()

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert sys_msg == "你是专业测试助手"

    # ------------------------------------------------------------------
    # LLM 配置参数传递给 openai 客户端
    # ------------------------------------------------------------------
    def test_config_passed_to_openai_client(self, cfg):
        cfg2 = LLMConfig(
            api_key="sk-abc",
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            max_tokens=64,
            temperature=0.1,
        )
        strategy = LLMStrategy(config=cfg2, prompt="x")

        with patch("data_builder.strategies.value.external.llm._OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _make_completion("val")
            MockOpenAI.return_value = mock_instance

            schema = {"type": "object", "properties": {"f": {"type": "string"}}}
            config = BuilderConfig(policies=[FieldPolicy("f", strategy)])
            DataBuilder(schema, config).build()

            MockOpenAI.assert_called_once_with(
                api_key="sk-abc",
                base_url="https://api.deepseek.com/v1",
                timeout=30,
                default_headers={},
            )
            create_kwargs = mock_instance.chat.completions.create.call_args.kwargs
            assert create_kwargs["model"] == "deepseek-chat"
            assert create_kwargs["max_tokens"] == 64
            assert create_kwargs["temperature"] == 0.1

    # ------------------------------------------------------------------
    # openai 未安装时给出明确错误
    # ------------------------------------------------------------------
    def test_import_error_when_openai_missing(self, cfg):
        strategy = LLMStrategy(config=cfg, prompt="x")

        import data_builder.strategies.value.external.llm as llm_module
        original = llm_module._OpenAI
        try:
            llm_module._OpenAI = None
            strategy._client = None
            with pytest.raises(ImportError, match="openai"):
                strategy._get_client()
        finally:
            llm_module._OpenAI = original

    # ------------------------------------------------------------------
    # 便捷工厂函数 llm()
    # ------------------------------------------------------------------
    def test_llm_factory_function(self, cfg):
        s = llm(config=cfg, prompt="test prompt")
        assert isinstance(s, LLMStrategy)
        assert s.prompt == "test prompt"
        assert s.json_output is False
        assert s.config is cfg

    def test_llm_factory_with_options(self, cfg):
        s = llm(config=cfg, prompt="p", system_prompt="sys", json_output=True)
        assert s.system_prompt == "sys"
        assert s.json_output is True

    # ------------------------------------------------------------------
    # 批量生成时 index 递增
    # ------------------------------------------------------------------
    def test_index_increments_in_batch(self, cfg):
        captured = []

        def side_effect(**kwargs):
            msg = next(m["content"] for m in kwargs["messages"] if m["role"] == "user")
            captured.append(msg)
            return _make_completion(f"val{len(captured)}")

        strategy = LLMStrategy(config=cfg, prompt="index={index}")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = side_effect
        strategy._client = mock_client

        schema = {"type": "object", "properties": {"v": {"type": "string"}}}
        config = BuilderConfig(policies=[FieldPolicy("v", strategy)])
        DataBuilder(schema, config).build(count=3)

        assert "index=0" in captured[0]
        assert "index=1" in captured[1]
        assert "index=2" in captured[2]

    # ------------------------------------------------------------------
    # parent_data 上下文可用
    # ------------------------------------------------------------------
    def test_parent_data_in_context(self, cfg):
        captured_prompts = []

        def side_effect(**kwargs):
            msg = next(m["content"] for m in kwargs["messages"] if m["role"] == "user")
            captured_prompts.append(msg)
            return _make_completion("summary")

        summary_strategy = LLMStrategy(
            config=cfg,
            # 使用 {parent_data} 整体序列化，避免 str.format 解析字典键
            prompt="data={parent_data}",
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = side_effect
        summary_strategy._client = mock_client

        schema = {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "summary": {"type": "string"},
            },
        }
        from data_builder import fixed
        config = BuilderConfig(policies=[
            FieldPolicy("product", fixed("键盘")),
            FieldPolicy("summary", summary_strategy),
        ])
        DataBuilder(schema, config).build()

        # parent_data 被序列化为 JSON 字符串，包含已生成的 product 字段
        assert "键盘" in captured_prompts[0]
