"""
校准裁判:用一批"人工标好答案"的商家名对子,
看 LLM 裁判和人意见的一致率;并和老的字符串规则对比,
证明"语义场景下,裁判确实比死规则强"。

运行(项目根目录):python eval/calibrate_judge.py
"""

import pandas as pd

from judge import same_merchant          # LLM 裁判
from run_eval import match_merchant      # 老的字符串规则

# ---------------------------------------------------------------------------
# 校准集:(预测商家, 标准商家, 人工判定是否同一家)
# 注意:最后一列 human 是【人】定的标准——这是衡量裁判的"真值"。
# 有些是故意挑的"陷阱":跨语言、品牌别名、形近但不同家。
# ---------------------------------------------------------------------------
CALIB = [
    ("沃尔玛", "沃尔玛", True),
    ("沃尔玛超市", "沃尔玛", True),
    ("COSTCO", "COSTCO WHOLESALE", True),
    ("星巴克", "Starbucks", True),          # 跨语言:字符串规则必错
    ("滴滴", "滴滴出行", True),
    ("肯德基", "肯德基(KFC)", True),
    ("麦当劳", "金拱门", True),             # 金拱门=麦当劳中国:别名,字符串规则必错
    ("麦当劳", "肯德基", False),
    ("星巴克", "瑞幸咖啡", False),
    ("京东", "淘宝", False),
    ("中国石化", "中国石油", False),        # 形近但不同家:陷阱
    ("盒马", "天猫超市", False),
]


def main():
    rows = []
    for pred, truth, human in CALIB:
        judge_says = same_merchant(pred, truth)       # 裁判判
        rule_says = match_merchant(pred, truth)        # 老规则判
        rows.append({
            "A": pred, "B": truth,
            "人工": human,
            "裁判": judge_says, "裁判对": judge_says == human,
            "字符串规则": rule_says, "规则对": rule_says == human,
        })

    df = pd.DataFrame(rows)
    pd.set_option("display.unicode.east_asian_width", True)
    print(df.to_string(index=False))

    n = len(df)
    print("\n" + "=" * 44)
    print(f"校准集:{n} 对")
    print(f"  LLM 裁判   与人工一致率: {df['裁判对'].mean():6.1%}")
    print(f"  字符串规则 与人工一致率: {df['规则对'].mean():6.1%}")
    print("=" * 44)
    # 把分歧的行单独列出来(裁判错在哪 / 规则错在哪)
    bad_judge = df[~df["裁判对"]]
    if not bad_judge.empty:
        print("\n裁判判错的:")
        print(bad_judge[["A", "B", "人工", "裁判"]].to_string(index=False))


if __name__ == "__main__":
    main()
