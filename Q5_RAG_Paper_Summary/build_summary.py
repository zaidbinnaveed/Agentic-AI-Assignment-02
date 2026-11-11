"""Builds the two-page summary of Ersoy & Ersahin (2025), IEEE Access 13:194185-194196."""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from common.docx_utils import bullet, new_document, para, rich, save_with_pdf, table  # noqa: E402

doc = new_document("Paper Summary - Question 5", margins_cm=1.8, base_pt=10.5)
rich(doc, [("Paper: ", "b"),
           ("P. Ersoy and M. Ersahin, \"A Comparative Evaluation of RAG Architectures for Cross-Domain LLM Applications: Design, "
            "Implementation, and Assessment,\" IEEE Access, vol. 13, pp. 194185-194196, 2025. DOI: 10.1109/ACCESS.2025.3632404. "
            "Open access (CC BY 4.0), read in full from https://ieeexplore.ieee.org/document/11245479 (accessed 11 Nov 2026).", "")])

doc.add_heading("1. Problem and motivation", level=2)
para(doc, "LLMs answer well zero-shot, but their parametric knowledge goes stale and they invent specifics. In finance and e-commerce "
          "that is costly, because exact figures and an audit trail are required. Retrieval-augmented generation (RAG) "
          "conditions the answer on passages fetched at query time, which keeps answers current and gives them provenance. The "
          "authors argue that existing comparisons of RAG designs are hard to trust for three reasons. They mix up retrieval quality "
          "and generation quality, they under-report hyperparameters, and they give single aggregate scores without confidence "
          "intervals or error analysis. The paper's contribution is methodological rather than a new algorithm: a controlled, "
          "statistically reported comparison of four retrieval paradigms against a zero-shot baseline.")

doc.add_heading("2. Research questions", level=2)
para(doc, "RQ1 compares faithfulness and recall across paradigms with the generator held fixed. RQ2 asks how sensitive the results "
          "are to retrieval depth, chunking and index tuning. RQ3 asks which paradigm gives the best utility under service-level "
          "latency and cost limits. RQ4 asks how paradigms differ in citation coverage and auditability. RQ5 asks whether the "
          "advantages hold across hosting modes and query difficulty.")

doc.add_heading("3. Architectures compared", level=2)
bullet(doc, "Sparse (BM25): lexical term matching over an inverted index. It is transparent, cheap and fast on CPUs, but it misses "
            "paraphrases and new jargon unless synonym lists are maintained.")
bullet(doc, "Dense (ANN): passages and queries are embedded with a transformer encoder and matched by approximate nearest-neighbour "
            "search. It handles paraphrased and multilingual queries well, but the similarity scores are hard to audit and the "
            "index is costly to build and refresh.")
bullet(doc, "Hybrid: BM25 and dense retrieval run in parallel, and the two lists are merged by reciprocal-rank fusion and a "
            "cross-encoder re-ranker. The authors motivate it by the low correlation between lexical and semantic relevance. "
            "The cost is maintaining two indices and de-duplicating results.")
bullet(doc, "Fusion: an LLM expands the query into m = 4 sub-queries whose results are merged, or Fusion-in-Decoder attends over up to "
            "24 separately encoded passages. It gives the widest coverage, but it is the slowest, its context is the largest, and "
            "source-to-token attribution is blurred.")

doc.add_heading("4. Experimental setup", level=2)
para(doc, "Every pipeline is a parameterised LangChain template. Each is run on a cloud generator (GPT-4o, temperature 0.2, top-p "
          "0.9, 512 output tokens, tools disabled) and on an on-premises one (Llama-3-8B-Instruct, 4-bit GGUF via llama.cpp on an "
          "Apple M3 Pro laptop). The generator and prompt are fixed within each comparison, so differences can be attributed to "
          "retrieval. Dense retrieval uses all-mpnet-base-v2 (768-d) in an HNSW index (M = 32, efSearch = 64) with an "
          "ms-marco-MiniLM cross-encoder re-ranker. Chunk sizes (256-512 tokens) and top-k (10 to 15+15) are pre-registered per "
          "pipeline (Table 2).")
