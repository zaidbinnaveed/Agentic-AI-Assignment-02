"""Builds the Q2 report from results/*.json written by Assignment_Beta_Question_no_2_23K-0028.ipynb.

Run after copying the notebook's results/ folder from Colab into Q2_LoRA_Comparison/results/
(or pass another results folder as the first argument).
Sections that depend on results that do not exist yet are written as clearly marked placeholders.
"""
import json
import sys
from pathlib import Path

from docx.shared import Cm

HERE = Path(__file__).parent
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results"
sys.path.insert(0, str(HERE.parent))
from common.docx_utils import bullet, math, new_document, para, placeholder, rich, save_with_pdf, table  # noqa: E402

METHODS = ["base", "lora_r8", "qlora_r8", "dora_r8", "adalora_r8"]
LABELS = {"base": "Base (no tuning)", "lora_r8": "LoRA r=8", "qlora_r8": "QLoRA r=8 (NF4)", "dora_r8": "DoRA r=8",
          "adalora_r8": "AdaLoRA r 12->8"}


def load(name):
    path = RES / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


runs = {m: load(m) for m in METHODS}
done = {m: r for m, r in runs.items() if r}
winner = json.loads((RES / "winner.json").read_text())["winner"] if (RES / "winner.json").exists() else None
failures = json.loads((RES / "failures.json").read_text()) if (RES / "failures.json").exists() else None
env = next(iter(done.values()), {})

doc = new_document("Question 2 - LoRA vs QLoRA vs DoRA vs AdaLoRA for Tool Calling")

doc.add_heading("Parameters and setup", level=1)
table(doc, ["Item", "Value"], [
    ["Student", "Zaid Bin Naveed, roll no. 23K-0028"],
    ["Notebook", "Assignment_Beta_Question_no_2_23K-0028.ipynb (Google Colab)"],
    ["Base model", "Qwen/Qwen2.5-1.5B-Instruct (1,543,714,304 parameters)"],
    ["Data", "glaiveai/glaive-function-calling-v2, first 2,000 usable rows after a seeded shuffle; parsed into "
             "(user message + function schemas -> one JSON function call); 1,800 train / 200 held-out test"],
    ["Fixed across runs", "seed 42; 2 epochs; LR 2e-4, cosine schedule, 3% warm-up; effective batch 16; max length 768; "
                          "target modules q,k,v,o,gate,up,down; alpha 16; dropout 0.05; gradient checkpointing; greedy decoding"],
    ["Hardware", f"{env.get('gpu', '[PLACEHOLDER - filled from results after the Colab run]')}, {env.get('dtype', '')}"],
    ["Libraries", f"torch {env.get('torch', '?')}, transformers {env.get('transformers', '4.57.6')}, peft {env.get('peft', '0.17.1')}"],
], font_pt=9)

doc.add_heading("Section 1 - LoRA arithmetic and the 'why does this exist?' question", level=1)
para(doc, "(a) Trainable parameters added by a rank-16 adapter on a 4096 x 4096 matrix", bold=True)
math(doc, "W0 in R^(d x k), d = k = 4096.  Update: dW = B A,  B in R^(d x r),  A in R^(r x k),  r = 16")
math(doc, "|A| = r x k = 16 x 4,096 = 65,536")
math(doc, "|B| = d x r = 4,096 x 16 = 65,536")
math(doc, "Total = 2 x 4,096 x 16 = 131,072 trainable parameters")
para(doc, "(b) Share of the original layer", bold=True)
math(doc, "|W0| = 4,096 x 4,096 = 16,777,216")
math(doc, "131,072 / 16,777,216 = 0.0078125 = 0.78125%    (in general r(d+k)/(dk) = 2r/d = 32/4,096)")
para(doc, "(c) Why B starts at zero and A starts random", bold=True)
para(doc, "With B = 0, dW = BA = 0, so at step 0 the adapted model is exactly the pretrained model and fine-tuning starts from a "
          "known-good point. A random A is still needed for learning to begin. For h = W0x + BAx, the gradients are "
          "dL/dB = (dL/dh)(Ax)^T and dL/dA = B^T (dL/dh) x^T. With A random, Ax != 0, so B gets a non-zero gradient on the first "
          "step. A's gradient is zero at first (B = 0), but becomes non-zero as soon as B has moved. If both were zero, both "
          "gradients would stay zero forever and nothing would train. If both were random, dW = BA would be a random matrix "
          "(scaled by alpha/r) added to every adapted layer before any training. The first forward pass would then corrupt the "
          "pretrained behaviour, the initial loss would be higher, and the first steps would be spent undoing that noise. That can "
          "destabilise training, and for a tool-calling model it immediately damages the JSON formatting it already knew.")
