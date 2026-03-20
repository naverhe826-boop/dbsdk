import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError

try:
    from openai import OpenAI as _OpenAI
except ImportError:
    _OpenAI = None


@dataclass
class LLMConfig:
    """LLM 连接配置，由外部调用方传入"""
    api_key: str = ""
    model: str = ""
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 30
    max_tokens: int = 256
    temperature: float = 0.7
    extra_headers: Dict[str, str] = field(default_factory=dict)


class LLMStrategy(Strategy):
    """
    LLM 生成策略。

    调用方通过 LLMConfig 传入连接参数，prompt 模板支持以下占位符：
      {field_path}   - 当前字段路径，如 "user.name"
      {field_schema} - 当前字段的 JSON Schema（JSON 字符串）
      {root_data}    - 已生成的根数据（JSON 字符串）
      {parent_data}  - 父级数据（JSON 字符串）
      {index}        - 批量生成时当前索引

    LLM 返回值默认取响应文本；若设置 json_output=True，则尝试将响应解析为 JSON。
    """

    def __init__(
        self,
        config: LLMConfig,
        prompt: str,
        system_prompt: str = "你是一个测试数据生成助手，请根据要求生成符合格式的测试数据，只返回数据本身，不要添加任何解释。",
        json_output: bool = False,
    ):
        self.config = config
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.json_output = json_output
        self._client = None

    def _get_client(self):
        if self._client is None:
            if _OpenAI is None:
                raise ImportError("LLMStrategy 需要安装 openai 包：pip install openai")
            self._client = _OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                default_headers=self.config.extra_headers,
            )
        return self._client

    def _render_prompt(self, ctx: StrategyContext) -> str:
        # 用 format_map 支持 {parent_data[key]} 语法（直接访问 dict）
        # 同时提供序列化版本 {parent_data_json} 等供需要 JSON 字符串时使用
        mapping = {
            "field_path": ctx.field_path,
            "field_schema": json.dumps(ctx.field_schema, ensure_ascii=False),
            "root_data": ctx.root_data or {},
            "parent_data": ctx.parent_data or {},
            "root_data_json": json.dumps(ctx.root_data, ensure_ascii=False, default=str),
            "parent_data_json": json.dumps(ctx.parent_data, ensure_ascii=False, default=str),
            "index": ctx.index,
        }
        return self.prompt.format_map(mapping)

    def _clean_text_response(self, text: str) -> str:
        """
        清理非 JSON 模式下的 LLM 响应，移除思考块等无关内容。
        """
        text = text.strip()
        
        # 移除 markdown 代码块
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1])
            elif len(lines) >= 1:
                text = "\n".join(lines[1:])
        
        # 移除 LLM 思考过程
        import re
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
        
        # 移除多余的空白行
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text.strip()

    def _clean_json_response(self, text: str) -> str:
        """
        清理 LLM 返回的文本，提取其中的 JSON 内容。
        
        处理以下情况：
        1. Markdown 代码块包裹（如 ```json [...] ```）
        2. LLM 思考过程（如 [...</think>]）
        3. 首尾空白
        """
        text = text.strip()
        
        # 移除 markdown 代码块
        if text.startswith("```"):
            lines = text.splitlines()
            # 移除第一行（```json 或 ```）和最后一行（```）
            if len(lines) >= 2:
                # 检查是否以 ``` 结尾
                if lines[-1].strip() == "```":
                    text = "\n".join(lines[1:-1])
                else:
                    text = "\n".join(lines[1:])
        
        # 移除 LLM 思考过程（DeepSeek 等模型的 thinking 标签）
        import re
        # 移除 <think>...</think> 对
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # 移除 <thinking>...</thinking> 对
        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
        
        # 再次清理首尾空白
        text = text.strip()
        
        # 如果文本看起来像 JSON（以 [ 或 { 开头），直接返回
        if text.startswith("[") or text.startswith("{"):
            return text
        
        # 否则尝试提取 JSON 数组或对象
        # 找到第一个 '[' 或 '{' 和最后一个 ']' 或 '}'
        json_start = text.find('[')
        obj_start = text.find('{')
        
        start = -1
        if json_start != -1 and obj_start != -1:
            start = min(json_start, obj_start)
        elif json_start != -1:
            start = json_start
        elif obj_start != -1:
            start = obj_start
        
        if start == -1:
            return text
        
        # 找到对应的结束括号
        if text[start] == '[':
            # 寻找匹配的 ]
            depth = 0
            end = -1
            for i, c in enumerate(text[start:], start):
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end != -1:
                return text[start:end+1]
        elif text[start] == '{':
            # 寻找匹配的 }
            depth = 0
            end = -1
            for i, c in enumerate(text[start:], start):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end != -1:
                return text[start:end+1]
        
        return text

    def generate(self, ctx: StrategyContext) -> Any:
        client = self._get_client()
        rendered = self._render_prompt(ctx)

        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": rendered},
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # 检查响应是否有效
        if not response.choices:
            raise StrategyError("LLMStrategy: API 返回空响应choices，请检查API配置是否正确")

        message = response.choices[0].message
        if message is None:
            raise StrategyError("LLMStrategy: API 返回空消息，请检查API配置是否正确")

        text = message.content
        if text is None:
            raise StrategyError("LLMStrategy: API 返回的 message.content 为 None，可能是内容被过滤或模型拒绝生成")

        text = text.strip()
        if not text:
            raise StrategyError("LLMStrategy: API 返回空文本，请检查API配置或模型是否正常工作")

        if self.json_output:
            # 清理响应文本
            cleaned = self._clean_json_response(text)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise StrategyError(f"LLMStrategy: JSON 解析失败: {e}，原始响应: {text!r}")

        # 非 JSON 模式也需要清理思考块
        return self._clean_text_response(text)
