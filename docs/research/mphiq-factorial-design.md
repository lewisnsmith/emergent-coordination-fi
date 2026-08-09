# MPHIQ Factorial Design

This protocol operationalizes the five-factor sameness experiment defined in
[`configs/designs/mphiq.yaml`](../../configs/designs/mphiq.yaml). It is subordinate to the
frozen preregistration, when one exists, and must be versioned with any amendment.

## Research question

When agents invest in the same environment, which shared components cause convergence: the
model, investor profile, harness, information, or task wording? The design estimates each
component's marginal effect and whether combinations of shared components amplify one another.

The five letters are ordered `M P H I Q`:

| Bit | Factor | `1` means same | `0` means balanced different |
|---|---|---|---|
| M | Model | Exact provider, model ID/checkpoint, revision, and endpoint class resolve to one hash | Agents are balanced across at least two eligible frontier models |
| P | Investor profile | Fully rendered profile, financial facts, and mandate resolve to one hash | Agents are balanced across preregistered structured profiles |
| H | Harness | Decoding, reasoning, memory, output limit, and response mode resolve to one hash | Agents are balanced across supported preregistered harness presets |
| I | Information | Market evidence and events are byte-identical before agent portfolio state is attached | Agents receive balanced, equally sized, cutoff-matched evidence partitions |
| Q | Task wording | The task frame resolves to one hash | Agents receive balanced semantically equivalent paraphrases |

The coding is literal: `1 = same is true`; `0 = same is false and designed difference is true`.
Zero never means missing, uncontrolled, or randomly heterogeneous. Profile and information blocks
are excluded from the Q comparison because they are their own factors. Substantively different
prompt families are not Q paraphrases; they require a separate declared treatment.

## The 32 schemes

Every possible binary code is required. The table inherits the factor definitions above.

| Code | M | P | H | I | Q | Code | M | P | H | I | Q |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `00000` | 0 | 0 | 0 | 0 | 0 | `10000` | 1 | 0 | 0 | 0 | 0 |
| `00001` | 0 | 0 | 0 | 0 | 1 | `10001` | 1 | 0 | 0 | 0 | 1 |
| `00010` | 0 | 0 | 0 | 1 | 0 | `10010` | 1 | 0 | 0 | 1 | 0 |
| `00011` | 0 | 0 | 0 | 1 | 1 | `10011` | 1 | 0 | 0 | 1 | 1 |
| `00100` | 0 | 0 | 1 | 0 | 0 | `10100` | 1 | 0 | 1 | 0 | 0 |
| `00101` | 0 | 0 | 1 | 0 | 1 | `10101` | 1 | 0 | 1 | 0 | 1 |
| `00110` | 0 | 0 | 1 | 1 | 0 | `10110` | 1 | 0 | 1 | 1 | 0 |
| `00111` | 0 | 0 | 1 | 1 | 1 | `10111` | 1 | 0 | 1 | 1 | 1 |
| `01000` | 0 | 1 | 0 | 0 | 0 | `11000` | 1 | 1 | 0 | 0 | 0 |
| `01001` | 0 | 1 | 0 | 0 | 1 | `11001` | 1 | 1 | 0 | 0 | 1 |
| `01010` | 0 | 1 | 0 | 1 | 0 | `11010` | 1 | 1 | 0 | 1 | 0 |
| `01011` | 0 | 1 | 0 | 1 | 1 | `11011` | 1 | 1 | 0 | 1 | 1 |
| `01100` | 0 | 1 | 1 | 0 | 0 | `11100` | 1 | 1 | 1 | 0 | 0 |
| `01101` | 0 | 1 | 1 | 0 | 1 | `11101` | 1 | 1 | 1 | 0 | 1 |
| `01110` | 0 | 1 | 1 | 1 | 0 | `11110` | 1 | 1 | 1 | 1 | 0 |
| `01111` | 0 | 1 | 1 | 1 | 1 | `11111` | 1 | 1 | 1 | 1 | 1 |

`11111` is total sameness. `00000` is maximum designed heterogeneity. Neither is sufficient by
itself: the main effects come from all 16 Hamming-distance-one pairs for each bit.

## Questions and estimands

| Question | Estimand | Direction |
|---|---|---|
| Does sharing a model increase convergence? | Mean paired difference in convergence when M flips `0→1`, averaging over P/H/I/Q | Same minus different |
| Do profiles, harnesses, information, or wording matter? | Corresponding average paired effect for P, H, I, or Q | Same minus different |
| Is information diversity more effective than profile diversity? | Absolute decorrelation effect of I minus absolute decorrelation effect of P | Positive supports H4 |
| Do shared components reinforce one another? | Difference-in-differences for preregistered two-factor interactions | Interaction scale |
| Does sameness spread existing convergence? | Change in capital-weighted synchronized-cluster size and affected-symbol coverage | Positive means broader convergence |

Primary convergence endpoints are per-symbol Cohen's kappa, portfolio overlap, and strategy
fingerprint similarity as defined in [Metrics](metrics.md). Capital-weighted synchronized
cluster size is primary for breadth. Action distributions, active-trade agreement, turnover,
constraint binding, and parse/safeguard failures are mandatory diagnostics.

