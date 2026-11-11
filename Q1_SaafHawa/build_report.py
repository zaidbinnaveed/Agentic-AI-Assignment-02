"""Builds the Q1 report (Word + PDF) from models.csv, cost_inputs.csv and results/q1_results.json."""
import json
import re
import sys
from pathlib import Path

import pandas as pd
from docx.enum.section import WD_ORIENT
from docx.shared import Cm, Pt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from common.docx_utils import bullet, math, new_document, para, placeholder, rich, save_with_pdf, table  # noqa: E402

R = json.loads((HERE / "results/q1_results.json").read_text())
MODELS = pd.read_csv(HERE / "models.csv", dtype=str).fillna("")
INPUTS = pd.read_csv(HERE / "cost_inputs.csv")
ACCESS = "11 Nov 2026"
P, TOK, PEAK, SH = R["params"], R["tokens"], R["peak"], R["selfhost"]
LAT, BE, TOOLS = R["latency"], R["breakeven"], R["tools"]


def usd(x):
    return f"${x:,.2f}"


def short(text, n=95):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


refs = {}


def cite(field):
    nums = []
    for url in re.findall(r"https?://[^\s;,)]+", field):
        nums.append(refs.setdefault(url, len(refs) + 1))
    return "[" + ",".join(map(str, sorted(set(nums)))) + "]" if nums else "[source: not verified]"


doc = new_document("Question 1 - SaafHawa: closed API or self-hosted open model?", margins_cm=1.8, base_pt=10.5)

doc.add_heading("Parameters (roll number 23K-0028)", level=1)
math(doc, f"Digits of 23K-0028 (letters and hyphen ignored): {', '.join(map(str, P['digits']))}; sum = {P['digit_sum']}")
math(doc, f"R = last two digits = {P['R']}        D = {P['digit_sum']} mod 10 = {P['D']}")
table(doc, ["Parameter", "Formula", "Working", "Value"], [
    ["Normal daily queries Q", "1,500 + 25R", f"1,500 + 25 x {P['R']}", f"{P['Q']:,}"],
    ["LLM calls per query N", "5 + (R mod 4)", f"5 + ({P['R']} mod 4) = 5 + {P['R'] % 4}", P["N"]],
    ["Tool-call failure prob. p", "0.04 + 0.01D", f"0.04 + 0.01 x {P['D']}", P["p"]],
    ["Heatwave days per month H", "4 + (R mod 4)", f"4 + {P['R'] % 4}", P["H"]],
    ["Monthly budget B (USD)", "1,200 + 10R", f"1,200 + 10 x {P['R']}", f"{P['B']:,}"],
    ["Latency target T (s)", "10 - (R mod 3)", f"10 - {P['R'] % 3}", P["T"]],
], font_pt=10)
para(doc, "All prices are in USD and all web sources were accessed on 11 Nov 2026. Raw research data: models.csv (one source URL per "
          "field). Values used in the calculations: cost_inputs.csv. Calculations: q1_calculations.ipynb and q1_calculations.xlsx. "
          "Raw tool timing log: timing_log.csv.", italic=True)

# ---------------- Section 1: comparison table (landscape) ----------------
sec = doc.add_section()
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width
sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(1.2)
doc.add_heading("Section 1 - Model comparison (current as of November 2026)", level=1)
para(doc, "Nine closed models from four providers (OpenAI, Anthropic, Google, xAI) and ten open-weight models from nine labs. Each model "
          "is priced and timed at its lowest reasoning setting, given in the 'Tools / JSON / setting used' column. Bracketed numbers "
          "are sources in the reference list below; every source was accessed 11 Nov 2026. Open-weight prices are the lowest public "
          "provider's. Long cells are shortened with '…', and the full text is in models.csv.", size=8)
