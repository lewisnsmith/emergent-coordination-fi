# flock agent guide

Read `CLAUDE.md` before changing or operating the project; it remains the repository guide.

Use `$run-flock-experiment` for experiment status, planning, preparation, execution, recovery,
verification, analysis, preregistration, or release requests. The skill owns the prompt-facing
workflow and points to the canonical scientific manuals instead of copying them.

Never treat `scaffold_ok` as execution readiness. Provider-backed execution is blocked until the
repository has a tested authorization-bound materialized executor, persistent cumulative spend
ledger, and provider-drift provenance. A general run request never authorizes spending, provider
calls, purchases, participant contact, paper orders, registration, publication, or remote writes.

Keep secrets out of prompts, files, logs, manifests, and git; report credential presence only.
Preserve incomplete attempts and unrelated work. Manifests and hashes outrank chat memory.

Before claiming an implementation change complete, run `uv run pytest`, `uv run ruff check .`, and
`uv run pyright`, plus the phase-specific verifier.
