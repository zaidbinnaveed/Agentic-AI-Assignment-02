"""Builds q1_calculations.xlsx: the Q1 calculations as live Excel formulas (run q1_calculations.ipynb first)."""
import json
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HERE = Path(__file__).parent
RES = json.loads((HERE / "results/q1_results.json").read_text())
INPUTS = pd.read_csv(HERE / "cost_inputs.csv")
BOLD, INPUT_FILL = Font(bold=True), PatternFill("solid", fgColor="FFF2CC")

wb = Workbook()


def sheet(title, header=None):
    ws = wb.create_sheet(title)
    if header:
        ws.append(header)
        for c in ws[1]:
            c.font = BOLD
    return ws


REFS = {}


def name(label, ref):
    REFS[label] = ref


def block(ws, rows, start=1):
    """Write (label, value_or_formula, note) rows in columns A-C and return the row of each label."""
    where = {}
    for i, (label, value, note) in enumerate(rows, start):
        ws.cell(i, 1, label)
        ws.cell(i, 2, value)
        ws.cell(i, 3, note)
        if not str(value).startswith("="):
            ws.cell(i, 2).fill = INPUT_FILL
        where[label] = i
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 70
    return where


wb.remove(wb.active)
ws = sheet("Parameters")
r = block(ws, [
    ("Roll number", "23K-0028", "yellow cells are inputs, white cells are formulas"),
    ("Digits", "2,3,0,0,2,8", ""),
    ("Digit sum", "=2+3+0+0+2+8", ""),
    ("R", 28, "last two digits"),
    ("D", "=MOD(B3,10)", "digit sum mod 10"),
    ("Q (queries/day)", "=1500+25*B4", "1500 + 25R"),
    ("N (LLM calls/query)", "=5+MOD(B4,4)", "5 + (R mod 4)"),
    ("p (tool-call failure)", "=0.04+0.01*B5", "0.04 + 0.01D"),
    ("H (heatwave days)", "=4+MOD(B4,4)", "4 + (R mod 4)"),
    ("B (USD/month)", "=1200+10*B4", "1200 + 10R"),
    ("T (s)", "=10-MOD(B4,3)", "10 - (R mod 3)"),
    ("Cacheable prefix (tokens)", 1500, "assignment assumption"),
])
for label, row in (("Q", 6), ("N", 7), ("p", 8), ("H", 9), ("B", 10), ("T", 11), ("PREFIX", 12)):
    name(label + "_", f"Parameters!$B${row}")

ws = sheet("Tokens", ["k", "Input I_k", "Output O_k", "Retried?"])
for kk in range(1, 6):
    ws.append([kk, f"=2000+800*(A{kk + 1}-1)", f"=IF(A{kk + 1}<N_,350,600)", f"=IF(A{kk + 1}<N_,1,0)"])
r = block(ws, [
    ("Sum I_k", "=SUM(B2:B6)", ""),
    ("Sum O_k", "=SUM(C2:C6)", ""),
    ("Retry input = p * sum I_k (k<N)", "=p_*SUMPRODUCT(B2:B6,D2:D6)", ""),
    ("Retry output = p * sum O_k (k<N)", "=p_*SUMPRODUCT(C2:C6,D2:D6)", ""),
    ("E[input] per query", "=B8+B10", ""),
    ("E[output] per query", "=B9+B11", ""),
    ("E[calls] per query", "=N_+p_*(N_-1)", ""),
    ("Monthly queries M", "=(30-H_)*Q_+H_*5*Q_", "(30-H)Q + H*5Q"),
    ("Monthly input tokens", "=B12*B15", ""),
    ("Monthly output tokens", "=B13*B15", ""),
    ("Monthly prefix tokens", "=PREFIX_*B14*B15", "1500 * E[calls] * M"),
], start=8)
for label, row in (("E_in", 12), ("E_out", 13), ("E_calls", 14), ("M_", 15)):
    name(label, f"Tokens!$B${row}")

cols = ["model", "side", "reasoning setting", "P_in", "P_out", "P_cached", "write mult", "min prefix", "TTL (min)",
        "reasoning tok/call", "caching applies", "cost no cache", "cost with cache", "fits B (no cache)", "fits B (cache)"]
ws = sheet("API_costs", cols)
for i, row in enumerate(INPUTS.itertuples(), 2):
    vals = [row.model, row.side, row.reasoning_basis, row.price_in, row.price_out, row.price_cached, row.cache_write_mult,
            row.cache_min_tokens, row.cache_ttl_min, row.reasoning_tokens_per_call]
    ws.append([None if pd.isna(v) else v for v in vals])
    out_tok = f"(E_out+N(J{i})*E_calls)*M_"
    prefix = "PREFIX_*E_calls*M_"
    writes = f"MIN({prefix},PREFIX_*43200/IF(ISNUMBER(I{i}),I{i},5))"
    ws[f"K{i}"] = f"=AND(ISNUMBER(F{i}),N(F{i})<D{i},OR(NOT(ISNUMBER(H{i})),N(H{i})<=PREFIX_))"
    ws[f"L{i}"] = f"=(E_in*M_*D{i}+{out_tok}*E{i})/1000000"
    ws[f"M{i}"] = (f"=IF(K{i},((E_in*M_-{prefix})*D{i}+{writes}*N(G{i})*D{i}+({prefix}-{writes})*N(F{i})"
                   f"+{out_tok}*E{i})/1000000,L{i})")
    ws[f"N{i}"] = f"=L{i}<=B_"
    ws[f"O{i}"] = f"=M{i}<=B_"
