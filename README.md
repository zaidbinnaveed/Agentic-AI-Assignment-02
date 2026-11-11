# Agentic AI (AI4015) – Assignment Beta, Fall 2026

Zaid Bin Naveed · Roll No. 23K-0028 · FAST-NUCES Karachi

Each question folder has its working (notebook or scripts), a `results/` folder, a `build_report.py` that writes the Word deliverable from those results, and the deliverable itself (`Assignment_Beta_Question_no_<n>_23K-0028.docx`, plus a PDF export).

| Folder | Question | What is inside |
|---|---|---|
| `Q1_SaafHawa/` | Closed API vs self-hosted open model for the SaafHawa WhatsApp agent | `models.csv` holds the raw research for 19 models, with a source URL per field. `cost_inputs.csv` holds the numbers used in the calculations. `q1_calculations.ipynb` and `q1_calculations.xlsx` contain the calculations with live formulas. `tool_latency.py` measures the tools and writes `timing_log.csv`, the raw timing log. `knowledge_base.json` holds the NDMA, WHO, EPA and NWS advisories. `research_notes/` explains how each value was found. `ai_declaration.md` is the AI-use declaration. |
| `Q2_LoRA_Comparison/` | LoRA vs QLoRA vs DoRA vs AdaLoRA on Qwen2.5-1.5B-Instruct for function calling | `Assignment_Beta_Question_no_2_23K-0028.ipynb` is the Colab notebook: base model plus the 4 methods, rank sweep, merged vs unmerged speed, and failure collection. `build_report.py` turns `results/*.json` into the report. |
| `Q3_Distillation/` | Knowledge-distillation loss, gradient and one update step | `q3_distillation.ipynb` holds the numpy working with a finite-difference gradient check. The report shows every step by hand. |
| `Q4_LLM_Evaluation/` | Confusion-matrix metrics, prompt stability, BLEU/ROUGE/METEOR, perplexity | `Assignment_Beta_Question_no_4_23K-0028.ipynb` does every metric by hand and asserts that it matches scikit-learn, NLTK and rouge-score. |
| `Q5_RAG_Paper_Summary/` | Two-page summary of Ersoy & Erşahin (2025), IEEE Access 13:194185 | `build_summary.py` and the summary document. |
| `common/` | Shared helpers | `docx_utils.py`: document styling and PDF export. |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
copy .env.example .env            # then put your OpenAQ v3 key in .env (Q1 only)
```

PDF export uses LibreOffice (`soffice`) if it is installed, and otherwise Microsoft Word through `docx2pdf`. If neither works, the `.docx` is still written. You can then export it from Word with *File → Save As → PDF*.

## Reproduce

```bash
# Q1
cd Q1_SaafHawa
python tool_latency.py --n 25                  # run on two different days; appends to timing_log.csv
jupyter nbconvert --to notebook --execute --inplace q1_calculations.ipynb
python build_spreadsheet.py && python build_report.py

# Q2: open the notebook in Google Colab (GPU runtime, T4 or better), Run all,
# download results/ into Q2_LoRA_Comparison/results/, then:
python Q2_LoRA_Comparison/build_report.py

# Q3, Q4
jupyter nbconvert --to notebook --execute --inplace Q3_Distillation/q3_distillation.ipynb
python Q3_Distillation/build_report.py
jupyter nbconvert --to notebook --execute --inplace Q4_LLM_Evaluation/Assignment_Beta_Question_no_4_23K-0028.ipynb
python Q4_LLM_Evaluation/build_report.py

# Q5
python Q5_RAG_Paper_Summary/build_summary.py
```

Run the notebooks from inside their own folder (nbconvert does this automatically), because they read and write `results/` relative to the notebook.

## Conventions

* No figure is invented. Every external number in Q1 has a source URL and an access date (11 Nov 2026), and values that could not be verified are written as "not verified".
* Results that need hardware I don't have locally (the Q2 GPU runs, the second-day timing run) are clearly marked placeholders in the documents. They are listed in `TODO_FOR_STUDENT.md`.
* `CHECKLIST.md` maps every requirement in the assignment PDF to the file and section that satisfies it.
