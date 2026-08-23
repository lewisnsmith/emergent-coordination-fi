# flock research program control

small index for independently publishable flock studies

This branch contains no study runner, provider integration, market engine, result, or publication
claim. The complete pre-condensation program remains at
`4016845d86b58b8da2715a60cd621a03dd049626` and in the verified recovery bundles.

The publication base is `main` at `c1fd8cd5c0205dfdf66b587f90477b2014f8aff1`. Every active study
branch starts there and initially contains only `studies/<study-id>/study.yaml` and `protocol.md`.
A study returns to `main` only as a verified namespaced release; unfinished sibling studies are not
required.

[research-program.yaml](research-program.yaml) is the canonical 17-study registry and dependency
graph. [branch-corrections.yaml](branch-corrections.yaml) maps the nine former broad families to the
new refs and records scientific amendments. See [scientific decisions](docs/scientific-decisions.md)
and the [evidence snapshot](docs/evidence-snapshot.md) for claim boundaries and evidence context.

## Verify the index

```bash
uv sync
UV_NO_EDITABLE=1 uv run pytest
uv run ruff check .
uv run pyright
```

These checks validate branch structure and declared study contracts. They do not establish
execution readiness or an empirical result.
