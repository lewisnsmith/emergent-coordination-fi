# Reproducibility

This document defines the small contract shared by flock studies. A study can add stricter rules
inside its own directory, but it must not weaken these rules.

## Environment

Use Python 3.12 and the checked-in `uv.lock`:

```bash
UV_NO_EDITABLE=1 uv sync --frozen
UV_NO_EDITABLE=1 uv run pytest
uv run ruff check .
uv run pyright
```

Study-specific dependencies belong in a named optional dependency group on that study's branch.
Normal analysis and verification must not require provider credentials or network access.

## Study source

Each study lives under `studies/<study-id>/` and carries:

- `study.yaml` for its hypotheses, experiment IDs, source lineage, dependencies, rights, costs,
  approvals, blockers, runner and verifier status, and expected outputs;
- `protocol.md` for its question, estimands, independent units, controls, exclusions, limits, and
  execution order;
- only the references cited by that study; and
- a report only after the evidence needed to build it exists.

Plans are not results. Mock and fake-model runs validate software paths only.

## Artifacts

Published files use canonical relative paths and SHA-256 checksums. Manifests are serialized with
sorted keys and no non-finite JSON values. Writers replace completed files atomically. Verification
fails on missing files, duplicate paths, traversal, or checksum drift.

Raw model activations, restricted source data, provider responses, caches, and incomplete attempts
remain outside the public Git tree. A release records their permitted metadata and hashes where the
underlying bytes are available; it never invents a hash for an unavailable placeholder.

## Clean reproduction

A study is ready to merge only when a clean checkout can install from the lockfile, run its focused
tests, verify its release checksums, and reproduce its declared core artifacts. The release records
the source commit and every input needed to interpret the result. Null and negative outcomes use
the same contract as positive outcomes.
