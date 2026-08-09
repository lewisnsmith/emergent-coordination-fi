# Cost and Execution Runbook

**Pricing verified:** 2026-07-13. All amounts are USD before tax.

This runbook converts the staged research design into API calls, token costs,
GPU hours, storage, and CPU analysis time. It is a planning estimate, not a
vendor quote. Re-run the pilot calibration before authorizing either the base
or high program.

Machine-readable inputs are in:

- `configs/budgets/pricing.yaml` — verified standard-execution prices.
- `configs/budgets/run-matrix.yaml` — low/pilot, base, and high workloads.

## Scope boundary

The run matrix budgets the broader research program, not just the first paper. Every component is
therefore assigned to one of three authorization scopes:

- `first_paper` — H1/H3/H4 MPHIQ and semantic-equivalence work.
- `separate_h5` — the simulator-only AI-capital-share experiment, which is not part of the first
  paper's confirmatory family.
- `future_program` — H6 trust/delegation, H12 prompt pressure, and H13 local-model fidelity work.
  H8/H13 mechanistic GPU work is budgeted separately rather than treated as ordinary decision
  calls.

**Retention rule:** authorization scope and cost never remove a hypothesis from the canonical
program. High-cost work may be staged, deferred, supported through credits, or partly satisfied by
qualified external evidence, but the underlying hypothesis and claim boundary remain recorded.
Removal or substantive merger requires a scientific rationale unrelated to cost and a visible
preregistration amendment. The machine-readable rule and high-cost registry live in
`configs/research-program.yaml`.

| Scenario | First paper | Separate H5 | Future program | Full-program total |
|---|---:|---:|---:|---:|
| Pilot | 74,880 | 11,520 | 48,960 | 135,360 |
| Base cumulative | 4,068,480 | 126,720 | 1,978,560 | 6,173,760 |
| High cumulative | 11,134,080 | 241,920 | 3,908,160 | 15,284,160 |

Authorizing only the first-paper pilot defers 60,480 decisions, or 44.7% of the full pilot.
At the base ceiling it defers 2,105,280 cumulative decisions, or 34.1%. These are call-count
reductions, not final dollar estimates: endpoint mix, retries, fixed compute overhead, and the
deferral of H8 mechanistic GPU work must be recalculated before purchasing credits or compute.

The full-program totals below remain useful as ceilings, but they are not one indivisible study.
External datasets or prior experiments may later reduce bridge or exploratory work; no such saving
is counted here until the artifacts pass provenance and comparability review and the analysis plan
records how they will be used.

### H13 local-first sidecar

H13 was added after the existing full-program call ceilings were calculated, so its sidecar below
is **not included** in the scenario totals above or in the historical dollar estimates below. Keep
it separate until exact checkpoints, hardware throughput, frontier endpoints, context lengths, and
output caps are benchmarked.

| H13 pilot component | Formula | Workload/cap |
|---|---|---:|
| Local free-running precision screen | 2 families × 2 sizes × 4 precisions × 4 depths × 50 items | 3,200 local chains |
| Local gold-prefix scoring | 2 families × 2 sizes × 4 precisions × 50 items × (2+4+8+16 steps) | 24,000 scored prefixes |
| Frontier financial-chain bridge | 384 held-out chains × 2 endpoints | 768 API calls |
| Frontier repeat sample | about 10% of chains × 2 extra repeats × 2 endpoints | 154 API calls |
| Frontier short replay | 12 blocks × 30 steps × 4 agents × 2 endpoints | 2,880 API calls |
| **Frontier bridge cap** |  | **3,802 API calls** |
| Mechanistic discovery | coarse-to-fine layers/sites after behavioral gate | 24 H100-hours |
| Mechanistic confirmation | frozen sites on held-out blocks/family | 80 H100-hours, separately authorized |

The 3,802-call bridge is about 96.6% below the existing 112,800-API-decision full-program pilot
assumption. It is not powered merely because it has thousands of calls: its evidence comes from
held-out template/document/market clusters. Use 25–50 items per depth cell for local screening,
8–12 discovery clusters for nuisance estimates, and power roughly 24–32 paired confirmatory
clusters with a preregistered blinded cap near 48.

Do not assign a dollar figure yet. First benchmark local token throughput and measure actual
frontier input, visible output, reasoning tokens, retries, and latency on a small authorized canary.
Then multiply the fixed call cap by the selected endpoints' measured usage and add the same spend
abort and contingency rules used elsewhere in this runbook.

## Recommendation

Do not buy the whole confirmatory budget up front.

1. Authorize the 74,880-call first-paper pilot first and recalculate its dollar envelope from the
   selected endpoints. Stage H5, H6, H8, H12, and H13 separately without removing their
   hypotheses.