para(doc, "The finance corpus has 3,214 SEC 10-K/10-Q filings, earnings releases and central-bank circulars (2019-2025, 92.7M "
          "tokens). The e-commerce corpus has 4,836 English and Turkish catalogue, pricing and returns-policy passages (68.3M "
          "tokens). A separate evidence pool holds 7,150 passages. The test set has 500 questions stratified by difficulty; 25% "
          "are deliberately unanswerable (time-shifted or perturbed entities), so a system cannot score well just by abstaining. "
          "Labels were double-annotated, with Cohen's kappa 0.77 for answerability and 0.74 for difficulty. Outputs are scored "
          "with RAGAS-style metrics: faithfulness, answer relevance, context precision and context recall. The authors add an "
          "auditability metric (the share of answer claims backed by a valid, recent citation) and end-to-end latency. Results "
          "are reported as means with 95% bootstrap CIs and paired Wilcoxon tests with Holm correction.")

doc.add_heading("5. Results (Table 3 of the paper)", level=2)
table(doc, ["Pipeline", "Faithful.", "Ans. rel.", "Ctx prec.", "Ctx recall", "Auditab.", "Median latency (ms)"], [
    ["Zero-shot", "0.58", "0.61", "0.42", "0.38", "0.35", "680"],
    ["Sparse (BM25)", "0.70", "0.76", "0.66", "0.62", "0.71", "880"],
    ["Dense (ANN)", "0.74", "0.80", "0.63", "0.78", "0.73", "1,020"],
    ["Hybrid (RRF + re-rank)", "0.80", "0.83", "0.69", "0.75", "0.79", "1,110"],
    ["Fusion (expand / FiD)", "0.82", "0.84", "0.71", "0.77", "0.81", "1,230"],
], font_pt=8.5)
para(doc, "CI half-widths are 0.02-0.04 throughout. Every retrieval pipeline beats the zero-shot baseline by a wide margin. "
          "The authors report that the baseline hallucinated monetary figures or outdated regulatory thresholds in roughly a "
          "third of cases, and that RAG cut this to single-digit percentages. Fusion is best on faithfulness, relevance, "
          "precision and auditability. Dense has the highest context recall, so semantic matching matters for paraphrased "
          "queries. Hybrid comes within 0.02 of fusion on most metrics while being about 120 ms faster, so the authors present "
          "it as the best balance. Latency rises steadily with pipeline complexity, from 680 to 1,230 ms.")

doc.add_heading("6. Conclusions and deployment guidance", level=2)
para(doc, "Retrieval grounding reliably improves factual behaviour. The authors recommend matching the paradigm to the "
          "deployment's priority. Use sparse or hybrid when auditability and tight latency dominate. Use dense or hybrid for "
          "paraphrase-heavy or multilingual traffic. Use fusion when maximum factual fidelity matters and batch or offline "
          "latency is acceptable, ideally with citation filtering. The stated limitations are: only two domains; results that "
          "depend on the chosen generator, encoder and index settings; automatic metrics that only approximate human judgement; "
          "and no cost or carbon accounting. Future work includes dynamic indexing, retrieval-aware decoding, long-context "
          "generators with claim-level citations, and human-in-the-loop replications in other domains.")

doc.add_heading("7. Critical assessment", level=2)
bullet(doc, "Strengths: the generator is held fixed so retrieval is isolated; unanswerable questions are included; CIs and "
            "paired tests are reported; hyperparameters are pre-registered; and auditability is a practical metric for "
            "regulated domains.")
bullet(doc, "Text and table disagree: the text and radar plot say sparse retrieval leads on auditability and context precision "
            "and that fusion loses auditability. Table 3 shows the opposite (sparse 0.71 vs fusion 0.81 auditability). The radar "
            "plot also describes the fastest system (the baseline, 680 ms) as 'skewed towards high latency'.")
bullet(doc, "Promised analyses are missing: the ablations (RQ2), cost-adjusted utility (RQ3) and the per-generator and "
            "per-difficulty breakdowns (RQ5) are not reported, and Table 3 does not say whether its numbers come from GPT-4o, "
            "Llama or both.")
bullet(doc, "Chunk size and top-k differ between pipelines, so the comparison is not purely about the retriever. Answer keys and "
            "code are only available on request, which limits reproducibility.")
bullet(doc, "Relevance to SaafHawa (Q1): our users mix English, Urdu and Roman Urdu, and our advisories must be auditable. That "
            "matches the paper's case for hybrid retrieval: dense matching for paraphrase, plus BM25 for exact terms such as "
            "PM2.5 thresholds.")

save_with_pdf(doc, HERE / "Assignment_Beta_Question_no_5_23K-0028.docx")
print("written Assignment_Beta_Question_no_5_23K-0028.docx")
