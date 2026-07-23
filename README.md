# flock

**Which shared components make LLM trading agents converge, relative to matched classical
strategies?**

flock is an experiment zone for measuring *common-response convergence* and *outcome
homogenization* in LLM trading agents. The proposed study uses a matched
`technology (LLM/classical) × ecology (homogeneous/heterogeneous)` design and asks how model
lineage, profiles, harnesses, information, and wording affect convergence. It does not infer
coordination or collusion from agents independently responding to the same information.

See [`docs/research/`](docs/research/) and the machine-readable
[`configs/research-program.yaml`](configs/research-program.yaml) for the full H1–H12 program:

- [01 – Research question](docs/research/01-research-question.md)
- [02 – Experimental design](docs/research/02-experimental-design.md)
- [03 – Metrics](docs/research/03-metrics.md)
- [04 – Datasets](docs/research/04-datasets.md)
- [05 – Follow-up questions](docs/research/05-follow-up-questions.md)
- [06 – Pre-registration](docs/research/06-preregistration.md)
- [07 – Related work](docs/research/07-related-work.md)
- [09–12 – MPHIQ, profiles, prompt pressure, and statistics](docs/research/09-mphiq-factorial-design.md)
- [13–17 – safeguards, markets/trust, interpretability, attribution, outputs](docs/research/13-grounding-and-logical-verification.md)
- [18 – cost and execution runbook](docs/research/18-cost-and-execution-runbook.md)
- [19–23 – authorship, research log, mistake case study, review, and release](docs/research/19-authorship-and-tool-use.md)
- [24 – H5 ODD/STRESS report and simulator gate](docs/research/24-simulator-odd-stress.md)

The proposed first study is H1/H3/H4. H2 is a conditional descriptive external anchor, and H5 is
a separate causal experiment whose claims are bounded to the validated simulator. H6–H12 are
future work, not claims of the proposed study. The working manuscript is
[`paper/main.tex`](paper/main.tex); it is a skeleton with no confirmatory results.

## Current readiness

The software scaffold passes its offline test, lint, type, study-compilation, and fresh synthetic
mock-smoke gates. Local ignored history also contains mock shared-exchange diagnostics. These runs
validate code paths only: no paid frontier-model pilot or confirmatory study has run, the
preregistration is not frozen or registered, and no paper-level empirical result exists.

The proposed study is **not execution-ready**. It still requires real datasets and nonoverlapping
windows, immutable model releases, matched cohort weights and activity, final prompts,
power-derived top-level sample sizes, deterministic raw-run aggregation, and a frozen
preregistration.

Run the preflight rather than inferring readiness from config files:

```bash
uv run flock validate
uv run flock doctor
uv run flock compile-study configs/studies/paper-core.yaml --output results/paper-core/plan.json
uv run flock validate-study results/paper-core/plan.json
uv run flock materialize-study results/paper-core/plan.json \
  --output results/paper-core/assignments.json --allow-unresolved
uv run flock estimate --plan results/paper-core/plan.json --stage canary
```

`scaffold_ok=true` means only that repository contracts are internally consistent.
`execution_ready=false` lists missing real datasets, approvals, exposure evidence, or runners and
therefore blocks confirmatory execution.

## Quickstart (no API keys required)

The pipeline runs offline with deterministic mock models:

```bash
uv sync
uv run flock data build synthetic          # seeded synthetic equities
uv run flock run configs/experiments/exp-000-smoke.yaml
uv run flock verify-run results/<run-id>
uv run flock analyze latest                # convergence report with bootstrap CIs
```

Do not start a real-model run until `flock doctor --live` passes for the exact endpoints,
`flock validate` has no first-paper blocker, the compiled high envelope is below the authorized
stage cap, and the preregistration is frozen. Frontier configs carry request, token, and dollar
limits; a call reserves its conservative envelope before reaching a provider. Real-model runs
need provider keys and the extras:

```bash
uv sync --extra providers --extra data
uv run flock data build equities --symbols AAPL,MSFT,NVDA --start 2023-01-01 --end 2024-12-31
# replace the placeholder block/window IDs only with frozen compiled assignments
uv run flock run configs/experiments/exp-001-replay-equities.yaml
```

## How it works

```
First paper (Replay):                  Separate H5 (Shared exchange):
  data ──▶ Agent A ──▶ trades_A          Agent A ─┐
  data ──▶ Agent B ──▶ trades_B          Agent B ─┼─▶ [order book] ─▶ price impact
  data ──▶ Agent C ──▶ trades_C          Agent C ─┘        ▲              │
  (no interaction; estimates                              └── feedback ──┘
   common-response convergence)        (tests market effects inside the
                                        validated simulator only)
```