ws.column_dimensions["A"].width = 30
ws.column_dimensions["C"].width = 40

ws = sheet("Peak_load")
block(ws, [
    ("Heatwave-day queries", "=5*Q_", ""),
    ("Queries 12:00-14:00", "=0.35*B1", "35% of the heatwave day"),
    ("Peak QPM", "=B2/120", ""),
    ("Peak lambda (queries/s)", "=B3/60", ""),
    ("Peak RPM (LLM requests)", "=B3*E_calls", ""),
    ("Peak TPM input", "=B3*E_in", ""),
    ("Peak TPM output", "=B3*E_out", "no reasoning tokens"),
    ("Peak uncached TPM input", "=B3*(E_in-PREFIX_*E_calls)", "Anthropic ITPM counts uncached input only"),
])

sh = RES["selfhost"]
ws = sheet("Self_hosting")
block(ws, [
    ("Model", sh["model"], "full GQA attention"),
    ("Parameters P", sh["params"], "Hugging Face API safetensors.total"),
    ("Layers L", sh["layers"], "config.json num_hidden_layers"),
    ("KV heads", sh["kv_heads"], "config.json num_key_value_heads"),
    ("head_dim", sh["head_dim"], sh["head_dim_note"]),
    ("Weights FP16 (GB)", "=B2*2/1E9", "P x 2 bytes"),
    ("Weights 8-bit (GB)", "=B2*1/1E9", "P x 1 byte"),
    ("Weights 4-bit (GB)", "=B2*0.5/1E9", "P x 0.5 byte"),
    ("Longest context S (tokens)", "=Tokens!B6+Tokens!C6", "input of call N + 600 output"),
    ("KV bytes per token", "=2*B3*B4*B5*2", "2 x L x kv_heads x head_dim x 2 bytes"),
    ("KV per sequence (GB)", "=B10*B9/1E9", ""),
    ("GPU memory (GB)", sh["gpu_gb"], sh["gpu"]),
    ("Usable (90%) (GB)", "=0.9*B12", "10% reserved"),
    ("KV budget (GB)", "=B13-B8", "after 4-bit weights"),
    ("Max concurrent sequences / GPU", "=FLOOR(B14/B11,1)", ""),
    ("GPU price (USD/h)", sh["gpu_price"], "RunPod Secure Cloud on-demand, accessed 2026-11-11"),
    ("End-to-end latency L (s)", round(sh["session_s"], 4), "faster candidate after the architectural change"),
    ("Concurrent sessions at Q", "=Peak_load!B4*B17", "Little's law: lambda x L"),
    ("GPUs needed at Q", "=MAX(1,CEILING(B18/B15,1))", ""),
    ("Self-host cost at Q (USD/month)", "=B19*B16*720", "every GPU billed 720 h"),
])

ws = sheet("Latency", ["candidate", "k", "I_k", "O_k", "a (s)", "b (s/token)", "tps", "TTFT(I_k)", "call latency"])
row = 2
for cand, v in RES["latency"].items():
    for kk in range(5):
        ws.append([cand, kk + 1, f"=Tokens!B{kk + 2}", f"=Tokens!C{kk + 2}", v["a"], v["b"], v["tps"],
                   f"=E{row}+F{row}*C{row}", f"=H{row}+D{row}/G{row}"])
        row += 1
tool_row = row + 1
block(ws, [
    ("Pooled median tool delay t (s)", RES["tools"]["median_ms"] / 1000, "from timing_log.csv"),
    (f"L {list(RES['latency'])[0]}", f"=SUM(I2:I6)+(N_-1)*B{tool_row}+p_*(SUM(I2:I5)+4*B{tool_row})", "sum + tools + retries"),
    (f"L {list(RES['latency'])[1]}", f"=SUM(I7:I11)+(N_-1)*B{tool_row}+p_*(SUM(I7:I10)+4*B{tool_row})", ""),
], start=tool_row)

be = RES["breakeven"]
ws = sheet("Break_even", ["Q' (queries/day)", "concurrent sessions", "GPUs", "self-host USD/month", "API USD/month (linear)"])
for i, q in enumerate(range(500, 20001, 500), 2):
    ws.append([q, f"=0.35*5*A{i}/7200*Self_hosting!$B$17", f"=MAX(1,CEILING(B{i}/Self_hosting!$B$15,1))",
               f"=C{i}*Self_hosting!$B$16*720", f"=A{i}*{be['api_per_daily_query']}"])
ws.cell(1, 7, "API USD per daily query (from notebook, includes cache-write term)").font = BOLD
ws.cell(2, 7, be["api_per_daily_query"])

pattern = re.compile(r"\b(" + "|".join(sorted(REFS, key=len, reverse=True)) + r")\b")
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.value = pattern.sub(lambda m: REFS[m.group(1)], cell.value)
wb.save(HERE / "q1_calculations.xlsx")
print("written q1_calculations.xlsx")
