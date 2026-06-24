"""
Eval v1:跑测试集,逐字段算准确率。

核心思想:不同字段用不同的"判对标准"——
  商家:宽松匹配(COSTCO 和 COSTCO WHOLESALE 算同一家)
  金额:精确匹配(124.18 ≠ 124.08)
  日期/币种/类别:精确匹配
这正是 eval 设计的精髓:判对标准本身就是一种"产品决策"。

运行(在项目根目录):python eval/run_eval.py
产出:eval/results.csv(每张的预测 vs 答案,供 error analysis)
"""

import os

import pandas as pd

from extract import extract_receipt

HERE = os.path.dirname(__file__)
IMG_DIR = os.path.join(HERE, "images")
LABELS_PATH = os.path.join(HERE, "labels.csv")
RESULTS_PATH = os.path.join(HERE, "results.csv")

FIELDS = ["merchant", "date", "total", "currency", "category"]


# ---- 各字段的判对规则 --------------------------------------------------------
def match_merchant(pred: str, truth: str) -> bool:
    """宽松:忽略大小写和空格,一方包含另一方就算对。"""
    p = str(pred).strip().lower().replace(" ", "")
    t = str(truth).strip().lower().replace(" ", "")
    return bool(p) and (p == t or p in t or t in p)


def match_total(pred, truth) -> bool:
    """精确:金额差小于一分钱才算对。"""
    try:
        return abs(float(pred) - float(truth)) < 0.01
    except (TypeError, ValueError):
        return False


def match_exact(pred, truth) -> bool:
    """精确:去空格、忽略大小写后完全相等。"""
    return str(pred).strip().lower() == str(truth).strip().lower()


def judge(field: str, pred, truth) -> bool:
    if field == "merchant":
        return match_merchant(pred, truth)
    if field == "total":
        return match_total(pred, truth)
    return match_exact(pred, truth)  # date / currency / category


def main():
    labels = pd.read_csv(LABELS_PATH, encoding="utf-8-sig")
    rows = []

    for _, gt in labels.iterrows():
        img_path = os.path.join(IMG_DIR, gt["image"])
        with open(img_path, "rb") as f:
            image_bytes = f.read()

        # 调用我们项目的核心函数(和真应用走的是同一条路)
        pred = extract_receipt(image_bytes, "image/png")

        row = {"image": gt["image"]}
        for field in FIELDS:
            pred_val = getattr(pred, field)
            truth_val = gt[field]
            ok = judge(field, pred_val, truth_val)
            row[f"{field}_pred"] = pred_val
            row[f"{field}_true"] = truth_val
            row[f"{field}_ok"] = ok
        # 整张全对才算"完全正确"
        row["all_ok"] = all(row[f"{f}_ok"] for f in FIELDS)
        rows.append(row)
        mark = "✅" if row["all_ok"] else "❌"
        print(f"{mark} {gt['image']}: 商家={pred.merchant} 金额={pred.total} 类别={pred.category}")

    results = pd.DataFrame(rows)
    results.to_csv(RESULTS_PATH, index=False, encoding="utf-8-sig")

    # ---- 汇总:每个字段的准确率 ----
    n = len(results)
    print("\n" + "=" * 40)
    print(f"测试集:{n} 张收据")
    print("-" * 40)
    for field in FIELDS:
        acc = results[f"{field}_ok"].mean()
        print(f"  {field:10s} 准确率: {acc:6.1%}")
    print("-" * 40)
    print(f"  {'整张全对':10s} 准确率: {results['all_ok'].mean():6.1%}")
    print("=" * 40)
    print(f"\n逐张明细已存:{RESULTS_PATH}(下一步做 error analysis 用)")


if __name__ == "__main__":
    main()
