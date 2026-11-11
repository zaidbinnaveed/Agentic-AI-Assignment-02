# Closed-source model research notes (accessed 2026-11-11)

Companion to `closed_models.csv`. There are 9 models from 4 providers: OpenAI (gpt-6-luna, gpt-6.1-terra, gpt-6.1-sol), Anthropic (claude-haiku-5-5, claude-sonnet-5-5), Google (gemini-3.8-flash, gemini-3.5-flash-lite) and xAI (grok-4.3, grok-4.7).

## Benchmarks

- **τ²-bench and GPQA Diamond could not be used across all models.** Artificial Analysis (AA) moved to Intelligence Index v5.0.1, and its current model entries have `tau2: null` and usually `gpqa: null`. The provider launch pages report different benchmarks (for example, Anthropic's Haiku 5.5 page reports GDPval-AA, OSWorld 2.1 and Terminal-Bench 4.0).
- **Benchmarks used instead.** Both come from AA and cover all 9 models:
  - bench1 is **GDPval-AA v2.1** (an Elo rating).
  - bench2, the tool-use benchmark, is **AutomationBench-AA**. AA describes it as its run of Zapier's AutomationBench, "realistic SaaS workflows ... using REST APIs as the tool interface". The figure is the `automationBenchPartialScore` field, converted to a percentage.
- **Extra scores in the `notes` column.** Only Grok 4.3 (Non-reasoning) has a τ²-Bench Telecom score on AA (65.8%). Gemini 3.8 Flash (Low) and Gemini 3.5 Flash-Lite have GPQA Diamond scores on AA.
- **Which variant was used.** Each model uses the AA variant closest to its lowest setting: Non-reasoning for Luna, Terra and Grok 4.3; Low for Sol, Haiku, Sonnet, Gemini 3.8 Flash and Grok 4.7; and the single listed variant for Gemini 3.5 Flash-Lite. Scores at higher effort are higher.
- **How the AA values were read.** The values come from the JSON data embedded in each AA model page (fetched with curl and parsed). The `headline`, `canonicalIntelligenceIndexTokenCount` and `intelligenceIndexOutputTokensPerTask` fields were used.

## Latency (Artificial Analysis)

- **How AA measures it.** The headline TTFT and output speed average four workloads (1k, 10k and 100k input, plus multi-turn agentic) over the last 5 days. They are measured under concurrent load on the provider's own endpoint.
  - Output speed includes reasoning tokens and the TTFT.
  - For reasoning variants, TTFT is the time to the first reasoning token.
  - The 10k-input TTFT is closest to a ~6k-token WhatsApp prompt, so it is given in each row's notes.
- **Claude Haiku 5.5.** AA only benchmarks it with adaptive thinking on. Its TTFT with thinking disabled (the true lowest setting) is not measured.

## Tier and limit ambiguities

- **OpenAI.** The paid tiers are now named Build, Launch and Grow. "Tier 1" no longer exists. Build ($5 in credit purchases) is the first paid tier, but the docs don't say outright that new accounts start there.
- **Anthropic.** The tiers are Start, Build, Scale and Custom. New organizations "may start in the Evaluation tier" with lower, unpublished limits. The CSV gives Start-tier limits.
  - The Start tier has a **$500/month spend cap** (Build $1,000, Scale $200,000). A ~$1,500/month budget would hit that cap.
  - ITPM counts only uncached input.
- **Google.** The per-model RPM and TPM for Tier 1 are **not published in the docs**. They appear only in the AI Studio console.
  - Tier 1 has a $250 billing-tier cap and a $10-per-10-minutes spend-rate limit.
  - Tier 2 requires $100 paid plus 3 days, and has a $2,000 cap.
- **xAI.** Limits are given in requests per **second**, not per minute: Grok 4.7 has 150 RPS and 50M TPM, and Grok 4.3 has 37 RPS and 10M TPM, at Tier 0 (the $0 default).
  - The RPM column is marked not verified, because converting RPS to RPM would be a derived figure.
  - xAI's docs say each team's personalized limits are shown in the console.

## Status and pricing caveats

- **Gemini 3.8 Flash.** Prices are scheduled to **double on 2027-01-01**: $1.50 input / $7.50 output / $0.15 cache.
- **Gemini 2.5 models.** gemini-2.5-flash and gemini-2.5-pro are deprecated and reroute on 2026-12-01, so they were excluded.
- **Status labels.** All Gemini models chosen are labelled Stable. Anthropic's are "Active (latest)". xAI and OpenAI don't give preview or GA labels for these models.
- **Long-context tiers.** These don't affect prompts under ~6k tokens:
  - OpenAI: above 272K tokens.
  - Anthropic Haiku 5.5: above 100K tokens.
  - xAI: 200K tokens or more.
  - No prompt-size tier is listed for Gemini 3.8 Flash or 3.5 Flash-Lite.
- **Claude Sonnet 5.5** is not Anthropic's flagship. Opus 5.5 ($4/$20) and Fable 5.2 ($8/$40) sit above it. The flagship-class models included are gpt-6.1-sol and grok-4.7.
- **Tokenizer.** Claude models from 4.7 onward use a new tokenizer that produces about 30% more tokens for the same text. This affects cost comparisons across providers.

## Licence sources

- **Fetched and confirmed:**
  - Anthropic Commercial Terms: no reverse engineering, no competing models, and no self-hosting right.
  - Gemini API Additional Terms: no reverse engineering or extracting of "parameter weights".
- **Could not be fetched:**
  - The OpenAI Services Agreement returned HTTP 403, and its PDF was not text-extractable.
  - The xAI Enterprise Terms returned HTTP 403.
  - For both, the "proprietary / no self-host" classification rests on API-only availability and AA's `openSourceCategorization: proprietary, isOpenWeights: false`, which was verified for all 9 models. The exact contract wording is **not verified**.

## Values marked `not verified` / `not disclosed`

- **Parameter counts:** `not disclosed` for all 9 models (AA shows `parameters: null`; AA's Haiku page says Anthropic has not revealed model size).
- **Max output tokens:** grok-4.3 and grok-4.7.
- **Prompt caching:**
  - Minimum cacheable tokens: gemini-3.5-flash-lite, grok-4.3 and grok-4.7.
  - Cache TTL: grok-4.3 and grok-4.7. For Gemini, the implicit-cache TTL isn't stated; the explicit-cache default is 1 hour.
  - Cache-write premium: grok-4.3 and grok-4.7. The docs mention no write fee, but they don't state that there is none.
- **Rate limits:**
  - RPM and TPM: gemini-3.8-flash and gemini-3.5-flash-lite.
  - RPM: grok-4.3 and grok-4.7 (only RPS is published).
- **Average reasoning tokens at the lowest setting:**
  - gemini-3.8-flash at low: AA has no token counts for that variant.
  - claude-sonnet-5-5 at between_tools.
  - grok-4.3 at none: reasoning is off per the docs, but AA's token count isn't available.
- **Licence wording:** the OpenAI and xAI contract text (see above).