inp = INPUTS.set_index("model")
rows = []
for m in MODELS.itertuples():
    key = next((k for k in inp.index if m.model.startswith(k) or k.startswith(m.model.split(" (")[0])), None)
    setting = inp.loc[key, "reasoning_basis"] if key else m.lowest_setting
    rows.append([
        f"{m.model}\n({m.provider}; {m.side})",
        f"{short(m.total_params, 45)} / {short(m.active_params, 30)} {cite(m.src_params)}",
        f"{short(m.context_window, 40)} / {short(m.max_output, 45)} {cite(m.src_context)}",
        f"{m.price_in} / {m.price_out} / {short(m.price_cached_in, 30)}\n@ {short(m.price_provider, 40)} {cite(m.src_price)}",
        f"{short(m.rpm, 40)} / {short(m.tpm, 45)}\n({short(m.rate_limit_tier, 45)}) {cite(m.src_rate_limits)}",
        f"{m.ttft_s} / {m.throughput_tps} {cite(m.src_latency)}",
        f"{short(m.bench1_name, 45)}: {m.bench1_score} {cite(m.src_bench1)}",
        f"{short(m.bench2_tool_name, 45)}: {m.bench2_tool_score} {cite(m.src_bench2)}",
        f"{short(m.tool_calling, 12)} / {short(m.json_output, 20)} / {short(setting, 60)} {cite(m.src_features)}",
        f"{short(m.license, 40)}; self-host: {short(m.commercial_self_host, 60)} {cite(m.src_license)}",
    ])
table(doc, ["Model", "Params total / active", "Context / max output", "$/1M in / out / cached", "RPM / TPM (new paid tier)",
            "TTFT s / tok/s", "Benchmark 1", "Tool-use benchmark", "Tools / JSON / setting used", "Licence; self-hosting"],
      rows, font_pt=6, col_widths_cm=[3.0, 2.4, 2.4, 2.8, 3.2, 1.8, 2.6, 2.6, 3.0, 3.2])
para(doc, "Benchmarks: Artificial Analysis stopped scoring current closed models on tau2-bench and GPQA, so the closed side uses "
          "GDPval-AA and AutomationBench-AA, Artificial Analysis' run of Zapier's tool-calling workflows. Open models use the tool "
          "benchmark their card or Artificial Analysis reports, and the variants differ: tau2/tau3, Tau-Bench Retail, BFCL v2. Tool "
          "scores are therefore comparable within a benchmark, not across benchmarks.", size=8)

para(doc, "Two values I could not verify, and their effect on the analysis", bold=True)
para(doc, "(1) The average number of reasoning tokens Gemini 3.5 Flash-Lite still produces at its lowest setting ('minimal'). Google "
          "says the model may still reason there. Artificial Analysis reports 16,765 reasoning tokens per task, but does not say for "
          "which setting. If that figure applied to every agent call, Flash-Lite would cost far more than B. Its $903/month is "
          "therefore only a lower bound, and I excluded it from the latency candidates even though it has the best tool-use score of "
          "the cheap closed models. The same applies to Sonnet 5.5, Gemini 3.8 Flash, GLM-5.3-Flash, Kimi K3 and DeepSeek V4.1 Flash. "
          "(2) Claude Haiku 5.5's time to first token with thinking disabled. Artificial Analysis only measures it with adaptive "
          "thinking on. I used the thinking-on TTFT (5.2 s at 1k tokens, 8.9 s at 10k), which includes reasoning time, so Haiku's "
          "latency is an upper bound. Haiku is the closed candidate and the break-even comparator, so its true latency may be much "
          "lower. That would shrink the concurrent sessions in the GPU sizing and make the API look even better. It cannot change "
          "the conclusion that T = 9 s is out of reach, because routing already removes four of Haiku's five calls.", size=9)
para(doc, "Other gaps recorded in models.csv: Google Tier-1 RPM/TPM (shown only in the console), most open-weight providers' RPM/TPM "
          "(not published), and cache write fees, minimums and lifetimes for xAI and several open-weight providers. Where a minimum is "
          "unknown, caching is assumed to apply and the model is flagged.", size=8)
para(doc, "References (all accessed 11 Nov 2026)", bold=True, size=8)
ref_par = doc.add_paragraph()
for url, n in sorted(refs.items(), key=lambda kv: kv[1]):
    run = ref_par.add_run(f"[{n}] {url}   ")
    run.font.size = Pt(6)

# ---------------- Section 2 (portrait) ----------------
sec = doc.add_section()
sec.orientation = WD_ORIENT.PORTRAIT
sec.page_width, sec.page_height = sec.page_height, sec.page_width
sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(1.8)
doc.add_heading("Section 2 - Calculations", level=1)

