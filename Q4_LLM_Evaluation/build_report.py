"""Builds the Q4 solution document from results/q4_results.json (run the Q4 notebook first)."""
import json
import math as m
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from common.docx_utils import bullet, math, new_document, para, save_with_pdf, table  # noqa: E402

R = json.loads((HERE / "results/q4_results.json").read_text())
CLASSES = ["Positive", "Negative", "Neutral"]


def f(x, d=4):
    return f"{x:.{d}f}"


def classification_section(doc, title, s):
    doc.add_heading(title, level=2)
    cm = s["confusion"]
    table(doc, ["Actual \\ Predicted", *CLASSES, "Row total"],
          [[c, *cm[i], s["row_totals"][i]] for i, c in enumerate(CLASSES)] + [["Column total", *s["col_totals"], s["n"]]])

    para(doc, "Accuracy and 95% confidence interval", bold=True)
    acc, n = s["accuracy"], s["n"]
    math(doc, f"Accuracy = (TP_pos + TP_neg + TP_neu) / n = ({' + '.join(map(str, s['tp']))}) / {n} = {s['correct']}/{n} = {f(acc)}")
    math(doc, "Wald 95% CI: p_hat +/- z * sqrt(p_hat (1 - p_hat) / n),  z = 1.96")
    math(doc, f"  SE = sqrt({f(acc)} * {f(1 - acc)} / {n}) = {f(m.sqrt(acc * (1 - acc) / n), 5)}")
    math(doc, f"  half-width = 1.96 * {f(m.sqrt(acc * (1 - acc) / n), 5)} = {f(s['wald_half_width'])}")
    math(doc, f"  CI = [{f(s['wald_ci'][0])}, {f(s['wald_ci'][1])}]   (Wilson check: [{f(s['wilson_ci'][0])}, {f(s['wilson_ci'][1])}])")

    para(doc, "Per-class precision, recall, F1", bold=True)
    math(doc, "P_c = TP_c / column_c    R_c = TP_c / row_c    F1_c = 2 P_c R_c / (P_c + R_c)")
    rows = []
    for i, c in enumerate(CLASSES):
        p, r, f1 = s["precision"][i], s["recall"][i], s["f1"][i]
        math(doc, f"  {c:8s}: P = {s['tp'][i]}/{s['col_totals'][i]} = {f(p)}, R = {s['tp'][i]}/{s['row_totals'][i]} = {f(r)}, "
                  f"F1 = 2*{f(p)}*{f(r)}/({f(p)}+{f(r)}) = {f(f1)}")
        rows.append([c, f(p), f(r), f(f1), s["row_totals"][i]])
    table(doc, ["Class", "Precision", "Recall", "F1", "Support"], rows)

    para(doc, "Averaged F1", bold=True)
    f1s, sup = s["f1"], s["row_totals"]
    math(doc, f"Macro    = ({' + '.join(f(x) for x in f1s)}) / 3 = {f(s['macro_f1'])}")
    math(doc, f"Weighted = ({' + '.join(f'{w}*{f(x)}' for w, x in zip(sup, f1s))}) / {n} = {f(s['weighted_f1'])}")
    math(doc, f"Micro    : sum TP = {s['correct']}, sum FP = sum FN = {n - s['correct']} (every error is one FP and one FN)")
    math(doc, f"           P_micro = R_micro = {s['correct']}/{n} = {f(s['micro_f1'])}  ->  Micro F1 = {f(s['micro_f1'])} = accuracy")
    para(doc, "scikit-learn (precision_recall_fscore_support, f1_score) returns identical values; the notebook asserts this.", italic=True)


doc = new_document("Question 4 - Evaluating an LLM Sentiment Classifier",
                   "Manual working with library cross-checks (Assignment_Beta_Question_no_4_23K-0028.ipynb)")
s1, s2 = R["stage1_zero_shot"], R["stage2_few_shot"]

