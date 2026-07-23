"""flock command-line interface.

Commands:
    flock data build <builder>   Build a versioned local dataset.
    flock data list              List datasets in the registry.
    flock run <config>           Run one experiment from a YAML config.
    flock sweep <config>         Run a sweep (models x personas x seeds), resumable.
    flock analyze <run-id>       Compute convergence metrics and write a report.
    flock validate               Verify the complete scaffold and execution blockers.
    flock design                 Print/export MPHIQ and prompt-pressure cells.
    flock compile-study          Compile a strict study YAML to a frozen JSON plan.
    flock validate-study         Recompile and validate a frozen study plan.
    flock materialize-study      Export deterministic run assignments/configs.
    flock aggregate-study        Aggregate verified raw runs into crossed inputs.
    flock execute-materialized   Execute a mock-only bundle with a terminal ledger.
"""

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
data_app = typer.Typer(no_args_is_help=True)
app.add_typer(data_app, name="data", help="Build and list versioned local datasets.")


@app.command("doctor")
def doctor_command(
    live: bool = typer.Option(False, "--live", help="Probe model metadata; never generate"),
    root: Path = typer.Option(Path("."), help="Repository root"),
) -> None:
    """Check SDKs, credentials, endpoints, data, pricing, storage, and iCloud state."""
    from flock.experiments.doctor import run_doctor

    report = run_doctor(root, live=live)
    typer.echo(report.model_dump_json(indent=2))
    if not report.ok:
        raise typer.Exit(code=1)


@data_app.command("build")
def data_build(
    builder: str = typer.Argument(
        ..., help="Builder name: synthetic|equities|polymarket|kalshi|refs13f"
    ),
    name: str = typer.Option(None, help="Dataset name (defaults per builder)"),
    seed: int = typer.Option(42, help="Seed for synthetic data"),
    start: str = typer.Option(None, help="Start date YYYY-MM-DD (network builders)"),
    end: str = typer.Option(None, help="End date YYYY-MM-DD (network builders)"),
    symbols: str = typer.Option(None, help="Comma-separated symbols/tickers (network builders)"),
) -> None:
    """Build a dataset and register it in datasets/manifests.json."""
    from flock.data import builders

    entry = builders.build(
        builder,
        name=name,
        seed=seed,
        start=start,
        end=end,
        symbols=symbols.split(",") if symbols else None,
    )
    typer.echo(f"built dataset {entry.name} v{entry.version} ({entry.rows} rows) -> {entry.path}")


@data_app.command("list")
def data_list() -> None:
    """List datasets registered in datasets/manifests.json."""
    from flock.data.registry import Registry

    reg = Registry()
    for e in reg.entries():
        typer.echo(f"{e.name}\tv{e.version}\t{e.rows} rows\t{e.source}\t{e.path}")


@app.command()
def run(
    config: Path = typer.Argument(..., help="Path to experiment YAML config"),
    seed: int = typer.Option(None, help="Override config seed"),
) -> None:
    """Run one experiment; writes decision logs + run manifest under results/."""
    from flock.experiments.runner import run_experiment

    result = run_experiment(config, seed_override=seed)
    typer.echo(f"run complete: {result.run_id} ({result.n_steps} steps, {result.n_agents} agents)")
    typer.echo(f"results -> {result.run_dir}")


@app.command()
def sweep(
    config: Path = typer.Argument(..., help="Path to sweep YAML config"),
    resume: bool = typer.Option(True, help="Skip cells already completed"),
) -> None:
    """Run a sweep across models x personas x seeds. Resumable."""
    from flock.experiments.grid import run_sweep

    summary = run_sweep(config, resume=resume)
    typer.echo(f"sweep complete: {summary.completed} run(s), {summary.skipped} skipped")


@app.command()
def analyze(
    run_id: str = typer.Argument(..., help="Run id (results/<run-id>) or 'latest'"),
    paper: bool = typer.Option(False, "--paper", help="Also regenerate paper figures/tables"),
) -> None:
    """Compute convergence/coordination metrics and write a report."""
    from flock.analysis.report import analyze_run

    report_dir = analyze_run(run_id, paper=paper)
    typer.echo(f"report -> {report_dir}")


