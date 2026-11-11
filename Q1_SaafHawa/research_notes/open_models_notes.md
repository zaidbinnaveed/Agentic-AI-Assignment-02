# Open-weight model research notes (access date: 2026-11-11)

Companion to `open_models.csv`. There are 10 models from 9 labs: Alibaba Qwen (2), Zhipu, Meta, DeepSeek, Moonshot, MiniMax, Mistral, OpenAI and Google. Every figure comes from a fetched page whose URL is in the CSV `src_*` columns or below. Anything that could not be read from a fetched page is marked `not verified`.

## 1. GPU facts

### On-demand cloud price (RunPod, https://www.runpod.io/pricing, fetched 2026-11-11)
RunPod bills per second with no commitment. Community Cloud H100 and A100 prices are "from" prices, so the actual rate may be higher.

| SKU | Secure Cloud ($/GPU-hr) | Community Cloud ($/GPU-hr) |
|---|---|---|
| H100 PCIe 80 GB | 2.89 | from 1.99 |
| H100 SXM 80 GB | 3.99 | from 2.69 |
| A100 PCIe 80 GB | 1.79 | from 1.19 |
| A100 SXM 80 GB | 1.79 | from 1.39 |
| L40S 48 GB | 1.09 | 0.79 (seen only in the page's structured data, not in the visible table) |

Recommended figure to cite: **RunPod Secure Cloud H100 SXM 80GB, $3.99/GPU-hr**, or **A100 SXM 80GB, $1.79/GPU-hr**.

Cross-check from Lambda (https://lambda.com/pricing; lambda.ai redirects there):
- 1x H100 SXM 80 GB: $4.89/GPU-hr.
- 1x H100 PCIe 80 GB: $3.79/GPU-hr.
- A100 80 GB is offered only as 8x HGX at $3.19/GPU-hr.
- Caveat: the page says these prices take effect 16 Nov 2026, and current prices are visible only when logged in.

### GPU memory (NVIDIA spec pages)
| GPU | Memory | Bandwidth | Source |
|---|---|---|---|
| H100 SXM | 80 GB | 3.35 TB/s | https://www.nvidia.com/en-us/data-center/h100/ |
| H100 NVL (PCIe) | 94 GB (188 GB per 2-GPU NVLink pair) | 3.9 TB/s | same page |
| A100 80GB PCIe / SXM | 80 GB HBM2e | 1,935 GB/s / 2,039 GB/s | https://www.nvidia.com/en-us/data-center/a100/ |
| L40S | 48 GB GDDR6 with ECC | 864 GB/s | https://www.nvidia.com/en-us/data-center/l40s/ |

Note: the NVIDIA page lists the PCIe-form H100 as "H100 NVL", with 94 GB. RunPod and Lambda sell an "H100 PCIe" SKU with 80 GB.

## 2. Attention type per model (checked against each Hugging Face config.json)

| Model (HF repo) | Attention | Usable for the standard KV-cache formula? | Key config fields |
|---|---|---|---|
| **meta-llama/Llama-3.3-70B-Instruct** | **Full GQA, dense** | **YES** | num_hidden_layers 80, num_attention_heads 64, num_key_value_heads 8, head_dim 128, hidden_size 8192, max_position_embeddings 131072, no sliding_window or layer_types. The Meta repo is gated, so the config was read from the identical mirror https://huggingface.co/unsloth/Llama-3.3-70B-Instruct/resolve/main/config.json |
| **Qwen/Qwen3-235B-A22B-Instruct-2507** | **Full GQA, MoE** | **YES** | Qwen3MoeForCausalLM; num_hidden_layers 94, num_attention_heads 64, num_key_value_heads 4, head_dim 128, hidden_size 4096, max_position_embeddings 262144, sliding_window null, use_sliding_window false, no layer_types; 128 experts, 8 active. https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/resolve/main/config.json |
| **mistralai/Mistral-Medium-3.5-128B** | **Full GQA, dense** | **YES** (text tower) | Mistral3ForConditionalGeneration; text_config: num_hidden_layers 88, num_attention_heads 96, num_key_value_heads 8, head_dim 128, hidden 12288, no sliding window or layer_types, max_position_embeddings 262144 (YaRN factor 64). Weights are FP8, and there is a separate vision tower. https://huggingface.co/mistralai/Mistral-Medium-3.5-128B/raw/main/config.json |
| Qwen/Qwen3-32B (extra, no CSV row) | Full GQA, dense | Yes | 64 layers, 64 heads, 8 KV heads, head_dim 128, max_position_embeddings 40960. Cheapest provider is DeepInfra at 0.08/0.28 per OpenRouter's endpoints API. |
| Qwen/Qwen3.8-27B | Hybrid: 48 Gated DeltaNet (linear) + 16 full gated-GQA layers (full_attention_interval 4) | No | Full layers: 24 Q heads, 4 KV heads, head_dim 256 |
| zai-org/GLM-5.3-Flash | Hybrid: 34 KDA linear + 11 DeepSeek-sparse MLA layers | No | kv_lora_rank 512, q_lora_rank 1536 |
| deepseek-ai/DeepSeek-V4.1-Flash(-1017) | CSA2 compressed sparse attention, sliding window 128, 1 KV head | No | Only the Sep snapshot's config was read (64 heads, 1 KV head, head_dim 512, indexer top-k 512) |
| moonshotai/Kimi-K3 | Hybrid: 69 KDA linear + 24 Gated MLA layers | No | model_type kimi_linear, 93 layers |
| MiniMaxAI/MiniMax-M3 | MiniMax Sparse Attention: layers 0-2 dense, 3-59 block-sparse (top-16 blocks of 128) | No | 60 layers, 64 heads, 4 KV heads, head_dim 128, partial rotary 0.5 |
| openai/gpt-oss-120b | Alternating sliding (window 128) and full GQA layers | No (needs a split formula) | 36 layers, 64 heads, 8 KV heads |
| google/gemma-4-31B-it | 5:1 sliding (window 1024) to full | No (needs a split formula) | 60 layers. Sliding layers: 16 KV heads, head_dim 256. Full layers: 4 KV heads, global_head_dim 512, attention_k_eq_v true |

Also checked and rejected: Mistral Large 4 (mistralai/Mistral-Large-4-1T-A52B, MLA + indexed attention), GLM-5.3 (MLA + DSA), MiniMax-M3.1-Flash (sparse attention throughout).

**Caveat on "current":** none of the newest Nov-2026 releases checked (Qwen3.8, GLM-5.3, DeepSeek V4.1, Kimi K3, MiniMax M3, Gemma 4) uses plain full attention. The three full-GQA models are older but still served:
- Llama 3.3 70B, released Dec 2024.
- Qwen3-235B-2507, released Jul 2025; Artificial Analysis marks it deprecated.
- Mistral Medium 3.5, released Apr 2026; deprecated on Mistral's API on 2026-10-31, with retirement on 2027-04-30.

Mistral Medium 3.5 is the most recent of the three.

## 3. Method and cross-model ambiguities

- **How the cheapest provider was chosen:** from OpenRouter's endpoints API (`https://openrouter.ai/api/v1/models/<slug>/endpoints`; the HTML providers page did not render provider data), plus Artificial Analysis provider pages and provider pricing pages. Ties and blends used a 3:1 input:output ratio.
  - Some of the cheapest endpoints are **Flex / best-effort tiers**, which are slower and may be unavailable at times: DeepSeek on Particle AI, and MiniMax-M3 on DeepInfra Flex. These may be unsuitable for real-time WhatsApp replies. Real-time alternatives are given in each row's notes.
- **Benchmarks are not perfectly uniform:**
  - **bench1** is GPQA Diamond for every model. The source varies: Artificial Analysis for Qwen3.8, GLM, Qwen3-235B, MiniMax and Mistral; the model card for Llama, DeepSeek, Kimi, gpt-oss and Gemma. Reasoning settings also vary.
  - **Tool benchmark:** Artificial Analysis has replaced τ²-Bench Telecom with τ³-Banking for current models.
    - τ²-Bench Telecom (Artificial Analysis): Qwen3-235B 33.33, MiniMax-M3 88.9, Mistral Medium 3.5 94.2.
    - τ³-Banking: Qwen3.8-27B 48.04, GLM-5.3-Flash 47.22 (both Artificial Analysis), Kimi K3 33.4 (model card).
    - Others: Tau-Bench Retail for gpt-oss 67.8; "Tau2 (average over 3)" for Gemma 4 76.9; BFCL v2 for Llama 77.3.
    - DeepSeek: none found (not verified).
    - These are different variants. Compare within the same variant only.
- **TTFT definitions differ:**
  - Several values are Artificial Analysis "time to first answer token", which includes thinking time: Llama 7.11 s and Gemma 7.74 s.
  - Others are true time to first token: Qwen3.8 1.663 s, Qwen3-235B 3.410 s, MiniMax 1.41 s, Mistral 7.13 s. The MiniMax figure is for DeepInfra's standard endpoint, not Flex.
  - OpenRouter returned null latency and throughput for every endpoint.
- **Rate limits:**
  - DeepInfra publishes only 200 concurrent requests per model, with no RPM or TPM cap (https://docs.deepinfra.com/account/rate-limits).
  - Mistral shows its limits only in the logged-in admin panel.
  - DeepSeek's first-party API publishes concurrency only (2500 for flash): https://api-docs.deepseek.com/quick_start/rate_limit
  - OpenRouter: "no platform-level request cap" for paid models (https://openrouter.ai/docs/api/reference/limits).
  - Particle AI, Wafer, NEAR AI, Relace, Multiverse and CoreWeave: no RPM or TPM numbers found.
- **Caching:**
  - DeepInfra caching is automatic prefix matching. The optional `prompt_cache_key` and paid retention (5 min / 1 h) are documented without a minimum prefix or default TTL (https://docs.deepinfra.com/chat/prompt-caching).
  - First-party rules from OpenRouter's caching guide (https://openrouter.ai/docs/guides/best-practices/prompt-caching):
    - DeepSeek: automatic; writes at the input price, reads at 0.1x input.
    - Moonshot: automatic; writes free, reads at 0.25x input.
  - Mistral: cache read at 10% of input; minimum 64 tokens per the Mistral docs; no TTL stated.
- **Language support:** Llama 3.3's officially supported languages do not include Urdu. Urdu and Roman Urdu quality was not benchmarked for any model.

## 4. Every `not verified` value, by model

- **Llama 3.3 70B (DeepInfra Turbo):**
  - Throughput for the DeepInfra endpoint (the Artificial Analysis median across providers is 73 tok/s).
  - RPM and TPM.
  - Whether the Flex 0.8x tier applies to this model.
- **Qwen3-235B-A22B-2507 (DeepInfra):** RPM, TPM.
- **Qwen3.8-27B (Multiverse):**
  - Cache write premium, minimum tokens, TTL and mode. The cache price of 0.0171 comes from Artificial Analysis only.
  - Rate-limit tier, RPM, TPM.
  - The provider's max output.
  - Whether the served model is compressed.
- **GLM-5.3-Flash (Relace):**
  - Cache write premium, minimum tokens, TTL and mode.
  - Rate-limit tier, RPM, TPM.
  - TTFT and throughput at Relace (the Wafer figures are in the notes).
  - Reasoning-token count at low.
  - src_rate_limits.
- **DeepSeek V4.1 Flash 1017 (Particle AI flex):**
  - Cache write premium, minimum tokens, TTL.
  - Rate-limit tier, RPM, TPM.
  - TTFT and throughput.
  - Tool benchmark name and score.
  - Reasoning tokens at the lowest setting.
  - Whether Particle honours non-thinking mode.
  - src_rate_limits, src_bench2.
- **Kimi K3 (Wafer):**
  - Cache write premium, minimum tokens, TTL and mode.
  - Rate-limit tier, RPM, TPM.
  - TTFT and throughput.
  - Average reasoning tokens at low.
  - Native max output.
  - src_rate_limits.
- **MiniMax-M3 (DeepInfra Flex):**
  - Cache write premium, minimum tokens, TTL.
  - RPM, TPM.
  - Average reasoning tokens with thinking disabled.
  - Native max output.
- **Mistral Medium 3.5 (Mistral API):**
  - Cache write premium, TTL.
  - RPM, TPM.
  - Average reasoning tokens at none.
  - Native max output.
- **gpt-oss-120b (NEAR AI via OpenRouter):**
  - Cache write premium, minimum tokens, TTL.
  - Rate-limit tier, RPM, TPM.
  - TTFT and throughput (NEAR AI is not on Artificial Analysis).
  - NEAR AI's own pricing page does not list the model; the price was seen only on OpenRouter.
- **Gemma 4 31B (CoreWeave):**
  - Cache minimum tokens, TTL.
  - RPM, TPM.
  - Throughput.
  - Token count of the empty thought block.

## 5. Other ambiguities

- **DeepSeek V4.1 Flash parameters:** the card gives 552B (16B active decode, 8B prefill), but the HF metadata shows 763B. GPQA 90.9 comes from the September snapshot's card.
- **Kimi:** K3 was chosen because it has the most endpoints on OpenRouter. Artificial Analysis marks it deprecated in favour of `moonshotai/Kimi-K3.1-Pro` (Wafer: $0.32 in / $10 out / $0.18 cached).
- **MiniMax-M3:**
  - The licence grant wording says "non-commercial purposes", which conflicts with its commercial-use clause. Read the licence.
  - DeepInfra serves a 524288-token context; the card says 1M.
- **gpt-oss-120b:** NVIDIA's copy of the card says 5.7B active in one section and 5.1B elsewhere. Benchmarks are at high reasoning effort and were taken from NVIDIA's copy because openai.com returned 403.
- **Gemma 4 31B:** CoreWeave caching gives no discount (cache read = input price).
- **Llama 3.3 70B:** GPQA Diamond is 50.5 on the model card, but the HF eval widget shows 51.52.
