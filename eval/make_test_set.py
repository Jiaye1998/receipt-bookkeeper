"""
生成"合成收据测试集":一批假收据图片 + 一份标准答案 labels.csv。

为什么合成?因为内容是我们编的,所以正确答案天生就知道(免费完美标注),
还能故意控制难度。注意:合成 ≠ 真实分布,后面要再混入几张真实收据。

运行:python eval/make_test_set.py
产出:eval/images/*.png  和  eval/labels.csv
"""

import os

import pandas as pd
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(__file__)
IMG_DIR = os.path.join(HERE, "images")
LABELS_PATH = os.path.join(HERE, "labels.csv")

CN_FONT = "C:/Windows/Fonts/msyh.ttc"       # 微软雅黑(支持中文)
CN_BOLD = "C:/Windows/Fonts/msyhbd.ttc"     # 雅黑粗体


# ---------------------------------------------------------------------------
# 标准答案:每条就是一张收据的"正确提取结果"。
# 这是整个 eval 的地基——我们编的,所以 100% 确定它是对的。
# items 只用来把图画得像收据,不参与评分。
# diff 是难度标记:让一部分图变难,eval 才有意义(全清晰=模型必满分=测不出东西)。
# ---------------------------------------------------------------------------
DATA = [
    dict(merchant="沃尔玛", date="2026-05-03", total=86.50, currency="CNY", category="超市",
         items=[("鸡蛋", 12.80), ("牛奶", 25.90), ("面包", 9.50), ("洗洁精", 38.30)]),
    dict(merchant="麦当劳", date="2026-05-06", total=43.00, currency="CNY", category="餐饮",
         items=[("巨无霸套餐", 35.00), ("甜筒", 8.00)]),
    dict(merchant="滴滴出行", date="2026-05-07", total=27.60, currency="CNY", category="交通",
         items=[("快车 3.2公里", 27.60)]),
    dict(merchant="星巴克", date="2026-05-09", total=39.00, currency="CNY", category="餐饮",
         items=[("拿铁 大杯", 33.00), ("纸杯", 6.00)]),
    dict(merchant="优衣库", date="2026-05-11", total=199.00, currency="CNY", category="购物",
         items=[("圆领T恤", 79.00), ("休闲裤", 120.00)]),
    dict(merchant="COSTCO WHOLESALE", date="2026-05-12", total=124.18, currency="USD", category="超市",
         items=[("ROTISSERIE CHICKEN", 4.99), ("KS PAPER TOWEL", 22.99), ("BEEF", 96.20)],
         diff="blur"),
    dict(merchant="同仁堂药房", date="2026-05-14", total=68.00, currency="CNY", category="医疗",
         items=[("板蓝根颗粒", 18.00), ("创可贴", 12.00), ("维生素C", 38.00)]),
    dict(merchant="万达影城", date="2026-05-16", total=90.00, currency="CNY", category="娱乐",
         items=[("电影票 x2", 90.00)]),
    dict(merchant="中国石化", date="2026-05-18", total=300.00, currency="CNY", category="交通",
         items=[("92号汽油 40.5L", 300.00)], diff="lowcontrast"),
    # 含税/服务费陷阱:小计≠实付,正确答案取"合计(实付)"
    dict(merchant="海底捞火锅", date="2026-05-20", total=358.00, currency="CNY", category="餐饮",
         items=[("锅底+菜品 小计", 325.00), ("服务费 10%", 33.00)], diff="subtotal"),
    dict(merchant="京东", date="2026-05-22", total=459.00, currency="CNY", category="购物",
         items=[("蓝牙耳机", 459.00)], diff="rotate"),
    # 少见类别:物业费 -> 住房(容易被误判成"其他")
    dict(merchant="阳光物业", date="2026-05-25", total=240.00, currency="CNY", category="住房",
         items=[("5月物业费", 180.00), ("电梯维护费", 60.00)]),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def render(rec, idx):
    """把一条标准答案画成一张收据图片,返回保存的文件名。"""
    W = 480
    pad = 30
    sym = "¥" if rec["currency"] == "CNY" else "$"

    # 先算高度:头部 + 日期 + 每个item一行 + 合计 + 页脚
    n = len(rec["items"])
    H = pad + 50 + 40 + 20 + n * 34 + 20 + 50 + 50 + pad

    img = Image.new("RGB", (W, H), (252, 252, 250))
    d = ImageDraw.Draw(img)

    f_head = font(CN_BOLD, 30)
    f_norm = font(CN_FONT, 20)
    f_bold = font(CN_BOLD, 24)

    y = pad
    # 商家(居中)
    tw = d.textlength(rec["merchant"], font=f_head)
    d.text(((W - tw) / 2, y), rec["merchant"], fill=(20, 20, 20), font=f_head)
    y += 50
    # 日期
    d.text((pad, y), f"日期: {rec['date']}", fill=(60, 60, 60), font=f_norm)
    y += 40
    d.line((pad, y, W - pad, y), fill=(180, 180, 180), width=1)
    y += 20
    # 明细:名称在左,价格右对齐
    for name, price in rec["items"]:
        d.text((pad, y), name, fill=(40, 40, 40), font=f_norm)
        ptxt = f"{sym}{price:.2f}"
        pw = d.textlength(ptxt, font=f_norm)
        d.text((W - pad - pw, y), ptxt, fill=(40, 40, 40), font=f_norm)
        y += 34
    y += 20
    d.line((pad, y, W - pad, y), fill=(180, 180, 180), width=1)
    y += 20
    # 合计(加粗)
    d.text((pad, y), "合计(实付)", fill=(0, 0, 0), font=f_bold)
    ttxt = f"{sym}{rec['total']:.2f}"
    tw = d.textlength(ttxt, font=f_bold)
    d.text((W - pad - tw, y), ttxt, fill=(0, 0, 0), font=f_bold)
    y += 50
    d.text((pad, y), "谢谢惠顾", fill=(120, 120, 120), font=f_norm)

    # 按难度标记做"变难"处理
    diff = rec.get("diff")
    if diff == "blur":
        img = img.filter(ImageFilter.GaussianBlur(1.3))
    elif diff == "lowcontrast":
        img = ImageEnhance.Contrast(img).enhance(0.45)
        img = ImageEnhance.Brightness(img).enhance(1.15)
    elif diff == "rotate":
        img = img.rotate(-7, expand=True, fillcolor=(252, 252, 250))

    fname = f"{idx:02d}_{rec['category']}.png"
    img.save(os.path.join(IMG_DIR, fname))
    return fname


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    rows = []
    for i, rec in enumerate(DATA, start=1):
        fname = render(rec, i)
        rows.append({
            "image": fname,
            "merchant": rec["merchant"],
            "date": rec["date"],
            "total": rec["total"],
            "currency": rec["currency"],
            "category": rec["category"],
        })
    pd.DataFrame(rows).to_csv(LABELS_PATH, index=False, encoding="utf-8-sig")
    print(f"生成了 {len(rows)} 张收据 -> {IMG_DIR}")
    print(f"标准答案 -> {LABELS_PATH}")


if __name__ == "__main__":
    main()