@app.command("validate")
def validate_repo(
    root: Path = typer.Option(Path("."), help="Repository root"),
    output: Path = typer.Option(None, help="Optional JSON output path"),
) -> None:
    """Validate configs, frontier policy, profiles, datasets, and protocols."""
    from flock.experiments.verify import verify_repository

    readiness = verify_repository(root)
    rendered = readiness.model_dump_json(indent=2)
    if output is not None:
        output.write_text(rendered + "\n")
        typer.echo(f"verification -> {output}")
    typer.echo(rendered)
    if not readiness.scaffold_ok:
        raise typer.Exit(code=1)


@app.command("design")
def design(
    output: Path = typer.Option(None, help="Optional JSON output path"),
) -> None:
    """Resolve the complete MPHIQ and core prompt-pressure design."""
    import json
    from dataclasses import asdict

    from flock.experiments.design import generate_mphiq_schemes, generate_pressure_cells

    payload = {
        "mphiq": [asdict(scheme) for scheme in generate_mphiq_schemes()],
        "prompt_pressure": [asdict(cell) for cell in generate_pressure_cells()],
    }
    rendered = json.dumps(payload, indent=2)
    if output is not None:
        output.write_text(rendered + "\n")
        typer.echo(f"design -> {output}")
    else:
        typer.echo(rendered)


@app.command("compile-study")
def compile_study_command(
    study: Path = typer.Argument(..., help="Strict study YAML contract"),
    output: Path = typer.Option(..., help="Frozen JSON plan output"),
) -> None:
    """Compile a strict study contract into a deterministic frozen run plan."""
    from flock.experiments.study import compile_study_file, write_study_plan

    plan = compile_study_file(study)
    write_study_plan(plan, output)
    typer.echo(
        f"study plan -> {output} ({plan.exact_runs} runs, {plan.exact_calls} calls, "
        f"hash {plan.plan_hash})"
    )


@app.command("validate-study")
def validate_study_command(
    plan_path: Path = typer.Argument(..., help="Frozen compiled study-plan JSON"),
) -> None:
    """Fail unless a frozen plan exactly matches deterministic recompilation."""
    from flock.experiments.study import load_study_plan

    plan = load_study_plan(plan_path)
    typer.echo(
        f"valid study plan: {plan.study_id} ({plan.exact_runs} runs, "
        f"{plan.exact_calls} calls, hash {plan.plan_hash})"
    )


@app.command("materialize-study")
def materialize_study_command(
    plan_path: Path = typer.Argument(..., help="Frozen compiled study-plan JSON"),
    output: Path = typer.Option(..., help="Materialized assignment-bundle JSON"),
    resolution: Path = typer.Option(
        None, help="Explicit execution-resolution YAML (no defaults are inferred)"
    ),
    root: Path = typer.Option(Path("."), help="Repository root for registries and assets"),
    allow_unresolved: bool = typer.Option(
        False,
        "--allow-unresolved",
        help="Export assignment records even when runner configs cannot be resolved",
    ),
) -> None:
    """Materialize every frozen run cell without executing provider calls."""
    from flock.experiments.materialize import (
        materialize_study_file,
        write_materialized_study,
    )

    materialized = materialize_study_file(
        plan_path,
        resolution,
        root=root,
        require_executable=False,
    )
    write_materialized_study(materialized, output)
    typer.echo(
        f"assignments -> {output} ({materialized.exact_runs} runs, "
        f"{materialized.exact_calls} calls, {materialized.executable_runs} executable, "
        f"hash {materialized.materialization_hash})"
    )
    if materialized.executable_runs != materialized.exact_runs and not allow_unresolved:
        unresolved = materialized.exact_runs - materialized.executable_runs
        typer.echo(
            f"blocked: {unresolved} assignment(s) lack explicit execution mappings; "
            "inspect execution_blockers or use --allow-unresolved for assignments-only export",
            err=True,
        )
        raise typer.Exit(code=1)


@app.command("aggregate-study")
def aggregate_study_command(
    assignments: Path = typer.Argument(..., help="Materialized assignment-bundle JSON"),
    output: Path = typer.Option(..., help="New directory for hashed aggregate inputs"),
    results_root: Path = typer.Option(
        Path("results"), help="Root containing completed raw run directories"
    ),
) -> None:
    """Derive crossed H1/H3/H4 inputs from complete verified raw runs."""
    from flock.experiments.aggregate import aggregate_study

    result = aggregate_study(assignments, output, results_root=results_root)
    typer.echo(
        f"aggregates -> {result.output_dir} ({result.independent_blocks} independent blocks, "
        f"{result.source_runs} verified runs, {result.evidence_kind}, "
        f"hash {result.aggregation_hash})"
    )