doc.add_heading("2.1 Token volume", level=2)
math(doc, "I_k = 2000 + 800(k-1);  O_k = 350 (k < N), 600 (k = N)")
for kk, (i, o) in enumerate(zip(TOK["I"], TOK["O"]), 1):
    math(doc, f"  call {kk}: I = {i:,}, O = {o}")
math(doc, f"E[in]  = sum I_k + p * sum_(k<N) I_k = {TOK['sum_I']:,} + {P['p']} x {TOK['sum_I'] - TOK['I'][-1]:,} = {TOK['E_in']:,.0f} tokens/query")
math(doc, f"E[out] = sum O_k + p * sum_(k<N) O_k = {TOK['sum_O']:,} + {P['p']} x {TOK['sum_O'] - TOK['O'][-1]:,} = {TOK['E_out']:,.0f} tokens/query")
math(doc, f"E[calls] = N + p(N-1) = {P['N']} + {P['p']} x {P['N'] - 1} = {TOK['E_calls']:.2f}")
math(doc, f"M = (30-H)Q + H*5Q = {30 - P['H']} x {P['Q']:,} + {P['H']} x {5 * P['Q']:,} = {TOK['M']:,} queries/month")
math(doc, f"Monthly input  = {TOK['M']:,} x {TOK['E_in']:,.0f} = {TOK['monthly_in']:,.0f} tokens")
math(doc, f"Monthly output = {TOK['M']:,} x {TOK['E_out']:,.0f} = {TOK['monthly_out']:,.0f} tokens")

doc.add_heading("2.2 API cost with and without prompt caching", level=2)
CT = R["cache_terms"]
math(doc, "C_no_cache = M x (E[in] x P_in + E[out]' x P_out) / 1e6,   E[out]' = E[out] + r x E[calls]  (r = reasoning tokens/call)")
math(doc, f"Prefix tokens/month = 1500 x E[calls] x M = 1500 x {TOK['E_calls']:.2f} x {TOK['M']:,} = {CT['prefix_tokens']:,.0f}")
math(doc, f"Non-prefix input    = {TOK['monthly_in']:,.0f} - {CT['prefix_tokens']:,.0f} = {CT['nonprefix_input']:,.0f}")
math(doc, "Cache writes W = 43,200 min / TTL per month (upper bound: one cold write per TTL window, day and night)")
math(doc, "C_cache = [non-prefix x P_in + 1500W x m_w x P_in + (prefix - 1500W) x P_cached + output x P_out] / 1e6")
terra = next(c for c in R["costs"] if c["model"] == "GPT-6.1 Terra")
math(doc, f"Example GPT-6.1 Terra: W = 43,200/30 = 1,440 writes; no cache = {usd(terra['cost_no_cache'])}; with cache = {usd(terra['cost_cache'])}")
cache_rules = []
for c in R["costs"]:
    cache_rules.append([
        c["model"], f"{c['P_in']} / {c['P_out']} / {c['P_cached'] if c['P_cached'] is not None else '-'}",
        f"{c['write_mult'] if c['write_mult'] is not None else '-'}x / {int(c['min_prefix']) if c['min_prefix'] else 'n.v.'} / "
        f"{int(c['ttl_min']) if c['ttl_min'] else 'n.v.'}",
        "yes" if c["caching_applied"] else "no", "-" if c["reasoning_per_call"] in (None, 0) else f"{c['reasoning_per_call']:,.0f}",
        usd(c["cost_no_cache"]) + ("*" if c["lower_bound"] else ""), usd(c["cost_cache"]) + ("*" if c["lower_bound"] else ""),
        "yes" if c["fits_B_no_cache"] else "no", "yes" if c["fits_B_cache"] else "no"])
table(doc, ["Model", "$ in / out / cached", "write premium / min prefix / TTL min", "cache used", "reasoning tok/call",
            "no cache /mo", "cached /mo", f"<= B no cache", f"<= B cached"], cache_rules, font_pt=7.5)
