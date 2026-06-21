"""
模块1【核心】:把一张收据图片 -> 结构化的记账数据。

这是整个项目里唯一调用大模型的地方。把它单独成文件,
是为了后面项目2 能给它单独写 eval(批量测准确率)。

本版本用 OpenAI 的模型。注意:无论换哪家模型,
下面 Receipt 结构、CATEGORIES 白名单、extract_receipt 这个函数签名都不变——
变的只是函数内部怎么调 API。这就是"关注点分离"的好处。
"""

import base64
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# 读取 .env 里的 OPENAI_API_KEY,放进环境变量
load_dotenv()


# ---------------------------------------------------------------------------
# 1) 用 Pydantic 定义"我们想要的输出长什么样"。
#    我们不是让模型"随便吐 JSON",而是给它一份严格的表格模板。
#    OpenAI 的 structured output 会保证返回的内容 100% 符合这个结构,
#    省掉了用正则去抠字段、还经常抠错的痛苦。
# ---------------------------------------------------------------------------
class Receipt(BaseModel):
    """一张收据提取出来的字段。"""

    merchant: str = Field(description="商家名称,例如 '沃尔玛'、'星巴克'。看不清就填 '未知'")
    date: str = Field(description="消费日期,统一格式 YYYY-MM-DD。看不清就填空字符串")
    total: float = Field(description="消费总金额(最终实付),只要数字,例如 86.50")
    currency: str = Field(description="币种,如 CNY、USD。看不出来默认填 CNY")
    category: str = Field(
        description="消费类别,从这几类里选最合适的一个:"
        "餐饮、超市、交通、购物、医疗、娱乐、住房、其他"
    )


# 类别白名单。提取时让模型从这里挑,后面做 eval 才好判断对错。
CATEGORIES = ["餐饮", "超市", "交通", "购物", "医疗", "娱乐", "住房", "其他"]

# 用哪个模型。gpt-4o-mini 便宜、支持看图和结构化输出,够用。
# 想更准可以换成 "gpt-4o"。改这一行就行。
MODEL = "gpt-4o-mini"

# 全局只建一个客户端,自动从环境变量 OPENAI_API_KEY 读 key
client = OpenAI()


def extract_receipt(image_bytes: bytes, media_type: str) -> Receipt:
    """
    输入:收据图片的二进制内容 + 图片类型(如 'image/jpeg')
    输出:一个填好字段的 Receipt 对象
    """
    # 图片要先转成 base64,再拼成 data URL 才能塞进请求
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{media_type};base64,{image_b64}"

    # parse = 普通请求 + "请按 Receipt 这个结构返回"。
    # 它会自动帮我们校验并解析成 Receipt 对象。
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "这是一张消费收据/发票/账单。请仔细看图,"
                            "提取记账需要的字段。金额取最终实付总额。"
                            f"类别只能从这几类里选:{', '.join(CATEGORIES)}。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                ],
            }
        ],
        response_format=Receipt,
    )

    return completion.choices[0].message.parsed


# 直接运行这个文件可以快速自测:python extract.py 某张收据.jpg
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:python extract.py <收据图片路径>")
        sys.exit(1)

    path = sys.argv[1]
    # 根据文件后缀猜图片类型
    ext = os.path.splitext(path)[1].lower()
    media = "image/png" if ext == ".png" else "image/jpeg"

    with open(path, "rb") as f:
        data = f.read()

    result = extract_receipt(data, media)
    print("提取结果:")
    print(f"  商家:{result.merchant}")
    print(f"  日期:{result.date}")
    print(f"  金额:{result.total} {result.currency}")
    print(f"  类别:{result.category}")