The first-paper benchmark crosses technology with ecology: homogeneous LLM, heterogeneous LLM,
homogeneous classical, and heterogeneous classical cohorts. Cohorts are matched on family count
and weights, activity, capital, information, and trading constraints. Family-weighted estimands
prevent a provider or strategy family with more sampled endpoints from dominating the contrast.
H2 real-investor panels are reported only if universe, cadence, activity, capital weighting, and
sampling can be harmonized; otherwise they remain separate descriptive context.

## Repo map

| Path | What |
|---|---|
| `src/flock/agents/` | Agent protocol, LLM harness, provider adapters, baseline strategies |
| `src/flock/markets/` | Replay engine (Phase 1), shared exchange / matching engine (Phase 2) |
| `src/flock/data/` | Dataset builders, schemas, versioned registry |
| `src/flock/experiments/` | Run orchestration, sweeps, portfolio ledger |
| `src/flock/analysis/` | Convergence and simulator-bounded market metrics, statistics, reports |
| `src/flock/interpretability/` | API input interventions and local activation-patching contracts |
| `configs/research-program.yaml` | All hypotheses, experiments, dependencies, outputs, verification |
| `configs/designs/`, `prompts/`, `personas/` | MPHIQ, pressure, wording, and profile treatments |
| `configs/budgets/` | Dated official prices and staged call/credit assumptions |
| `docs/research/` | Research question, design, metrics, pre-registration |
| `paper/` | Claim-locked LaTeX manuscript and bibliography; no single-run paper export |

## Reproducibility

Every run writes a manifest (resolved config/persona/model hash, git SHA, dataset hash, seeds)
under `results/<run-id>/`. LLM responses are cached content-addressed in `.flock-cache/` so
published results can be re-derived offline. Decision logs include full observation, prompt and
raw-response hashes, evidence references, grounding verdicts, token usage, and cost.

Paper-level inference requires multiple top-level units: independently generated synthetic
trajectories or nonoverlapping historical windows. Overlapping windows and units exposed to a
common shock share a dependence cluster. Seeds, agents, agent pairs, calls, steps, symbols, and
prompt variants are nested observations, not additional independent evidence. A single run is a
pipeline artifact, never a paper result.

Study-level release commands fail closed on incomplete or unverified runs, duplicate trajectories,
mock evidence declared as real, changed inputs, and missing immutable preregistration evidence:

```bash
uv run flock analyze-study results/study-source.json --output results/paper-core/bundle
uv run flock verify-study results/paper-core/bundle
# --paper additionally requires real evidence and the frozen preregistration reference
uv run flock verify-study results/paper-core/bundle --paper
uv run flock reproduce results/paper-core/bundle/release-manifest.json \
  --output results/paper-core/clean-reproduction
```

The bundle contains independent-unit and block-effect tables, missingness/failure and sensitivity
tables, frozen estimand and equivalence/noninferiority records, one crossed H1/H3/H4 multiplicity
family, claim links, an experimental-topology figure, and a block-level forest plot. Every crossed
aggregate row must cite verified treatment runs with the same block lineage, and every contributing
run is hash-locked without increasing independent `n`. Reproduction regenerates into an empty
directory and requires byte-identical core artifacts. A deterministic raw-decision-to-crossed-input
compiler remains a paper blocker; externally assembled aggregate tables are never accepted without
complete run provenance.

## Publication gates

Before submission, the study must pass the
[ODD protocol](https://doi.org/10.18564/jasss.4259) for model description and the
[STRESS guidelines](https://doi.org/10.1080/17477778.2018.1442155) for simulation reporting. The
paper and release package must also satisfy the
[NeurIPS paper checklist](https://neurips.cc/public/guides/PaperChecklist), the
[AEA Data and Code Availability Policy](https://www.aeaweb.org/journals/data/data-code-policy),
and the current [ACM artifact review and badging criteria](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
These are release gates: claims remain draft until the model description, experiment report,
provenance, master reproduction path, artifact inventory, and independent rerun evidence are
present and audited.

## Development

```bash
uv run pytest && uv run ruff check . && uv run pyright
```

In iCloud-synced folders (for example, `~/Documents`), export `UV_NO_EDITABLE=1` before running
uv. iCloud can hide editable-install `.pth` files, causing intermittent `ModuleNotFoundError`
failures; `.claude/settings.json` sets this automatically for Claude Code sessions.