para(doc, "(d) What each variant fixes that plain LoRA does not", bold=True)
rich(doc, [("QLoRA (Dettmers et al., 2023, arXiv:2305.14314). ", "b"),
           ("Plain LoRA still keeps the frozen base in 16-bit, so the base weights dominate memory (about 3.1 GB here, 140 GB for a "
            "70B model). QLoRA stores the frozen base in 4-bit NormalFloat (NF4), a data type whose quantisation levels are "
            "quantiles of a normal distribution. That suits pretrained weights, which are roughly normally distributed. It also "
            "double-quantises the quantisation constants, and backpropagates through the dequantised weights into 16-bit LoRA "
            "adapters. Paged optimizers use NVIDIA unified memory to move optimizer state to CPU RAM during memory spikes, such as "
            "long sequences with gradient checkpointing, instead of crashing with out-of-memory. The result is that a 65B model can "
            "be fine-tuned on one 48 GB GPU.", "")])
rich(doc, [("DoRA (Liu et al., 2024, arXiv:2402.09353). ", "b"),
           ("DoRA splits every weight into a magnitude vector and a direction: W = m * V / ||V||_c, with column-wise norm "
            "||.||_c. The magnitude m is trained directly, and the direction is updated with LoRA: V = W0 + BA. The authors found "
            "that LoRA changes magnitude and direction together, in a fixed proportion, while full fine-tuning can change them "
            "independently. Decoupling them makes DoRA learn more like full fine-tuning and usually gives better accuracy at the same "
            "rank, especially at low rank. After merging it has no inference overhead. Unmerged, it pays for the norm computation on "
            "every forward pass.", "")])
rich(doc, [("AdaLoRA (Zhang et al., 2023, arXiv:2303.10512). ", "b"),
           ("Plain LoRA gives every adapted matrix the same rank, although some layers and modules need more capacity than others. "
            "AdaLoRA writes each update in SVD form, dW = P Lambda Q, with an orthogonality regulariser on P and Q. It scores every "
            "singular triplet by importance: the sensitivity |w * dL/dw| smoothed over steps and combined with its uncertainty. "
            "Under a global budget that shrinks on a schedule (here from an average rank of 12 to 8), it prunes the least important "
            "singular values, so the remaining rank goes where the loss is most sensitive.", "")])


def fmt(v, d=1):
    return "-" if v is None else (f"{v:,.{d}f}" if isinstance(v, float) else f"{v:,}")


doc.add_heading("Section 2 - Results on the 200 held-out examples", level=1)
if done:
    rows = []
    for m in METHODS:
        r = runs[m]
        if not r:
            rows.append([LABELS[m]] + ["[PLACEHOLDER - run missing]"] + [""] * 9)
            continue
        merged = r.get("merged") or {}
        rows.append([LABELS[m], f"{r['trainable_params']:,} ({r['trainable_pct']:.3f}%)", fmt(r.get("peak_train_mem_gb"), 2),
                     fmt(r["train_minutes"], 1), f"{r['json_valid']}/200", f"{r['tool_correct']}/200", f"{r['full_match']}/200",
                     r["hallucinated_tool"], r["wrong_action"], r["no_call"],
                     f"{r['eval_new_tokens_per_s']:.0f} / {merged.get('eval_new_tokens_per_s', 0):.0f}" if merged
                     else f"{r['eval_new_tokens_per_s']:.0f} / -"])
    table(doc, ["Run", "Trainable (% of model)", "Peak train mem GB", "Train min", "JSON valid", "Tool correct", "Full match",
                "Halluc. tool", "Wrong action", "No call", "tok/s unmerged / merged"], rows, font_pt=7.5)
    merged_rows = [[LABELS[m], f"{runs[m]['full_match']}/200", f"{runs[m]['merged']['full_match']}/200",
                    f"{runs[m]['eval_ms_per_example']:.0f}", f"{runs[m]['merged']['eval_ms_per_example']:.0f}"]
                   for m in METHODS[1:] if runs[m] and runs[m].get("merged")]
    table(doc, ["Run", "Full match (adapter)", "Full match (merged into 16-bit)", "ms/example adapter", "ms/example merged"],
          merged_rows, font_pt=8)
    para(doc, "Peak memory is torch.cuda.max_memory_allocated() over model loading and training. Inference speed is greedy batched "
              "decoding (batch 16) of the 200 test prompts. Merged = adapter folded into a fresh 16-bit copy of the base model.", size=8)
else:
    placeholder(doc, "results table - run the Colab notebook, copy results/ here and re-run build_report.py")