doc.add_heading("Parts 1-3: Stage 1 (zero-shot)", level=1)
classification_section(doc, "Stage 1 metrics", s1)

doc.add_heading("Part 4: Interpreting Stage 1", level=1)
cmp_ = R["comparison"]
errs = sorted(cmp_["stage1_errors"].items(), key=lambda kv: -kv[1])
para(doc, f"Stage 1 makes {cmp_['total_errors_stage1']} errors. {cmp_['errors_involving_neutral']} of them "
          f"({100 * cmp_['errors_involving_neutral'] / cmp_['total_errors_stage1']:.0f}%) involve the Neutral class:")
for k, v in errs:
    bullet(doc, f"{k}: {v}")
para(doc, "Where it fails:", bold=True)
bullet(doc, f"Neutral is the weak class (F1 {f(s1['f1'][2])} vs {f(s1['f1'][0])} Positive and {f(s1['f1'][1])} Negative). "
            f"Its recall is only {f(s1['recall'][2])}: 30 of 80 neutral reviews are pushed to a polar label.")
bullet(doc, "The biggest single error is Neutral -> Positive (20). Mixed reviews ('late delivery but good product') are being read as "
            "positive, so the model latches onto the positive clause.")
bullet(doc, "It also over-uses Neutral for clear reviews (Positive -> Neutral 15, Negative -> Neutral 12), so Neutral precision is "
            f"low too ({f(s1['precision'][2])}). Without a definition the model treats 'Neutral' as an 'unsure' bucket.")
bullet(doc, f"Polarity flips are rare (Negative <-> Positive = {cmp_['stage1_errors']['Negative->Positive'] + cmp_['stage1_errors']['Positive->Negative']}). "
            "The model knows positive from negative; the problem is the decision boundary around Neutral.")
bullet(doc, f"Macro F1 ({f(s1['macro_f1'])}) is below weighted F1 ({f(s1['weighted_f1'])}) because the worst class is also the smallest.")
para(doc, "Recommendations:", bold=True)
for r in ["Define Neutral explicitly in the prompt (factual, mixed, or no clear opinion) and state how to label mixed reviews.",
          "Add balanced few-shot examples, including borderline mixed reviews, and shuffle their order to avoid recency/label bias.",
          "Ask for a one-line justification before the label (or a short reasoning step) so mixed signals are weighed explicitly.",
          "Constrain the output to exactly one of the three labels (structured output) and audit low-confidence cases.",
          "Re-check the annotation guidelines: if annotators were inconsistent about mixed reviews, no prompt can fix that."]:
    bullet(doc, r)
para(doc, "Stage 2 applies the first two recommendations.")

doc.add_heading("Part 5: Stage 2 (improved prompt) and comparison", level=1)
classification_section(doc, "Stage 2 metrics", s2)
para(doc, "Comparison", bold=True)
rows = [[k, f(s1[k]), f(s2[k]), f"{s2[k] - s1[k]:+.4f}"] for k in ("accuracy", "macro_f1", "weighted_f1", "micro_f1")]
rows += [[f"F1 {c}", f(s1["f1"][i]), f(s2["f1"][i]), f"{s2['f1'][i] - s1['f1'][i]:+.4f}"] for i, c in enumerate(CLASSES)]
table(doc, ["Metric", "Stage 1", "Stage 2", "Change"], rows)
bullet(doc, f"Every metric improves. Accuracy rises by {100 * (s2['accuracy'] - s1['accuracy']):.1f} points; Neutral F1 gains the most "
            f"(+{s2['f1'][2] - s1['f1'][2]:.4f}), which shows the fix targeted the actual weakness.")
bullet(doc, "Neutral -> Positive errors fall from 20 to 9 and Positive -> Neutral from 15 to 10. The definition and mixed examples did their job.")
bullet(doc, f"Macro F1 now trails weighted F1 by only {s2['weighted_f1'] - s2['macro_f1']:.4f}, so the classes are more balanced.")
bullet(doc, f"Caution: the two Wald intervals overlap slightly ([{f(s1['wald_ci'][0])}, {f(s1['wald_ci'][1])}] vs "
            f"[{f(s2['wald_ci'][0])}, {f(s2['wald_ci'][1])}]). Overlap does not prove the gain is noise, though. Both stages scored "
            "the same 300 reviews, so the right test is a paired McNemar test on per-review outcomes, and those are not provided.")

