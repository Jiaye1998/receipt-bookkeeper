"""
LLM-as-judge:用模型来判断"两个商家名是不是同一家"。

为什么不用字符串规则?因为 '星巴克' vs 'Starbucks'、'麦当劳' vs '金拱门'
这种语义相同、字面不同的情况,规则判不了——而真实场景全是这种。
"""

from pydantic import BaseModel

# 复用 extract.py 里的同一个客户端和模型(我们自己的项目,内部用一下没问题)
from extract import MODEL, _get_client


class Verdict(BaseModel):
    """裁判的结论:是否同一家 + 一句理由(理由便于我们排查裁判为啥这么判)。"""
    same: bool
    reason: str


def same_merchant(pred: str, truth: str) -> bool:
    """问模型:这两个商家名指的是不是同一家商户?"""
    completion = _get_client().beta.chat.completions.parse(
        model=MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": (
                    "判断下面两个商家名是否指【同一家商户】。\n"
                    "判断时要考虑:简称与全称、品牌别名/曾用名、中英文写法、"
                    "OCR 造成的轻微错字。\n"
                    "不要因为字面不同就判不同——看的是'是不是同一家'。\n\n"
                    f"A: {pred}\n"
                    f"B: {truth}\n\n"
                    "same=true 表示同一家,false 表示不同。reason 用一句话说明。"
                ),
            }
        ],
        response_format=Verdict,
    )
    return completion.choices[0].message.parsed.same
