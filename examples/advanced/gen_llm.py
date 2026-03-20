"""
演示通过 LLMStrategy 让大模型生成字段值。

运行前需设置环境变量：
  export OPENAI_API_KEY=sk-xxx
  export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，默认值
  export OPENAI_MODEL=gpt-4o-mini                   # 可选，默认值

兼容任意 OpenAI 格式接口（如 DeepSeek、通义千问、本地 Ollama 等），
只需修改 base_url 和 model 即可。

包含以下示例：
- LLM 生成商品评价标签（JSON 数组输出）
- LLM 生成评价摘要
- LLM 扩写详细评价（引用已生成的摘要）
"""

import os
import sys
import json

from dotenv import load_dotenv
load_dotenv()   # 自动读取项目根目录 .env，不影响已设置的系统环境变量

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_builder import (
    DataBuilder,
    BuilderConfig,
    FieldPolicy,
    LLMConfig,
    llm,
    seq,
    fixed,
    range_int,
    enum,
)


def example_llm_usage():
    """LLM 使用示例"""
    print("=" * 60)
    print("LLM 生成示例")
    print("=" * 60)

    # LLM 配置由调用方提供，框架本身不持有任何凭证
    llm_config = LLMConfig(
        api_key=os.environ["OPENAI_API_KEY"],
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        max_tokens=4096,
        temperature=0.8,
    )

    # Schema：商品评价
    schema = {
        "type": "object",
        "properties": {
            "id":          {"type": "integer"},
            "product":     {"type": "string"},
            "score":       {"type": "integer"},
            "tags":        {"type": "array",  "items": {"type": "string"}},
            "summary":     {"type": "string"},
            "review":      {"type": "string"},
        },
    }

    PRODUCTS = ["无线蓝牙耳机", "机械键盘", "人体工学椅", "便携充电宝", "智能手表"]

    config = BuilderConfig(policies=[
        FieldPolicy("id",      seq(start=1)),
        FieldPolicy("product", enum(PRODUCTS)),
        FieldPolicy("score",   range_int(1, 5)),

        # LLM 生成：根据商品名和评分生成 tags（要求返回 JSON 数组）
        FieldPolicy("tags", llm(
            config=llm_config,
            prompt=(
                "商品「{parent_data[product]}」的用户评分为 {parent_data[score]} 分（满分5分）。"
                "请生成 3 个简短的评价标签，以 JSON 数组形式返回，例如：[\"做工精良\", \"续航持久\", \"物超所值\"]。"
                "只返回 JSON 数组，不要其他内容。"
            ),
            json_output=True,
        )),

        # LLM 生成：一句话评价摘要
        FieldPolicy("summary", llm(
            config=llm_config,
            prompt=(
                "商品「{parent_data[product]}」，用户评分 {parent_data[score]} 分。"
                "请用一句话（不超过20字）写出用户评价摘要，只返回摘要文本。"
            ),
        )),

        # LLM 生成：详细评价（利用已生成的 summary 作为参考）
        FieldPolicy("review", llm(
            config=llm_config,
            prompt=(
                "商品「{parent_data[product]}」，评价摘要：{parent_data[summary]}。"
                "请据此扩写一段50字左右的详细用户评价，语气自然真实，只返回评价内容。"
            ),
        )),
    ])

    builder = DataBuilder(schema, config)
    reviews = builder.build(count=2)

    for r in reviews:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print("-" * 60)


if __name__ == "__main__":
    example_llm_usage()
