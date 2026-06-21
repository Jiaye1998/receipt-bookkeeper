"""
模块2【存储】:把一条提取结果追加进 CSV 账本。

为什么用 CSV 不用数据库?v1 要"最丑能跑"。CSV 一行一条账,
Excel 直接能打开,够用了。以后真需要再升级数据库。
"""

import os
from datetime import datetime

import pandas as pd

from extract import Receipt

# 账本存在 data/records.csv
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "records.csv")

# 表头(列名)。顺序固定,方便以后对比和做 eval。
COLUMNS = ["录入时间", "商家", "日期", "金额", "币种", "类别"]


def save_record(receipt: Receipt) -> None:
    """把一条 Receipt 追加到 CSV 账本末尾。"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # 组装成一行
    row = {
        "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "商家": receipt.merchant,
        "日期": receipt.date,
        "金额": receipt.total,
        "币种": receipt.currency,
        "类别": receipt.category,
    }

    # 文件不存在就先写表头;存在就只追加这一行,不重复写表头
    write_header = not os.path.exists(CSV_PATH)
    pd.DataFrame([row], columns=COLUMNS).to_csv(
        CSV_PATH,
        mode="a",            # append 追加模式
        header=write_header,
        index=False,
        encoding="utf-8-sig",  # 带 BOM,这样 Excel 打开中文不乱码
    )


def load_records() -> pd.DataFrame:
    """读出整个账本,返回一个表格。账本为空就返回空表。"""
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")