para(doc, "* lower bound: the model still reasons at its lowest setting and no average token count could be verified. n.v. = not "
          "verified (caching assumed to apply). No caching: Gemini 3.8 Flash (its 4,096-token minimum exceeds the 1,500-token prefix), "
          "Qwen3-235B and Llama 3.3 at DeepInfra (no cache price), and Gemma 4 at CoreWeave (cache read = input price). Reasoning tokens "
          "added: GPT-6.1 Sol 1,585 and Grok 4.7 21,674 per call (Artificial Analysis average per task at 'low'; this overstates a "
          "short tool step) and gpt-oss-120b 24 per call (arXiv 2608.14161).", size=8)
fit = [c["model"] for c in R["costs"] if c["fits_B_cache"]]
savings = [1 - c["cost_cache"] / c["cost_no_cache"] for c in R["costs"] if c["caching_applied"]]
para(doc, f"Within B = ${P['B']:,} (both with and without caching): {', '.join(fit)}. Where caching applies it saves "
          f"{100 * min(savings):.0f}-{100 * max(savings):.0f}%: the 1,500-token prefix is only "
          f"{100 * 1500 * TOK['E_calls'] / TOK['E_in']:.0f}% of input, and output tokens dominate the bill for reasoning models. Every strong closed tool "
          "user (GPT-6.1 Terra/Sol, Sonnet 5.5, Grok 4.7) is over budget even with caching.")

doc.add_heading("2.3 Peak load and rate limits (12:00-14:00 on a heatwave day)", level=2)
math(doc, f"Heatwave day = 5Q = {PEAK['peak_day']:,};  window = 0.35 x {PEAK['peak_day']:,} = {PEAK['window']:,.0f} queries in 120 min")
math(doc, f"QPM = {PEAK['window']:,.0f}/120 = {PEAK['qpm']:.2f}    RPM = QPM x E[calls] = {PEAK['qpm']:.2f} x {TOK['E_calls']:.2f} = {PEAK['rpm']:.1f}")
math(doc, f"TPM_in = {PEAK['qpm']:.2f} x {TOK['E_in']:,.0f} = {PEAK['tpm_in']:,.0f}    TPM_out = {PEAK['qpm']:.2f} x {TOK['E_out']:,.0f} = {PEAK['tpm_out']:,.0f}")
math(doc, f"Uncached TPM_in (Anthropic ITPM) = {PEAK['qpm']:.2f} x ({TOK['E_in']:,.0f} - 1500 x {TOK['E_calls']:.2f}) = {PEAK['tpm_in_uncached']:,.0f}")
def show(v):
    return "n.v." if v is None else f"{v:,.0f}"


def verdict(v):
    return "n.v." if v is None else ("OK" if v else "EXCEEDED")


lim_rows = [[l["model"], f"{l['RPM_needed']:.0f} / {show(l['RPM_limit'])}", f"{l['TPM_needed']:,.0f} / {show(l['TPM_limit'])}",
             verdict(l["RPM_ok"]), verdict(l["TPM_ok"])] for l in R["limits"]]
headroom = sorted((l["TPM_limit"] / l["TPM_needed"], l["model"]) for l in R["limits"] if l["TPM_limit"])
rpm_headroom = min(l["RPM_limit"] / l["RPM_needed"] for l in R["limits"] if l["RPM_limit"])
table(doc, ["Model", "RPM need / limit", "TPM need / limit", "RPM", "TPM"], lim_rows, font_pt=7.5)
para(doc, f"Every published limit is met. RPM has at least {rpm_headroom:.0f}x headroom; the tightest TPM case is "
          f"{headroom[0][1]} at {headroom[0][0]:.2f}x its limit (reasoning tokens included), and Claude Haiku 5.5 has "
          f"{dict((m, h) for h, m in headroom)['Claude Haiku 5.5']:.1f}x. The real constraints for a new account are spend caps: Anthropic Start $500/month, Google Tier 1 $250. For "
          "open-weight providers the limits are mostly unpublished (n.v.). DeepInfra allows 200 concurrent requests per model, and "
          "SaafHawa's peak concurrency is about 13-16 sessions (Section 2.4), so that is not binding.", size=9)

doc.add_heading("2.4 Self-hosting memory: Llama 3.3 70B Instruct (full GQA attention)", level=2)
para(doc, "Llama 3.3 70B is the open-weight model in the table with plain grouped-query attention that fits one 80 GB GPU at 4-bit. "
          "Qwen3-235B is also GQA but needs about 118 GB at 4-bit. The newer models use hybrid-linear, sparse, sliding-window or "
          "latent attention, so the standard formula would not apply to them. The meta-llama repo is gated, so P comes from the "
          f"Hub API and config.json from the identical unsloth mirror. {SH['head_dim_note']}.")