doc.add_heading("Section 3 - Is a bigger rank actually better?", level=1)
sweep = [load(f"{winner}_r{r}") for r in (4, 8, 16, 32)] if winner else []
if winner and all(sweep):
    doc.add_picture(str(RES / "rank_sweep.png"), width=Cm(13))
    table(doc, ["Rank", "Trainable params", "Peak mem GB", "Train min", "Tool accuracy %", "Full match %"],
          [[s["rank"], f"{s['trainable_params']:,}", fmt(s["peak_train_mem_gb"], 2), fmt(s["train_minutes"], 1),
            fmt(s["tool_accuracy_pct"]), fmt(s["full_match_pct"])] for s in sweep], font_pt=8)
    placeholder(doc, "your conclusion from the graph: does doubling the rank buy accuracy, or only memory? Quote the numbers above")
else:
    placeholder(doc, "rank sweep (r = 4, 8, 16, 32) plot and conclusion - produced by Section 3 of the notebook")

doc.add_heading("Section 4 - Report", level=1)
doc.add_heading("1. Your call: what ships on Monday", level=2)
para(doc, "Merge behaviour is the deciding technical difference between the two memory-light options:")
bullet(doc, "QLoRA's adapter was trained to correct an NF4-quantised base. A 4-bit layer cannot absorb a 16-bit update, so merging "
            "means de-quantising the base to fp16 and adding BA. The merged model is then a 16-bit model the adapter never saw, "
            "so it loses QLoRA's memory saving and can drift in accuracy. Re-quantising after merging adds rounding error on top. "
            "The alternative is to serve the 4-bit base with the adapter unmerged, which costs per-token overhead. The notebook "
            "measures QLoRA's merged accuracy to show the size of this effect.")
bullet(doc, "DoRA merges exactly into 16-bit weights (W' = m * V / ||V||_c is just a new matrix), so after merging it is as fast as the "
            "base model. Unmerged it is the slowest variant, because it recomputes the column norm on every forward pass.")
placeholder(doc, "state the method you would ship and justify it with the numbers in Sections 2-3 (accuracy, peak memory, "
                 "training minutes, merged/unmerged tokens per second)")

doc.add_heading("2. Where it still breaks", level=2)
if failures:
    para(doc, f"Best run: {failures['best_run']}. Error labels across all its misses: "
              + ", ".join(f"{k}: {v}" for k, v in failures["label_counts"].items()) + ".")
    picked, seen = [], set()
    for f in failures["failures"]:
        if f["label"] not in seen:
            picked.append(f)
            seen.add(f["label"])
    picked += [f for f in failures["failures"] if f not in picked][: 5 - len(picked)]
    for i, f in enumerate(picked[:5], 1):
        para(doc, f"Case {i} - label: {f['label']}", bold=True)
        math(doc, f"Customer : {f['user'][:300]}")
        math(doc, f"Expected : {json.dumps(f['gold'])[:300]}")
        math(doc, f"Produced : {f['output'][:300]}")
    placeholder(doc, "describe the pattern you see across these failures")
else:
    placeholder(doc, "five failure cases with labels - produced automatically by the last cell of the notebook (results/failures.json)")

doc.add_heading("3. The agentic angle", level=2)
para(doc, "A router agent, a refund agent and a shipping agent can share one frozen copy of Qwen2.5-1.5B (about 3.1 GB in 16-bit) "
          "and differ only in small adapters. At r = 8 on all seven projection types, one adapter has 2 x 8 x (input + output "
          "dimension) parameters per matrix over 28 layers: 9,232,384 parameters, or about 18 MB in fp16. That is 0.6% of the "
          "model. Three agents therefore cost about 3.1 GB + 3 x 18 MB of GPU memory instead of 3 x 3.1 GB. Each adapter trains in "
          "minutes on the one GPU the startup has. Multi-LoRA servers (S-LoRA, vLLM, LoRAX) can batch requests for different "
          "adapters on the same base, so one deployment serves all three agents, and each agent can be retrained and versioned "
          "independently.")
para(doc, "Real risk of hot-swapping adapters: a request runs with the wrong adapter. If adapters are swapped in place while requests "
          "are in flight, or merged into shared weights and un-merged later, a shipping query can be decoded with the refund "
          "agent's adapter. That agent has learned to emit initiate_refund, so the result is an unauthorised financial action. "
          "A stale or partially loaded adapter after a deploy gives the same failure without any error. Mitigations: pin "
          "the adapter ID and version to each request for its whole lifetime, serve adapters unmerged from an immutable registry, "
          "never share prefix/KV caches across adapters, and enforce each agent's allowed functions outside the model so that "
          "initiate_refund is rejected unless it comes from the refund agent.")

doc.add_heading("4. What surprised me", level=2)
placeholder(doc, "write this yourself after the runs: be specific about a result that did not match your expectation")

save_with_pdf(doc, HERE / "Assignment_Beta_Question_no_2_23K-0028.docx")
print("written Assignment_Beta_Question_no_2_23K-0028.docx", "(with results)" if done else "(placeholders only)")
