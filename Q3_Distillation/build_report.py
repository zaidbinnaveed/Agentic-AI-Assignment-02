"""Builds the Q3 hand-working document from results/q3_results.json (run q3_distillation.ipynb first)."""
import json
import math as m
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from common.docx_utils import bullet, math, new_document, para, save_with_pdf, table  # noqa: E402

R = {k: v for k, v in json.loads((HERE / "results/q3_results.json").read_text()).items()}
WORDS = ["hospital", "clinic", "ward", "school"]
Z_T, Z_S = [5.0, 3.0, 2.0, 0.0], [3.0, 2.5, 1.0, 0.5]
T, ALPHA, ETA = 2.0, 0.5, 0.5


def f(x, d=4):
    return f"{x:.{d}f}"


def softmax_steps(doc, name, z, temp, probs):
    scaled = [v / temp for v in z]
    exps = [m.exp(v) for v in scaled]
    total = sum(exps)
    lhs = f"z/{temp:g}" if temp != 1 else "z"
    math(doc, f"{name}: {lhs} = [{', '.join(f'{v:g}' for v in scaled)}]")
    math(doc, f"  e^({lhs}) = [{', '.join(f(e) for e in exps)}]")
    math(doc, f"  sum = {' + '.join(f(e) for e in exps)} = {f(total)}")
    for w, e, p in zip(WORDS, exps, probs):
        math(doc, f"  P({w:8s}) = {f(e)} / {f(total)} = {f(p)}")


doc = new_document("Question 3 - Knowledge Distillation", "Every step worked by hand; numbers cross-checked in q3_distillation.ipynb")

para(doc, "Setup", bold=True)
math(doc, "Vocabulary  : [hospital, clinic, ward, school]     y = [1, 0, 0, 0]")
math(doc, "Teacher z_t : [5.0, 3.0, 2.0, 0.0]")
math(doc, "Student z_s : [3.0, 2.5, 1.0, 0.5]")
math(doc, "T = 2, alpha = 0.5, eta = 0.5, natural log (ln)")
math(doc, "L = alpha * T^2 * KL(p_T || q_T) + (1 - alpha) * CE(y, q_1)")
math(doc, "softmax(z / T)_i = exp(z_i / T) / sum_j exp(z_j / T)")

doc.add_heading("(a) Probabilities at T = 1", level=2)
softmax_steps(doc, "Teacher p_1", Z_T, 1, R["p1"])
softmax_steps(doc, "Student q_1", Z_S, 1, R["q1"])
para(doc, "The teacher is very confident in 'hospital' (0.839); the student only gives it 0.548 and puts a third of its mass on 'clinic'.")

doc.add_heading("(b) Softened probabilities at T = 2", level=2)
softmax_steps(doc, "Teacher p_T", Z_T, T, R["pT"])
softmax_steps(doc, "Student q_T", Z_S, T, R["qT"])
para(doc, "Dividing logits by T = 2 halves the gaps between them, so both distributions flatten. The teacher's 'dark knowledge' becomes "
          "visible: clinic (0.220) and ward (0.133) are clearly ranked above school (0.049).")

doc.add_heading("(c) KL divergence KL(p_T || q_T)", level=2)
math(doc, "KL = sum_i p_T,i * ln(p_T,i / q_T,i)")
for w, p, q, term in zip(WORDS, R["pT"], R["qT"], R["kl_terms"]):
    math(doc, f"  {w:8s}: {f(p)} * ln({f(p)} / {f(q)}) = {f(p)} * ({f(m.log(p / q))}) = {f(term, 5)}")
math(doc, f"  KL = {' + '.join(f(t, 5) for t in R['kl_terms'])} = {f(R['kl'], 5)} nats")

doc.add_heading("(d) Hard-label cross-entropy CE(y, q_1)", level=2)
math(doc, "CE = -sum_i y_i ln q_1,i = -ln q_1,hospital   (only y_1 = 1)")
math(doc, f"   = -ln({f(R['q1'][0])}) = {f(R['ce'], 5)} nats")