2. Keep **$2,300** as the ceiling only for the full-program pilot: $1,100 API, $1,000 GPU/VM,
   and $200 CPU/storage.
3. Measure actual provider-specific tokens, parse retries, throughput, and
   exclusion rates. Recalculate every later stage from those observations.
4. If the pre-registered stop/go gates pass, treat **$121,000** as the full-program base
   ceiling: $100,000 API, $20,000 GPU/VM, and $1,000 auxiliary.
5. Treat **$580,000** as a full-program sensitivity ceiling, not as the default plan. It is
   needed only if pilot power analysis requires twenty seeds and the expanded
   robustness battery.

Only the scoped first-paper pilot is a current authorization recommendation. The $2,300 pilot and
the base and high figures are full-program ceilings: do not prebuy those credits before scope,
pilot power, usage, failure-rate, and throughput measurements are complete.

The full-program base API split for work performed on or after 2026-09-01 is:

| Provider | Credits/budget |
|---|---:|
| OpenAI | $39,000 |
| Anthropic | $50,000 |
| Google | $11,000 |
| **Total** | **$100,000** |

These rounded amounts include approximately 15% API contingency.

## Cost equations

One LLM decision is normally one model request. A malformed response triggers
one format-repair request, so calls and billable requests are not identical.

```text
decisions = sum(cells * environments * seeds * steps * LLM_agents)

API_decisions   = decisions * 5/6
local_decisions = decisions * 1/6

billable_API_requests = API_decisions * (1 + retry_rate)

API_cost(model) = requests(model)
                * (input_tokens * input_price
                   + output_tokens * output_price)
                / 1,000,000
```

The six endpoints are two OpenAI models, two Anthropic models, one Google
model, and one local open-weight model. They are balanced inside experimental
cells. The six endpoints, 24 personas, and five semantic prompt variants are
not blindly crossed with all 32 MPHIQ schemes.

For Anthropic, the calculation multiplies estimated token counts by 1.30.
Anthropic states that Claude Opus 4.7+ and Claude Sonnet 5 use a tokenizer that
produces approximately 30% more tokens for the same text. This adjustment is
conservative and must be replaced with measured usage after the pilot.

Local serving cost is benchmark-driven:

```text
GPU_hours = generated_tokens / effective_generated_tokens_per_second / 3,600
          + prefill + model_load + idle + orchestration overhead

VM_cost = instance_hours * hourly_instance_price
```

For an eight-GPU instance, `GPU_hours = instance_hours * 8`.

## Official price basis

The executable catalog uses standard synchronous inference and therefore sets
`batch_discount: 0.0`. OpenAI, Anthropic, and Google advertise roughly 50%
Batch/Flex reductions for the listed models, but the current experiment is
sequential: the decision at step `t+1` depends on the portfolio created at
step `t`. A discount must not be budgeted until a wavefront/batch runner is
implemented and verified.

| Endpoint | Input / MTok | Output / MTok | Notes |
|---|---:|---:|---|
| GPT-5.6 Sol | $5.00 | $30.00 | Standard processing |
| GPT-5.6 Terra | $2.50 | $15.00 | Standard processing |
| Claude Opus 4.8 | $5.00 | $25.00 | Plus the tokenizer-count adjustment |
| Claude Sonnet 5 | $2.00 | $10.00 | Introductory rate through 2026-08-31 |
| Claude Sonnet 5 | $3.00 | $15.00 | Announced rate from 2026-09-01 |
| Gemini 3.1 Pro Preview | $2.00 | $12.00 | Output includes thinking tokens |

Official sources:

