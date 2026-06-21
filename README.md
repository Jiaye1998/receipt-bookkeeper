# 🧾 Receipt Bookkeeper

Snap a photo of a receipt, and an LLM extracts the merchant, date, amount, and
spending category into a structured ledger you can export to Excel.

A small but complete LLM application: **vision-based extraction → structured
output → editable review → CSV ledger.** Built as a learning project with a real
user (myself, for household bookkeeping).

> ⚠️ Add a screenshot or short GIF here — `docs/demo.png`. A visual is the first
> thing a reader looks at. (TODO before sharing.)

---

## What it does

1. Upload a receipt image (`.jpg` / `.png`).
2. An LLM reads the image and extracts: **merchant, date, total, currency, category**.
3. You review and correct the result inline (one click), then save it.
4. Records accumulate in a CSV ledger you can view and download.

The category is constrained to a fixed set of 8 buckets (餐饮 / 超市 / 交通 /
购物 / 医疗 / 娱乐 / 住房 / 其他) so the output stays consistent and measurable.

---

## How it works

```
          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 receipt  │  extract.py  │      │   store.py   │      │    app.py    │
  image ─▶│  (LLM core)  │─────▶│  (CSV store) │◀────▶│ (Streamlit)  │─▶ browser
          │  image→struct│ Receipt│ append/load │      │ upload/review│
          └──────────────┘      └──────────────┘      └──────────────┘
```

The three modules are deliberately decoupled. `extract.py` is the only file that
talks to an LLM, and it exposes a single function — `extract_receipt(image_bytes,
media_type) -> Receipt`. Everything downstream (storage, UI) depends on the
`Receipt` schema, not on which model produced it.

---

## Tech stack & why

| Choice | Why |
|---|---|
| **Structured Outputs** (Pydantic schema) | Guarantees the model returns valid, parseable fields — no regex scraping of free-text. The schema *is* the contract. |
| **Category whitelist** (8 fixed buckets) | Keeps output consistent and makes correctness measurable — essential for the eval harness planned next. |
| **Decoupled `extract_receipt()` function** | The LLM call is isolated behind one function. Swapping providers (this project moved from Anthropic to OpenAI in minutes) touches only `extract.py`. |
| **Streamlit** | Fastest path from Python to a usable web UI; free one-click deploy on Streamlit Community Cloud. |
| **CSV + pandas** | Simplest store that "just works" and opens directly in Excel (`utf-8-sig` so Chinese isn't garbled). |
| **OpenAI `gpt-4o-mini`** | Vision + structured outputs at low cost. One config line (`MODEL` in `extract.py`) switches to `gpt-4o` for higher accuracy. |

---

## Run it locally

Requires Python 3.9+ (note: not exactly 3.9.7 — Streamlit excludes that patch).

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env            # then edit .env and paste your OPENAI_API_KEY

# 4. Run
streamlit run app.py
```

Open http://localhost:8501.

---

## Trade-offs

- **CSV instead of a database.** Simple and Excel-friendly, but no concurrent
  writes and no querying. Fine for a single user; would need a real DB to scale.
- **`gpt-4o-mini` over `gpt-4o`.** Cheaper per receipt, slightly less accurate on
  messy or handwritten receipts. The model is a one-line swap.
- **Structured output guarantees *format*, not *correctness*.** The model can
  still mis-read a merchant name or amount. That's exactly why there's a manual
  review step before saving — and why measuring accuracy is the next milestone.

---

## Known limitations

- **Accuracy is not yet quantified.** There is no automated evaluation; results
  are spot-checked by eye. Building a proper eval harness (error analysis,
  LLM-as-judge, accuracy over an iteration loop) is the planned next phase.
- Extraction quality degrades on blurry, cropped, or low-light photos.
- Currency is inferred and defaults to CNY when ambiguous.
- Categories are limited to 8 fixed buckets; unusual purchases fall into 其他.
- No authentication or multi-user support.

---

## Roadmap

- [ ] **Eval harness** — measure extraction accuracy on a labeled set, do error
      analysis, and iterate (v1 → v2 → v3 with data).
- [ ] Per-currency totals and monthly summaries.
- [ ] Deploy a public demo on Streamlit Community Cloud.
- [ ] Optional local-model backend (privacy: receipts never leave the machine).