doc.add_picture(str(HERE / "results/llama33_config.png"), width=Cm(15))
placeholder(doc, "replace this rendered API response with your own browser screenshot of config.json (see TODO_FOR_STUDENT.md)")
W = SH["weights_gb"]
math(doc, f"P = {SH['params']:,};  L = {SH['layers']}, kv_heads = {SH['kv_heads']}, head_dim = {SH['head_dim']}")
math(doc, f"Weights FP16 = P x 2 B = {W['16']:.2f} GB;  8-bit = P x 1 B = {W['8']:.2f} GB;  4-bit = P x 0.5 B = {W['4']:.2f} GB")
math(doc, f"Longest context S = I_N + O_N = {TOK['I'][-1]:,} + {TOK['O'][-1]} = {SH['S_max']:,} tokens")
math(doc, f"KV/seq = 2 x {SH['layers']} x {SH['kv_heads']} x {SH['head_dim']} x {SH['S_max']:,} x 2 B = {SH['kv_per_token'] * SH['S_max']:,} B = {SH['kv_seq_gb']:.3f} GB")
math(doc, f"GPU: {SH['gpu']} = {SH['gpu_gb']} GB, ${SH['gpu_price']}/h (https://www.runpod.io/pricing)")
math(doc, f"Usable = 0.9 x {SH['gpu_gb']} = {SH['usable_gb']:.1f} GB;  KV budget = {SH['usable_gb']:.1f} - {W['4']:.2f} = {SH['kv_budget_gb']:.2f} GB")
math(doc, f"Max concurrent sequences = floor({SH['kv_budget_gb']:.2f} / {SH['kv_seq_gb']:.3f}) = {SH['per_gpu']} per GPU")
math(doc, f"Little's law: C = lambda_peak x L = {SH['lam']:.4f}/s x {SH['session_s']:.2f} s = {SH['concurrent']:.2f} sessions")
math(doc, f"GPUs = ceil({SH['concurrent']:.2f} / {SH['per_gpu']}) = {SH['gpus']}  ->  {SH['gpus']} x ${SH['gpu_price']} x 720 h = {usd(SH['monthly'])}/month")
para(doc, f"L = {SH['session_s']:.2f} s is the end-to-end latency of the faster candidate after the architectural change (Section 2.6). "
          "Memory is not the only limit. Single-stream decoding of 35 GB of weights on a 2,039 GB/s A100 is bounded at about "
          f"{SH['decode_bound_tps']:.0f} tokens/s (an estimate, not a measurement). A self-hosted 70B would therefore be slower per "
          "user than the APIs measured here, which makes L, and hence the GPU count, larger.", size=9)

doc.add_heading("2.6 Latency budget (needed for 2.4 and 2.5)", level=2)
tl = pd.DataFrame(TOOLS["per_tool"])
table(doc, ["Tool", "n OK", "median ms", "mean ms", "min ms", "max ms"],
      [[r.tool, int(r["count"]), f"{r['median']:.4f}", f"{r['mean']:.4f}", f"{r['min']:.4f}", f"{r['max']:.4f}"] for _, r in tl.iterrows()],
      font_pt=8)
math(doc, f"Pooled median of all {TOOLS['n_ok']} successful measurements: t = {TOOLS['median_ms']:.4f} ms per tool call")
if not TOOLS["complete"]:
    placeholder(doc, f"timing log incomplete: OpenAQ calls need an API key, and a second day's run is required. The current log has "
                     f"{TOOLS['n_ok']} OK measurements from {TOOLS['days']} day(s). Re-run tool_latency.py, the notebook and this "
                     "builder (TODO_FOR_STUDENT.md)")
para(doc, "Because heat-index and KB lookups take microseconds, the pooled median sits between the local tools and the API calls. Even "
          "the slowest API median (~130 ms) x 4 tool calls is under 0.6 s, so tool delay is small next to LLM time.", size=9)