Each effect is first computed inside a complete independent block and then averaged across blocks.
Results may be generalized to the tested model set. Generalization to all frontier models requires
a model-sampling argument and leave-one-provider-family-out stability.

## Independent units and nesting

The independent replication unit is a nonoverlapping market-window-by-seed block. For a shared
exchange it is an independently initialized market replica. All 32 schemes share common market
innovations inside a block so Hamming-pair contrasts are paired.

Agents, agent pairs, symbols, steps, retries, cached responses, prompt paraphrases, and repeated API
calls are nested observations. They increase precision within a block but do not increase the
number of independent market replications. Pairwise metrics share agents and are therefore dyadic,
dependent measurements. They must be aggregated to the block or analyzed with a preregistered
dyadic/multi-membership method; ordinary row-level standard errors are prohibited.

Overlapping historical windows are one dependence cluster unless the analysis explicitly models
their overlap. Changing an LLM sampling seed without changing the market window is not a new market
replication.

## Randomization and balance

Before any provider call:

1. Freeze eligible model, profile, harness, information, and paraphrase level catalogs.
2. Generate independent block IDs and all 32 scheme assignments from the run seed.
3. Allocate zero-bit levels as evenly as possible; any count difference must be at most one.
4. Make simultaneous zero-bit assignments orthogonal or near-orthogonal and reject perfect
   confounding.
5. Preserve cohort size, capital, market path, and nonflipped assignments across Hamming pairs.
6. Randomize execution order within provider-rate-limit strata and blind treatment labels in the
   analysis table.
7. Write and hash the assignment plan before inference begins.

Information partitions must have the same cutoff, evidence-item count, and token budget within 2%.
Prompt variants must belong to one human-reviewed semantic-equivalence group. Unsupported harness
parameters are not levels and must not be silently mapped to provider defaults.

## Decision thresholds

The following defaults apply until replaced before the confirmatory freeze by simulation-based
power analysis:

| Endpoint | Improvement SESOI | Equivalence margin | Safety noninferiority margin |
|---|---:|---:|---:|
| Cohen's kappa | 0.10 absolute | ±0.05 | — |
| Portfolio overlap | 0.05 absolute | ±0.03 | — |
| Capital-weighted synchronization | 0.05 absolute | ±0.03 | — |
| Normalized regret | 0.05 lower on a 0–1 scale | ±0.025 | — |
| Hard-constraint or fabrication rate | — | ±0.005 | +0.01 absolute adverse increase |

SESOI establishes practical importance; statistical significance alone does not. A claim of no
material factor effect requires two one-sided tests (TOST) with the full confidence interval inside
the equivalence margin. Failure to reject a difference is inconclusive, not equivalent. A quality
benefit is acceptable only when every preregistered safety endpoint passes noninferiority.

## Inference and multiple testing

Within each independent block, compute the 16 paired contrasts for each bit and average them with
equal scheme-pair weight. The primary test is exact or Monte Carlo paired randomization inference
using block-level sign flips. Report a block-clustered or hierarchical confidence interval and the
block-level effect distribution.

The five MPHIQ main effects form one confirmatory Holm family. The H4 information-versus-profile
contrast is a separately named confirmatory contrast only if frozen in
[Preregistration](preregistration.md). Preregistered two-way interactions form a second
Holm family; all higher-order interactions are exploratory and use Benjamini-Hochberg false
discovery rate control. Endpoint hierarchy is kappa, portfolio overlap, then fingerprint similarity;
secondary endpoints cannot rescue a failed primary claim.

## Required outputs

Each run bundle must contain:

- `mphiq_plan.json`: frozen block, scheme, level, and seed plan.
- `mphiq_assignments.parquet`: one realized factor assignment per agent-step.
- `mphiq_hash_audit.parquet`: resolved hashes proving every one-bit and zero-bit claim.
- `mphiq_balance.json`: marginal and joint level counts and confounding diagnostics.
- `mphiq_block_effects.parquet`: one independent-block effect per endpoint and contrast.
- `mphiq_effects.parquet`: pooled estimates, intervals, raw and adjusted p-values.
- `mphiq_equivalence.json`: TOST and noninferiority decisions against frozen margins.
- `mphiq_verification.json`: quality-gate verdicts and exclusion reconciliation.
- `report.md` and figures for scheme means, main effects, interactions, and block sensitivity.

## Verification gates

A run is not analyzable unless:

- all 32 unique codes exist and match their bits;
- every `1` factor resolves to exactly one allowed hash within its cohort and block;
- every `0` factor resolves to at least two balanced hashes;
- assignments match the frozen plan and no zero factor is perfectly confounded;
- market paths and nonflipped factors match across each Hamming pair;
- information cutoffs pass leakage checks;
- all missing responses, retries, safeguard holds, and exclusions reconcile;
- pair/call/step counts are never reported as independent sample size; and
- inference, margins, and multiplicity families match the frozen analysis plan.

The verification report must identify the exact failing block and must fail closed rather than
silently dropping an incomplete scheme.