@app.command("execute-materialized")
def execute_materialized_command(
    bundle: Path = typer.Argument(..., help="Materialized assignment-bundle JSON"),
    results_root: Path = typer.Option(
        Path("results"), help="Root for mock run directories and the execution ledger"
    ),
    ledger: Path = typer.Option(None, help="Optional explicit execution-ledger path"),
) -> None:
    """Execute an offline mock bundle; real/API configurations are rejected."""
    from flock.experiments.materialized_execution import execute_materialized

    output, execution = execute_materialized(bundle, results_root, ledger)
    summary = execution["summary"]
    typer.echo(
        f"execution ledger -> {output} "
        f"({summary['completed']} completed, {summary['reused']} reused, "
        f"{summary['blocked']} blocked, {summary['failed']} failed)"
    )
    if summary["failed"]:
        raise typer.Exit(code=1)


@app.command("estimate")
def estimate(
    scenario: str = typer.Option("pilot", help="pilot|base|high"),
    matrix: Path = typer.Option(
        Path("configs/budgets/run-matrix.yaml"), help="Staged run-matrix YAML"
    ),
    plan_path: Path = typer.Option(None, "--plan", help="Frozen compiled study-plan JSON"),
    stage: str = typer.Option("pilot", help="canary|pilot|confirmatory"),
) -> None:
    """Print the dated credit envelope for a staged experiment scenario."""
    from flock.experiments.costs import estimate_plan_costs, load_pricing, load_run_matrix
    from flock.experiments.study import load_study_plan

    if plan_path is not None:
        plan_estimate = estimate_plan_costs(load_study_plan(plan_path), stage, load_pricing())
        typer.echo(plan_estimate.model_dump_json(indent=2))
        if not plan_estimate.within_stage_hard_cap:
            raise typer.Exit(code=1)
        return

    plan = load_run_matrix(matrix)
    if scenario not in plan.scenarios:
        raise typer.BadParameter(f"unknown scenario {scenario!r}; choose {sorted(plan.scenarios)}")
    selected = plan.scenarios[scenario]
    typer.echo(selected.model_dump_json(indent=2))


@app.command("verify-run")
def verify_run_command(
    run_dir: Path = typer.Argument(..., help="Completed results/<run-id> directory"),
) -> None:
    """Run deterministic completeness, grounding, fee, cost, and ledger checks."""
    from flock.experiments.verify import verify_run

    result = verify_run(run_dir)
    typer.echo(result.model_dump_json(indent=2))
    if not result.ok:
        raise typer.Exit(code=1)


@app.command("analyze-study")
def analyze_study(
    source_manifest: Path = typer.Argument(..., help="Strict study-source JSON manifest"),
    output: Path = typer.Option(None, help="Output bundle directory"),
    paper: bool = typer.Option(False, "--paper", help="Enforce preregistered real-evidence gates"),
) -> None:
    """Verify complete independent blocks and emit a hash-locked study bundle."""
    from flock.analysis.bundle import analyze_study_bundle

    bundle = analyze_study_bundle(source_manifest, output_dir=output, paper=paper)
    typer.echo(f"verified study bundle -> {bundle}")


@app.command("verify-study")
def verify_study_command(
    bundle: Path = typer.Argument(..., help="Generated study bundle directory"),
    paper: bool = typer.Option(False, "--paper", help="Require all paper-release gates"),
) -> None:
    """Verify study artifact hashes, independent units, and optional paper gates."""
    from flock.analysis.bundle import verify_study_bundle

    result = verify_study_bundle(bundle, require_paper=paper)
    typer.echo(result.model_dump_json(indent=2))
    if not result.ok:
        raise typer.Exit(code=1)


@app.command("reproduce")
def reproduce_command(
    release_manifest: Path = typer.Argument(..., help="Verified release-manifest.json"),
    output: Path = typer.Option(..., help="Empty output directory for clean regeneration"),
) -> None:
    """Regenerate a study bundle and require byte-identical core artifacts."""
    from flock.analysis.bundle import reproduce_study_bundle

    reproduced = reproduce_study_bundle(release_manifest, output)
    typer.echo(f"byte-identical reproduction -> {reproduced}")


@app.command()
def version() -> None:
    """Print flock version."""
    from flock import __version__

    typer.echo(__version__)


if __name__ == "__main__":
    app()
