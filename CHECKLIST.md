# Requirement checklist (Assignment Beta PDF → where it is satisfied)

Status: ✅ done · ⏳ code ready, needs your run/input (see TODO_FOR_STUDENT.md) · ⚠️ done with a stated limitation

Abbreviations: Q1 doc = `Q1_SaafHawa/Assignment_Beta_Question_no_1_23K-0028.docx`, nb = notebook.

## Question 1 – SaafHawa (CLO 2)
| Requirement (PDF p. 3–6) | Where | Status |
|---|---|---|
| R, D and every derived value on the first page | Q1 doc, "Parameters" (page 1); nb cell 2; xlsx sheet `Parameters` | ✅ |
| ≥ 6 closed models, ≥ 4 providers | Q1 doc, Section 1 table: 9 closed models from OpenAI, Anthropic, Google and xAI | ✅ |
| ≥ 6 open-weight models, ≥ 4 providers | Q1 doc, Section 1 table: 10 open-weight models from 9 labs | ✅ |
| Params, with MoE total and active | Section 1 table, column 2; `models.csv` | ✅ (closed: "not disclosed") |
| Context window and max output | Section 1 table, column 3 | ⚠️ max output not verified for 2 xAI models and 4 open models |
| Input / output / cached prices; cheapest provider named for open models | Section 1 table, column 4 | ✅ |
| RPM / TPM for a new paid tier | Section 1 table, column 5 | ⚠️ Google and most open providers do not publish them ("not verified") |
| TTFT and throughput | Section 1 table, column 6 | ⚠️ missing for 4 open-model endpoints |
| Two benchmarks, one of them tool use | Section 1 table, columns 7–8 | ⚠️ the tool benchmark differs by family (explained under the table); DeepSeek's is not verified |
| Tool calling, JSON, reasoning settings, setting used | Section 1 table, column 9; `cost_inputs.csv` `reasoning_basis` | ✅ |
| Licence and commercial self-hosting | Section 1 table, column 10 | ✅ |
| Single table with a source and access date for every figure | Section 1: numbered references, all accessed 11 Nov 2026 | ✅ |
| Paragraph naming two unverifiable values and their impact | End of Section 1 | ✅ |
| 2.1 Token volume, with retries, and monthly totals | Q1 doc 2.1; nb Section 2.1; xlsx `Tokens` | ✅ |
| 2.2 Cost with and without caching for all models: write premium, minimum prefix, TTL; which models fit B | Q1 doc 2.2 table; nb 2.2; xlsx `API_costs` | ✅ |
| Reasoning tokens added at the lowest setting (cost and latency) | nb 2.2 (`reasoning_tokens_per_call`); lower bounds flagged | ⚠️ averages not verified for 6 models (flagged as lower bounds) |
| 2.3 Peak QPM/TPM in the heatwave window vs rate limits | Q1 doc 2.3; nb 2.3; xlsx `Peak_load` | ✅ |
| 2.4 Full-attention model and config.json values | Q1 doc 2.4 (Llama 3.3 70B; Hub API + config.json) | ✅ |
| Screenshot of the config values | Q1 doc 2.4 (rendered API response) | ⏳ replace it with your own browser screenshot (TODO 4) |
| Weights at FP16/8/4-bit, KV per sequence at the longest context, max sequences on a real GPU (10% reserved), GPUs needed | Q1 doc 2.4; nb 2.4; xlsx `Self_hosting` | ✅ |
| 2.5 Break-even with a real GPU price, step function, Q*, plot, realism | Q1 doc 2.5 + `results/breakeven.png`; nb 2.5; xlsx `Break_even` | ✅ (result: no Q* exists; explained) |
| 2.6 Latency for 2 candidates, with retries and measured tool delay; architectural change | Q1 doc 2.6; nb 2.6; xlsx `Latency` | ✅ |
| Tool latency: AQ and weather APIs ≥ 20 calls each over ≥ 2 days, heat-index and KB timed, raw log | `tool_latency.py`, `timing_log.csv` | ⏳ OpenAQ key and second-day run needed (TODO 1–3) |
| Recommendation to the technical lead (incl. Urdu/Roman Urdu, municipal summary) | Q1 doc, final section | ✅ |
| Spreadsheet or notebook with the calculations | `q1_calculations.ipynb` and `q1_calculations.xlsx` | ✅ |
| AI-use declaration | `Q1_SaafHawa/ai_declaration.md` | ⏳ review and edit (TODO 5) |