- [OpenAI API pricing](https://openai.com/api/pricing/),
  [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), and
  [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
- [Anthropic Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

The local endpoint assumption is `gpt-oss-120b`. OpenAI describes it as a
117B-parameter, 5.1B-active-parameter MXFP4 model that fits on one 80 GB H100.
See [Introducing gpt-oss](https://openai.com/index/introducing-gpt-oss/) and the
[gpt-oss-120b model page](https://developers.openai.com/api/docs/models/gpt-oss-120b).

| VM shape | Instance price/hour | GPUs | Effective H100 price |
|---|---:|---:|---:|
| Runpod H100 PCIe | $2.89 | 1 | $2.89/GPU-hour |
| CoreWeave HGX H100 | $49.24 | 8 | $6.155/GPU-hour |
| GCP `a3-highgpu-8g` | $88.490000119 | 8 | $11.061/GPU-hour |
| GCP `e2-standard-4` | $0.13402284 | 0 | CPU analysis only |

Sources: [Runpod pricing](https://www.runpod.io/pricing),
[CoreWeave pricing](https://coreweave.com/pricing),
[GCP accelerator VM pricing](https://cloud.google.com/products/compute/pricing/accelerator-optimized),
and [GCP general-purpose VM pricing](https://cloud.google.com/products/compute/pricing/general-purpose).

Runpod is the quoted option that supports a true single-H100 pilot. The quoted
CoreWeave and GCP on-demand shapes contain eight H100s.

## Token and retry envelopes

The current prompt contains a persona/mandate, a 20-bar observation window,
five symbols, duplicated human- and machine-readable market summaries, the
portfolio, events, and structured-output instructions. Reasoning/thinking
tokens can materially exceed the short visible JSON response.

| Case | Input/request | Output/request | Retry rate used |
|---|---:|---:|---:|
| Pilot/low | 1,200 | 150 | 1% |
| Base/expected | 2,200 | 350 | 3% |
| High | 4,000 | 800 | 10% |

The existing model configuration caps completion output at 1,024 tokens. The
high case remains below that cap but allows substantial hidden reasoning. Any
increase in the cap requires a fresh cost estimate.

## Pilot call count

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ screen | 32 × 1 environment × 3 seeds × 60 steps × 8 agents | 46,080 |
| Semantic equivalence | 4 schemes × 5 variants × 1 × 3 × 60 × 8 | 28,800 |
| Prompt-pressure fractional screen | 16 cells × 1 × 3 × 60 × 8 | 23,040 |
| Exchange/AI share | 6 shares × 1 regime × 3 × 80 × 8 | 11,520 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 3 | 25,920 |
| **Total** |  | **135,360** |

Split: 112,800 API decisions and 22,560 local decisions. At a 1% repair rate,
the budget covers 113,928 API requests.

Estimated standard API cost is **$858.90** through 2026-08-31 or **$916.66**
after the announced Claude Sonnet 5 price change. With contingency, buy about
$1,100 of API capacity.

## Base call count

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ confirmation | 32 × 8 environments × 10 seeds × 120 steps × 8 agents | 2,457,600 |
| Semantic equivalence | 4 schemes × 5 variants × 8 × 10 × 120 × 8 | 1,536,000 |
| Full prompt pressure | 24 cells (`3×2×2×2`) × 8 × 10 × 120 × 8 | 1,843,200 |
| Exchange/AI share | 6 shares × 3 regimes × 10 × 80 × 8 | 115,200 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 10 | 86,400 |
| **Confirmation increment** |  | **6,038,400** |
| Prior pilot |  | 135,360 |
| **Cumulative total** |  | **6,173,760** |

Cumulative split: 5,144,800 API decisions and 1,028,960 local decisions. Applying
the pilot's 1% retry rate to pilot calls and 3% to confirmation calls produces
**5,296,888 billable API requests**.

Estimated cumulative standard API cost is **$80,463.99** through 2026-08-31
or **$85,844.65** after the Claude price change. The $100,000 API ceiling adds
approximately 15% contingency to the later price and rounds by provider.

## High sensitivity call count

The twenty-seed design replaces the ten-seed base matrix; it is not twenty
additional seeds after completing all ten base seeds. Only the pilot is added
to its total.

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ sensitivity | 32 × 8 × 20 × 120 × 8 | 4,915,200 |
| Expanded semantic equivalence | 8 schemes × 5 variants × 8 × 20 × 120 × 8 | 6,144,000 |
| Full prompt pressure | 24 cells (`3×2×2×2`) × 8 × 20 × 120 × 8 | 3,686,400 |
| Exchange/AI share | 6 shares × 3 regimes × 20 × 80 × 8 | 230,400 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 20 | 172,800 |
| **Sensitivity matrix** |  | **15,148,800** |
| Prior pilot |  | 135,360 |
| **Cumulative total** |  | **15,284,160** |

Cumulative split: 12,736,800 API decisions and 2,547,360 local decisions.
Stage-specific retries produce **14,000,328 API requests**.

Estimated cumulative standard API cost is **$435,225.50** through 2026-08-31
or **$464,166.97** afterward. Fifteen percent contingency raises the later
case to about **$534,000**; the provider-rounded ceiling is **$536,000**.

## Local inference and mechanistic-interpretability budget

Local serving hours include model loading, prompt prefill, generation, and
idle/orchestration loss. They are deliberately ranges because effective
throughput depends on continuous batching and the final reasoning effort.

| Scenario | Local serving | Mech pilot | Mech confirmation | Total H100 GPU-hours |
|---|---:|---:|---:|---:|
| Pilot | 50–120 | 80–160 on 1 H100 | — | 130–280 |
| Base | 900–2,300 | 80–160 on 1 H100 | 200–500 wall hours on 8 H100s = 1,600–4,000 | 2,580–6,460 |
| High | 3,300–8,700 | 80–160 on 1 H100 | 200–500 wall hours on 8 H100s = 1,600–4,000 | 4,980–12,860 |

At the listed prices, those totals cost:

| Scenario | Runpod | CoreWeave equivalent | GCP equivalent |
|---|---:|---:|---:|
| Pilot | $376–$809 | $800–$1,723 | $1,438–$3,097 |
| Base | $7,456–$18,669 | $15,880–$39,761 | $28,538–$71,456 |
| High | $14,392–$37,165 | $30,652–$79,153 | $55,085–$142,248 |

The CoreWeave and GCP figures are normalized GPU-hour comparisons; their
eight-GPU minimum shapes can create additional idle cost. Mechanistic work on
quantized MXFP4 weights must not automatically be interpreted as equivalent
to BF16/full-precision mechanisms. Confirmatory activation-patching and
causal-tracing results should therefore use the precision stated in the
pre-registration and record it in every artifact manifest.

The H13 24/80-hour funnel supersedes the assumption that an 80–160-hour mechanistic pilot should
start before a precision-related behavioral question is established. The older table remains the
ceiling for the broader H8 program. H13 first streams logit and activation summaries from the local
screen, retains raw tensors only for shortlisted layers/tokens, and releases the 80-hour
confirmation authorization only after frozen behavioral and reconstruction gates pass.

## CPU and storage

Ordinary result records are estimated at 3–8 KB per decision before caches and
backups: roughly 0.4–1.1 GB pilot, 19–50 GB base, and 46–123 GB high. The
rounded reservations are 10 GB, 100 GB, and 500 GB respectively.

Mechanistic activation tensors dominate storage. Temporary reservations are:

| Scenario | Activations | Runpod high-performance storage/month | Analysis VM hours | CPU estimate |
|---|---:|---:|---:|---:|
| Pilot | 0.5 TB | ~$70 | 250 | ~$34 |
| Base | 2 TB | ~$280 | 1,700 | ~$228 |
| High | 10 TB | ~$1,400 | 6,000 | ~$804 |

Stream aggregate statistics and discard raw activations after their hashes,
derived artifacts, and verification checks are complete. Do not retain every
layer × token × prompt tensor indefinitely.

## Stop/go controls

Before expanding beyond the pilot, verify all of the following:

- Provider invoice token counts reconcile with decision-log usage fields.
- Thinking/reasoning tokens are included in the logged output total.
- Parse-repair rates remain within the pre-registered exclusion threshold.
- The local H100 benchmark reports effective throughput at the actual context,
  output cap, reasoning effort, precision, and concurrency.
- H13 same-checkpoint pairs reconcile tokenizer, prompt, quantizer, calibration, runtime, and
  hookable/deployed logits; native low-precision-only weights are excluded from causal precision
  claims.
- The H13 frontier bridge stops at its call and dollar caps; local cells expand only where the
  attainable interval can resolve the frozen equivalence or difference margin.
- Exact model snapshots are available for confirmatory runs. A moving alias or
  preview model is not sufficient for reproducibility.
- Pilot variance and intraclass correlation justify ten or twenty independent
  seeds; repeated agent calls are not treated as independent market evidence.
- Every stage has a hard provider spend limit and aborts before exhausting the
  next stage's reserved credits.

## Important caveats and exclusions

- The repository's content-addressed response cache prevents paying twice for
  an exact rerun. It does not discount the first run: keys include model,
  temperature, seed, prompts, and dynamic portfolio observations.
- Provider-side prompt caching is not assumed. The dynamic observation and
  portfolio make up much of each prompt, and cache accounting is not yet
  represented completely in the usage schema.
- Google bills Gemini output including thinking tokens. The cost ledger must
  verify that the SDK usage fields include them rather than recording only
  visible candidate tokens.
- Anthropic has no seed parameter. Its reproducibility depends on exact model
  versions, recorded prompts, and the local response cache.
- The current prices can change. Re-verify all sources immediately before a
  paid sweep and preserve a dated pricing snapshot in the run manifest.
- H9–H11 signature transport, market detection, causal attribution, and data
  packaging primarily add analysis work, not new LLM calls. They are covered
  in the CPU/storage allowance.
- Trust/adoption vignette LLM calls prepare and validate experimental stimuli;
  they are not a substitute for human participants. Participant recruitment,
  compensation, IRB/ethics review, consent administration, survey hosting,
  and study operations are excluded and remain TBD.
- The budget excludes taxes, network egress, commercial market-data licenses,
  paid survey recruitment, legal/compliance review, and human annotation. The
  current estimate assumes the planned public market/reference datasets can
  be acquired without license fees.