doc.add_heading("(e) Total distillation loss", level=2)
math(doc, f"alpha * T^2 * KL = 0.5 * 4 * {f(R['kl'], 5)} = {f(ALPHA * T * T * R['kl'], 5)}")
math(doc, f"(1 - alpha) * CE = 0.5 * {f(R['ce'], 5)} = {f((1 - ALPHA) * R['ce'], 5)}")
math(doc, f"L = {f(ALPHA * T * T * R['kl'], 5)} + {f((1 - ALPHA) * R['ce'], 5)} = {f(R['loss'], 5)}")
para(doc, "The T^2 factor restores the scale of the soft-target gradients, which shrink by 1/T^2 when logits are divided by T, so the two "
          "terms stay comparable as T changes (Hinton et al., 2015).")

doc.add_heading("(f) Gradient with respect to the student logits", level=2)
para(doc, "Derivation:")
math(doc, "d softmax(z/T) / dz combined with KL gives  dKL/dz_s = (1/T) * (q_T - p_T)")
math(doc, "Softmax + cross-entropy gives                dCE/dz_s = q_1 - y")
math(doc, "dL/dz_s = alpha * T^2 * (1/T)(q_T - p_T) + (1 - alpha)(q_1 - y)")
math(doc, "        = alpha * T * (q_T - p_T) + (1 - alpha)(q_1 - y)")
math(doc, "        = 1.0 * (q_T - p_T) + 0.5 * (q_1 - y)")
rows = []
for i, w in enumerate(WORDS):
    rows.append([w, f(R["qT"][i]), f(R["pT"][i]), f(R["grad_soft"][i], 5), f(R["q1"][i]), f(1.0 if i == 0 else 0.0, 0),
                 f(R["grad_hard"][i], 5), f(R["grad"][i], 5)])
table(doc, ["word", "q_T", "p_T", "1.0(q_T-p_T)", "q_1", "y", "0.5(q_1-y)", "dL/dz_s"], rows)
math(doc, f"grad = [{', '.join(f(g, 5) for g in R['grad'])}]   (components sum to 0, as expected for softmax logits)")
para(doc, "The gradient is negative only for 'hospital', so a descent step raises that logit and lowers the others. A finite-difference "
          "check in the notebook agrees with this analytic gradient to about 1e-10.")

doc.add_heading("(g) One gradient-descent step (eta = 0.5) and the new loss", level=2)
math(doc, "z_s' = z_s - eta * grad")
for i, w in enumerate(WORDS):
    math(doc, f"  {w:8s}: {Z_S[i]:.1f} - 0.5 * ({f(R['grad'][i], 5)}) = {f(R['z_new'][i], 5)}")
para(doc, "New distributions (same softmax steps as above):")
softmax_steps(doc, "Student q_T'", R["z_new"], T, R["qT_new"])
softmax_steps(doc, "Student q_1'", R["z_new"], 1, R["q1_new"])
math(doc, "KL' = " + " + ".join(f(p * m.log(p / q), 5) for p, q in zip(R["pT"], R["qT_new"])) + f" = {f(R['kl_new'], 5)}")
math(doc, f"CE' = -ln({f(R['q1_new'][0])}) = {f(R['ce_new'], 5)}")
math(doc, f"L'  = 0.5 * 4 * {f(R['kl_new'], 5)} + 0.5 * {f(R['ce_new'], 5)} = {f(R['loss_new'], 5)}")
para(doc, "Summary", bold=True)
bullet(doc, f"Loss fell from {f(R['loss'])} to {f(R['loss_new'])} ({f(R['loss_new'] - R['loss'])}, "
            f"{100 * (R['loss'] - R['loss_new']) / R['loss']:.1f}% lower) after one step.")
bullet(doc, f"Both terms improved: KL {f(R['kl'])} -> {f(R['kl_new'])} and CE {f(R['ce'])} -> {f(R['ce_new'])}.")
bullet(doc, f"The student's probability for 'hospital' rose from {f(R['q1'][0])} to {f(R['q1_new'][0])}; at T = 2 its mass on 'clinic' "
            f"fell from {f(R['qT'][1])} to {f(R['qT_new'][1])}, moving towards the teacher's {f(R['pT'][1])}.")

save_with_pdf(doc, HERE / "Assignment_Beta_Question_no_3_23K-0028.docx")
print("written Assignment_Beta_Question_no_3_23K-0028.docx")
