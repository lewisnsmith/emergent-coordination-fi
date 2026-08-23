# flock research program control

This branch is the small cross-study index for planned flock research. It contains no study runner,
provider integration, market engine, result, or publication claim. Historical implementations and
the former broad manuals remain reachable from commit
`4016845d86b58b8da2715a60cd621a03dd049626` and the verified recovery bundle.

The publication base is local `main` at
`3002008b291dcd736b90237cccd1e5fd9f4ba0e4`. Each study family starts at that exact commit and owns
its hypotheses, experiments, protocol, dependencies, cost status, approval gates, blockers, and
outputs. A family returns to `main` only after its result and scoped release verify.

## Study families

| Branch | Scope |
| --- | --- |
| `feat/h8-exp017-causal-convergence` | H8 causal activation intervention and synthetic downstream effect |
| `feat/h1-h3-h4-h12-replay-convergence` | replay, model lineage, profiles, information, harness, and prompt robustness |
| `feat/h2-h2b-h6-investor-delegation` | matched investors, delegation breadth, human trust, and advisor execution |
| `feat/h2b-h5-shared-exchange` | shared-exchange calibration, capital share, liquidity, and cascades |
| `feat/h7-adoption-forecast` | conditional adoption and threshold forecasts |
| `feat/h8-h12-pressure-attribution` | black-box input attribution and prompt-pressure factorials |
| `feat/h9-h10-h11-market-signatures` | signature discovery, transport, detection, attribution, and dataset tiers |
| `feat/h8-h13-local-fidelity-quantization` | local behavioral fidelity and quantization error propagation |
| `feat/alpha-oos-evaluation` | separately judged historical out-of-sample signal evaluation |

See [research-program.yaml](research-program.yaml),
[scientific decisions](docs/scientific-decisions.md), and the
[evidence snapshot](docs/evidence-snapshot.md).

## Verify the index

```bash
uv sync
UV_NO_EDITABLE=1 uv run pytest
uv run ruff check .
uv run pyright
```

These checks validate the index only. They do not establish study readiness.