math(doc, "Per call:  l_k = TTFT(I_k) + O_k / tps,   TTFT(I) = a + b I  (fit through AA's measured TTFT at 1k and 10k input tokens)")
math(doc, "Per query: L = sum_k l_k + (N-1) t + p sum_(k<N) (l_k + t)")
para(doc, "Candidates. Rule: within B with caching, cost not a lower bound, verified TTFT and throughput, tool calling and JSON "
          "supported; on each side, take the highest tool-use score. Results: Claude Haiku 5.5 (closed, AutomationBench-AA 22.9%) and "
          "MiniMax-M3 on DeepInfra (open-weight, tau2-Bench Telecom 88.9%).")
for name, v in LAT.items():
    math(doc, f"{name}: TTFT(I) = {v['a']:.3f} + {v['b'] * 1000:.4f} x I/1000 s;  {v['tps']} tok/s   ({v['source']})")
    for kk, (i, tt, cl) in enumerate(zip(TOK["I"], v["ttft_k"], v["call_lat"]), 1):
        math(doc, f"   call {kk}: TTFT({i:,}) = {tt:.3f} + {TOK['O'][kk - 1]}/{v['tps']} = {cl:.2f} s")
    math(doc, f"   L = {sum(v['call_lat']):.2f} + {v['tools']:.4f} (tools) + {v['retries']:.2f} (retries) = {v['total']:.2f} s  >  T = {P['T']} s")
rt = R["router"]
para(doc, "Architectural change: route the four tool-selection steps (calls 1..N-1) to a small fast model, so the candidate only "
          f"writes the final answer. The router is {rt['model']} (non-reasoning, Apache-2.0, TTFT {rt['ttft']} s, {rt['tps']} tok/s), the "
          "fastest verified in-budget model with tool calling and JSON. Calls 1..N-1 are billed at the router's prices.")
for name, v in LAT.items():
    rc = v["routed_calls"]
    math(doc, f"{name}: 4 x {rc[0]:.3f} + {rc[-1]:.2f} (final) + {v['routed_retries']:.2f} (retries) + tools = {v['routed_total']:.2f} s;  "
              f"cost {usd(v['routed_cost'])}/month")
para(doc, f"Neither candidate meets T = {P['T']} s, even after routing. Each query still generates about 2,126 output tokens over "
          "5.36 sequential calls, so at 40-300 tok/s plus 1-7 s TTFT per call, 9 s is out of reach for any model in the table. "
          f"Following the assignment's rule, the comparator is the lower-latency design: {BE['comparator']} + router at "
          f"{LAT[BE['comparator']]['routed_total']:.1f} s.", bold=False)

doc.add_heading("2.5 Break-even analysis", level=2)
math(doc, f"Self-host: C_self(Q') = g(Q') x ${SH['gpu_price']} x 720 h,  g = max(1, ceil(0.35 x 5Q'/7200 x L / {SH['per_gpu']}))")
math(doc, f"One GPU holds {SH['per_gpu']} sessions = {BE['queries_per_gpu']:,.0f} daily queries -> ${SH['gpu_price'] * 720:,.2f} / {BE['queries_per_gpu']:,.0f} = "
          f"${BE['gpu_per_daily_query']:.4f} per daily query")
math(doc, f"API ({BE['comparator']} + router): {usd(BE['api_at_Q'])}/month at Q = {P['Q']:,} = ${BE['api_per_daily_query']:.4f} per daily query")
math(doc, f"Self-host at Q: {usd(BE['selfhost_at_Q'])}/month  vs  API {usd(BE['api_at_Q'])}/month")
q_star = f"{BE['Q_star']:,} queries/day" if BE["Q_star"] else f"none up to {BE['grid_max']:,} queries/day"
math(doc, f"Q* = {q_star}")
doc.add_picture(str(HERE / "results/breakeven.png"), width=Cm(15))
para(doc, f"There is no break-even. Every extra GPU adds ${BE['gpu_per_daily_query']:.2f} of monthly cost per daily query of capacity, "
          f"about {BE['gpu_per_daily_query'] / BE['api_per_daily_query']:.0f}x the API's ${BE['api_per_daily_query']:.3f}. The step "
          "function therefore pulls away from the API line as volume grows, instead of crossing it. Even if sessions lasted only "
          f"T = {P['T']} s (the what-if in the notebook), "
          f"{'Q* would be ' + format(BE['Q_star_if_T'], ',') if BE['Q_star_if_T'] else 'there would still be no Q*'}. A Q* would need either a much cheaper GPU-hour, "
          "or far more sessions per GPU (a smaller model, a shorter context, or KV-cache quantisation), or a much more expensive API. "
          f"At SaafHawa's real volume of 2,200-11,000 queries/day, one mostly idle A100 costs "
          f"{BE['selfhost_at_Q'] / BE['api_at_Q']:.1f}x the whole API bill, so self-hosting is not realistic for an organisation of this size.")

