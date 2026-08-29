# emergent-coordination

shared foundations for reproducible, branch-isolated studies

`main` contains only code and documentation shared by completed research releases. It currently
has no study runner and makes no empirical claim. The first active publication branch is
`feat/h8-exp017-causal-convergence`.

## What belongs here

- deterministic serialization, hashing, atomic writes, and checksum verification;
- concise reproduction and AI-use documentation;
- release metadata shared by published studies; and
- additive study directories after their results pass verification.

Experiment-specific prompts, models, data contracts, analyses, costs, and reports live on their
own branches until the corresponding study is complete. The full research program remains
recoverable from `refactor/research-program-control`.

## Study layout

Each study branch owns a self-contained directory:

```text
studies/<study-id>/
├── study.yaml
├── protocol.md
├── references.bib
└── report.md
```

Generated reports and release artifacts are added only after they can be reproduced and verified.
Empty result files and speculative manuscript templates are not kept on `main`.

## Development

```bash
UV_NO_EDITABLE=1 uv sync
UV_NO_EDITABLE=1 uv run pytest
uv run ruff check .
uv run pyright
```

See [reproducibility](docs/reproducibility.md) for the shared artifact contract and
[AI use](docs/ai-use.md) for the disclosure boundary.
