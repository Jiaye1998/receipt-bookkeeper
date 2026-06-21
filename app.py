"""
模块3【界面】:Streamlit 网页。
上传收据图 -> 提取 -> (可手动校正) -> 存进账本 -> 看账本/下载。

运行:streamlit run app.py
"""

import streamlit as st

from extract import CATEGORIES, extract_receipt
from store import load_records, save_record, CSV_PATH

st.set_page_config(page_title="收据记账助手", page_icon="🧾")
st.title("🧾 收据记账助手")
st.caption("上传一张收据,自动提取商家/日期/金额/类别,存进你的账本。")

# ---------------------------------------------------------------------------
# 第一步:上传图片
# ---------------------------------------------------------------------------
uploaded = st.file_uploader("上传收据图片", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    st.image(uploaded, caption="你上传的收据", width=350)

    # 点一下才调用模型(省钱:不点不花钱)
    if st.button("🔍 提取信息", type="primary"):
        with st.spinner("正在让 AI 读这张收据……"):
            image_bytes = uploaded.getvalue()
            receipt = extract_receipt(image_bytes, uploaded.type)
        # 存进 session_state,这样页面刷新后结果还在
        st.session_state["receipt"] = receipt

# ---------------------------------------------------------------------------
# 第二步:显示提取结果,允许手动校正后再保存
#   (这个"人工校正"既让结果更准,也是项目2 做人工标注的雏形)
# ---------------------------------------------------------------------------
if "receipt" in st.session_state:
    r = st.session_state["receipt"]
    st.subheader("提取结果(可修改)")

    col1, col2 = st.columns(2)
    merchant = col1.text_input("商家", r.merchant)
    date = col2.text_input("日期", r.date)
    total = col1.number_input("金额", value=float(r.total), step=0.01)
    currency = col2.text_input("币种", r.currency)
    # 类别用下拉框,只能选白名单里的
    default_idx = CATEGORIES.index(r.category) if r.category in CATEGORIES else len(CATEGORIES) - 1
    category = st.selectbox("类别", CATEGORIES, index=default_idx)

    if st.button("💾 保存到账本"):
        r.merchant, r.date, r.total, r.currency, r.category = (
            merchant, date, total, currency, category,
        )
        save_record(r)
        st.success("已保存!")
        # 清掉,避免重复保存
        del st.session_state["receipt"]
        st.rerun()

# ---------------------------------------------------------------------------
# 第三步:显示整个账本 + 下载按钮
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📒 我的账本")
records = load_records()

if records.empty:
    st.info("账本还是空的。上传第一张收据试试吧。")
else:
    st.dataframe(records, use_container_width=True)
    # 简单统计:一共几条、各币种合计
    st.caption(f"共 {len(records)} 条记录。")
    with open(CSV_PATH, "rb") as f:
        st.download_button("⬇️ 下载账本 CSV", f, file_name="records.csv", mime="text/csv")
