# What you still need to run or supply

## Q1 – SaafHawa
1. ~~**OpenAQ API key.**~~ Done: the key is in `.env` (git-ignored). The first OpenAQ run on 17 Nov 2026 got 25/25 OK, median 679 ms (station 5188633, Lyari).
2. **One more timing run on another day (air quality only).** Weather, heat index and KB already have ≥ 20 OK calls over 2 days (11 and 17 Nov). Air quality has 25 OK calls on 17 Nov only. On **any later day**, run `python tool_latency.py --n 25` from `Q1_SaafHawa/`. Every run appends to `timing_log.csv`; error rows from the keyless runs are kept as an honest record.
3. **Re-run Q1** after step 2: `jupyter nbconvert --to notebook --execute --inplace q1_calculations.ipynb`, then `python build_spreadsheet.py` and `python build_report.py`. The red placeholder in Section 2.6 disappears once air quality has 2 days.
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
11. ~~**PDF exports.**~~ Done (17 Nov 2026): LibreOffice is installed, and every builder now writes a PDF next to its `.docx`. Re-running a builder refreshes its PDF. Q5 was checked and fits on exactly 2 pages.
12. Read every document once and adjust the wording to your own voice where needed.