doc.add_heading("Part 6: Prompt stability over 5 orderings", level=1)
st = R["stability"]
runs = st["runs"]
math(doc, f"mean = ({' + '.join(f'{x:.3f}' for x in runs)}) / 5 = {sum(runs):.3f}/5 = {f(st['mean'])}")
math(doc, "deviations x_i - mean = [" + ", ".join(f"{x - st['mean']:+.4f}" for x in runs) + "]")
math(doc, f"sum of squared deviations = {st['sum_sq_dev']:.7f}")
math(doc, f"sample std     s     = sqrt({st['sum_sq_dev']:.7f} / (5 - 1)) = {f(st['std_sample'])}")
math(doc, f"population std sigma = sqrt({st['sum_sq_dev']:.7f} / 5)       = {f(st['std_population'])}")
para(doc, f"Reported: accuracy = {f(st['mean'])} +/- {f(st['std_sample'])} (sample std).", bold=True)
para(doc, "I use the sample (n - 1) standard deviation because the five orderings are a sample from the many possible example "
          "orderings. The goal is to estimate the spread over all of them, and dividing by n would understate it. The population "
          "value is shown for completeness.")
para(doc, f"Stability: the spread is {100 * (st['range'][1] - st['range'][0]):.1f} points ({st['range'][0]:.3f}-{st['range'][1]:.3f}) and "
          f"the coefficient of variation is {st['cv_percent']:.2f}%. That is roughly six times smaller than the sampling uncertainty of a "
          f"single run (Wald half-width approx. {f(st['single_run_wald_half_width'])}). Example ordering has little effect, and the "
          "Stage 2 gain is not an artefact of one lucky ordering. Five runs is still a small sample, so I would report "
          "the mean of several orderings rather than any single run.")

doc.add_heading("Part 7: Quality of the generated justification", level=1)
t = R["text_metrics"]
math(doc, f"Reference (r = {t['r_len']}): {t['reference']}")
math(doc, f"Candidate (c = {t['c_len']}): {t['candidate']}")
para(doc, "BLEU-4", bold=True)
for n_, (h, tot) in t["bleu_ngram"].items():
    math(doc, f"  p_{n_} (clipped {n_}-gram precision) = {h}/{tot} = {f(h / tot)}")
math(doc, f"  BP = exp(1 - r/c) = exp(1 - {t['r_len']}/{t['c_len']}) = {f(t['brevity_penalty'])}   (c < r)")
logs = [m.log(h / tot) for h, tot in t["bleu_ngram"].values()]
math(doc, f"  BLEU-4 = BP * exp(0.25 * ({' + '.join(f(x) for x in logs)})) = {f(t['brevity_penalty'])} * {f(m.exp(sum(logs) / 4))} = {f(t['bleu4'])}")
para(doc, "Smoothing: NLTK SmoothingFunction().method1. All four n-gram counts are non-zero, so smoothing changes nothing; "
          "smoothed and unsmoothed NLTK BLEU both equal the manual value.", italic=True)
para(doc, "ROUGE (rouge-score library, no stemming)", bold=True)
rg = t["rouge"]
math(doc, f"  ROUGE-1: overlap 8 -> P = 8/9 = {f(rg['rouge1']['precision'])}, R = 8/10 = {f(rg['rouge1']['recall'])}, F1 = {f(rg['rouge1']['f1'])}")
math(doc, f"  ROUGE-2: overlap 5 -> P = 5/8 = {f(rg['rouge2']['precision'])}, R = 5/9 = {f(rg['rouge2']['recall'])}, F1 = {f(rg['rouge2']['f1'])}")
math(doc, f"  ROUGE-L: LCS = {t['lcs']} ('the product quality is good') -> P = 5/9 = {f(rg['rougeL']['precision'])}, "
          f"R = 5/10 = {f(rg['rougeL']['recall'])}, F1 = {f(rg['rougeL']['f1'])}")