doc.add_heading("Recommendation to the technical lead", level=1)
para(doc, "Pay per token through an API. Do not run your own GPUs.", bold=True)
bullet(doc, f"Cost: the routed design (Qwen3.8-27B for tool steps, Claude Haiku 5.5 for the answer) costs about "
            f"{usd(LAT['Claude Haiku 5.5']['routed_cost'])}/month at Q = {P['Q']:,}, against B = ${P['B']:,}. A single self-hosted "
            f"A100 costs {usd(SH['monthly'])}/month whether busy or idle, and self-hosting never breaks even (Section 2.5).")
bullet(doc, f"Traffic: the heatwave peak is {PEAK['rpm']:.0f} RPM and {PEAK['tpm_in'] + PEAK['tpm_out']:,.0f} TPM, within every "
            f"published limit (Haiku 5.5 RPM headroom {4000 / PEAK['rpm']:.0f}x). Watch new-account spend caps instead: Anthropic Start allows $500/month, which this design fits, and "
            "Google Tier 1 allows $250/month.")
bullet(doc, f"Latency: no option meets T = {P['T']} s with five sequential calls generating about 2,100 tokens. Routing gets the best "
            f"candidate to {LAT['Claude Haiku 5.5']['routed_total']:.1f} s. To approach 9 s, also (i) issue the independent "
            "air-quality, weather and KB calls in parallel from one LLM turn, (ii) shrink tool-call outputs to compact JSON instead "
            "of 350 tokens, and (iii) stream the final answer so the user sees text after one TTFT. If 9 s is a hard requirement, "
            "send a short 'checking...' reply on WhatsApp first.")
bullet(doc, "Open weights still matter: Qwen3.8-27B (Apache-2.0) does the tool steps, so the bulk of the tokens already run on a model "
            "you could self-host later if data-residency rules or volume (well beyond 60,000 queries/day) ever justify it.")
para(doc, "Languages (English, Urdu script, Roman Urdu)", bold=True)
para(doc, "Evidence is thin and should be tested before launch. Anthropic's multilingual table "
          "(https://platform.claude.com/docs/en/build-with-claude/multilingual-support) does not list Urdu. Its closest relative, "
          "Hindi, scores 96.6% of English for Haiku 5.5 on Global-MMLU. The same page says native script works better than "
          "transliteration, a direct warning for Roman Urdu. The Qwen3.8-27B and MiniMax-M3 model cards do not mention Urdu, so "
          "their support is not verified. Llama 3.3 officially supports eight languages, and Urdu is not one of them. Before "
          "committing, build a test set of 100-200 real SaafHawa questions in all three scripts. Score reply language and script "
          "fidelity, and check the numbers quoted back to the user.")
para(doc, "The morning pollution summary for municipal officers", bold=True)
para(doc, "This output reaches decision-makers, so it needs a higher accuracy bar than the chat replies. (1) Never let the LLM produce "
          "the numbers. Code computes PM2.5/PM10 averages, maxima and AQI categories directly from OpenAQ station data, and the "
          "LLM only writes prose around a fixed table. (2) Cite the station ID and timestamp for every figure. If data is missing or "
          "stale, say so instead of interpolating. (3) Run an automatic check that every number in the text matches the table. "
          "(4) Use a stronger model for this one daily call (e.g. GPT-6.1 Terra or Claude Sonnet 5.5). At one call a day, even a "
          "20k-token input costs well under $1/month. (5) Keep a human sign-off before the summary goes out.")

save_with_pdf(doc, HERE / "Assignment_Beta_Question_no_1_23K-0028.docx")
print("written Assignment_Beta_Question_no_1_23K-0028.docx")