## Question 2 – PEFT comparison (CLO 3)
| Requirement (PDF p. 7–9) | Where | Status |
|---|---|---|
| 1(a) adapter parameters with working | Q2 doc, Section 1(a) | ✅ |
| 1(b) percentage of the layer | Q2 doc, Section 1(b) | ✅ |
| 1(c) B = 0 / A random, and what goes wrong if both are random | Q2 doc, Section 1(c) | ✅ |
| 1(d) QLoRA (NF4, paged optimizers), DoRA (magnitude/direction), AdaLoRA (rank allocation) | Q2 doc, Section 1(d) | ✅ |
| Qwen2.5-1.5B-Instruct, 2,000 glaive examples, 200 held out, PEFT | nb data cell (seeded split saved to `results/data_split.json`) | ✅ code / ⏳ run |
| Base + LoRA + QLoRA NF4 + DoRA + AdaLoRA (12→8), identical setup | nb "Runs 0–4" | ✅ code / ⏳ run |
| Trainable params and %, peak memory, minutes, JSON validity, tool accuracy, full match | nb `run_experiment` → `results/<run>.json`; Q2 doc Section 2 | ✅ code / ⏳ run |
| Extra: hallucinated tool, wrong action, no-call; merged vs unmerged speed | nb `score`/`evaluate_merged`; Q2 doc Section 2 | ✅ code / ⏳ run |
| Section 3: winner at r = 4, 16, 32 (plus 8), plot, conclusion | nb Section 3 → `results/rank_sweep.png`; Q2 doc Section 3 | ✅ code / ⏳ run + conclusion |
| Section 4.5 production choice incl. merge behaviour | Q2 doc 4.1 (merge analysis written) | ⏳ final choice depends on results |
| Section 4.6 five failures with labels and pattern | auto-collected → `results/failures.json`; Q2 doc 4.2 | ⏳ run, then write the pattern |
| Section 4.7 agentic angle and one swap risk | Q2 doc 4.3 | ✅ |
| Section 4.8 what surprised you | Q2 doc 4.4 | ⏳ yours to write |
| Notebook named `Assignment_Beta_Question_no_2_Student_ID` | `Assignment_Beta_Question_no_2_23K-0028.ipynb` | ✅ |
| Notebook smoke-tested | CPU smoke test on Qwen2.5-0.5B (LoRA/DoRA/AdaLoRA, merged eval, sweep); QLoRA needs CUDA, so not smoke-tested | ⚠️ |

## Question 3 – Distillation (CLO 3)
| Requirement (PDF p. 10) | Where | Status |
|---|---|---|
| (a) probabilities at T = 1 | Q3 doc (a); `q3_distillation.ipynb` | ✅ |
| (b) T = 2 probabilities | Q3 doc (b) | ✅ |
| (c) KL(p_T‖q_T) | Q3 doc (c) | ✅ |
| (d) hard-label CE | Q3 doc (d) | ✅ |
| (e) total loss with α T² | Q3 doc (e) | ✅ |
| (f) gradient w.r.t. student logits | Q3 doc (f); finite-difference check in the notebook | ✅ |
| (g) updated logits (η = 0.5) and new loss | Q3 doc (g) | ✅ |
| Format (none specified): docx + notebook | both present | ✅ |

## Question 4 – LLM evaluation (CLO 4)
| Requirement (PDF p. 11–12) | Where | Status |
|---|---|---|
| 1 accuracy and 95% CI (Wald formula stated) | Q4 doc Parts 1–3; nb | ✅ |
| 2 per-class P/R/F1 | Q4 doc | ✅ |
| 3 macro / weighted / micro F1 | Q4 doc | ✅ |
| 4 interpretation and recommendations | Q4 doc Part 4 | ✅ |
| 5 Stage 2 metrics and comparison | Q4 doc Part 5 | ✅ |
| 6 mean ± std (sample and population; sample used) | Q4 doc Part 6 | ✅ |
| 7 BLEU-4 (smoothing stated), ROUGE-1/2/L, METEOR | Q4 doc Part 7 | ✅ |
| 8 perplexity and interpretation | Q4 doc Part 8 | ✅ |
| Manual working agrees with libraries | `assert`s in `Assignment_Beta_Question_no_4_23K-0028.ipynb` | ✅ |
| Notebook named `Assignment_Beta_Question_no_4_Student_ID` | ✅ | ✅ |

## Question 5 – Paper summary (CLO 3)
| Requirement (PDF p. 12) | Where | Status |
|---|---|---|
| Two-page summary from the full text | `Q5_RAG_Paper_Summary/Assignment_Beta_Question_no_5_23K-0028.docx` | ⚠️ page count not checked in Word (no PDF converter here) |

## Repository-wide
| Item | Status |
|---|---|
| PDF exports of every document | ⏳ Word COM is unavailable on this PC (TODO 11) |
| No secrets committed; `.env` git-ignored; `.env.example` provided | ✅ |
| `requirements.txt` pinned; README with setup and reproduction steps | ✅ |