para(doc, "METEOR (NLTK: alpha = 0.9, beta = 3, gamma = 0.5)", bold=True)
mt = t["meteor"]
math(doc, f"  matches m = {mt['matches']} (exact). 'slow' vs 'late' share no WordNet synset, so no synonym match.")
math(doc, f"  P = 8/9 = {f(mt['precision'])}, R = 8/10 = {f(mt['recall'])}")
math(doc, f"  Fmean = P*R / (0.9 P + 0.1 R) = {f(mt['fmean'])}")
math(doc, f"  chunks = {mt['chunks']} ['the product quality is good'] ['but'] ['delivery was']")
math(doc, f"  penalty = 0.5 * ({mt['chunks']}/{mt['matches']})^3 = {f(mt['penalty'])}")
math(doc, f"  METEOR = {f(mt['fmean'])} * (1 - {f(mt['penalty'])}) = {f(mt['score'])}")
table(doc, ["Metric", "Score"], [["BLEU-4", f(t["bleu4"])], ["ROUGE-1 F1", f(rg["rouge1"]["f1"])], ["ROUGE-2 F1", f(rg["rouge2"]["f1"])],
                                ["ROUGE-L F1", f(rg["rougeL"]["f1"])], ["METEOR", f(mt["score"])]])
para(doc, "Interpretation: the candidate says the same thing as the reference with its two clauses swapped, and 'slow' in place of "
          "'late'. Unigram metrics (ROUGE-1 0.84, METEOR 0.79) are high because 8 of 9 words match. BLEU-4 (0.475) and ROUGE-L "
          "(0.53) are much lower because the reordering breaks long n-grams and the common subsequence. None of the metrics credit "
          "the near-synonym. For short justifications, n-gram overlap underrates semantically equivalent text. An embedding metric "
          "(e.g. BERTScore) or human/LLM-judge rating would suit this check better.")

doc.add_heading("Part 8: Perplexity of the justification", level=1)
pp = R["perplexity"]
math(doc, "PPL = exp( -(1/N) * sum_i ln p_i ),  N = 9")
for i, (p, lp) in enumerate(zip(pp["probs"], pp["ln_probs"]), 1):
    math(doc, f"  token {i}: ln({p:.2f}) = {lp:+.4f}")
math(doc, f"  sum ln p = {f(pp['sum_ln'])}")
math(doc, f"  average NLL = {f(-pp['sum_ln'])} / 9 = {f(pp['avg_nll'])} nats")
math(doc, f"  PPL = exp({f(pp['avg_nll'])}) = {f(pp['ppl'])}   (check: 1 / geometric-mean p = 1/{f(pp['geo_mean'])} = {f(pp['ppl'])})")
para(doc, f"Interpretation: PPL = {pp['ppl']:.2f} means that, on average, the model was as uncertain at each step as if it were choosing "
          f"uniformly among about {pp['ppl']:.1f} tokens; the average token probability (geometric mean) is {pp['geo_mean']:.2f}. "
          "That is fairly confident for free text. Mapping one token to one word (assumed, since 9 tokens = 9 words), the least "
          "confident tokens are 'but' (0.30), 'delivery' (0.25) and 'slow' (0.20). That is the second clause about the negative "
          "aspect, the part a mixed review makes hard, and 'slow' is the very word that differs from the reference. Perplexity measures "
          "the model's confidence in its own output, not correctness. It is only comparable across texts scored by the same model "
          "and tokenizer.")

save_with_pdf(doc, HERE / "Assignment_Beta_Question_no_4_23K-0028.docx")
print("written Assignment_Beta_Question_no_4_23K-0028.docx")
