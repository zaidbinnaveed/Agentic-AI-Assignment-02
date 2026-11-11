# What you still need to run or supply

## Q1 – SaafHawa
1. **OpenAQ API key.** Create a free key at https://explore.openaq.org/register, copy `.env.example` to `.env` and set `OPENAQ_API_KEY=...`. The first run (11 Nov 2026) had no key, so its 25 `air_quality` rows are logged as errors.
2. **Timing runs on two different days.** Run `python tool_latency.py --n 25` once today, now that the key is set, and once on another day. The PDF requires ≥ 20 calls per API spread over ≥ 2 days. Every run appends to `timing_log.csv`; the error rows from the first run are kept as an honest record.
3. **Re-run Q1** after step 2: execute `q1_calculations.ipynb`, then `python build_spreadsheet.py` and `python build_report.py`. The red placeholder in Section 2.6 of the report disappears once the log is complete.
4. **config.json screenshot.** Open https://huggingface.co/unsloth/Llama-3.3-70B-Instruct/blob/main/config.json (or the gated meta-llama page if you have access) and screenshot it, showing `num_hidden_layers`, `num_key_value_heads` and `head_dim`. Replace the rendered image and the red placeholder in Section 2.4 of the Q1 document.
5. **Review `ai_declaration.md`** and edit it so it matches how you actually used AI tools.
6. Optional: open `q1_calculations.xlsx` in Excel. All formulas recalculate on open.

## Q2 – LoRA comparison (needs a GPU)
7. Open `Q2_LoRA_Comparison/Assignment_Beta_Question_no_2_23K-0028.ipynb` in Google Colab, select a GPU runtime (T4 or better) and choose **Run all**. Expect roughly 2–3 hours on a T4: 7 training runs, plus merged and unmerged evaluation. Set `USE_DRIVE = True` if you want results to survive a disconnect. Re-running skips finished runs.
8. Download the Colab `results/` folder into `Q2_LoRA_Comparison/results/` and run `python Q2_LoRA_Comparison/build_report.py`.
9. Write the result-dependent parts marked in red in the Q2 document:
   - the production choice (Section 4.1);
   - the failure pattern (4.2);
   - the rank-sweep conclusion (Section 3);
   - **what surprised you** (4.4).
10. Check that the report stays within 4 pages for Section 4.

## All questions
11. **PDF exports.** Word's COM automation is not registered on this PC, so `docx2pdf` failed and no PDFs were produced. Either install LibreOffice (the builders then use it automatically) and re-run each `build_report.py`, or open each `.docx` in Word and choose *Save As → PDF*.
12. Read every document once and adjust the wording to your own voice where needed.
