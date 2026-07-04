"""flock command-line interface.

Commands:
    flock data build <builder>   Build a versioned local dataset.
    flock data list              List datasets in the registry.
    flock run <config>           Run one experiment from a YAML config.
    flock sweep <config>         Run a sweep (models x personas x seeds), resumable.
    flock analyze <run-id>       Compute convergence metrics and write a report.
"""

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
data_app = typer.Typer(no_args_is_help=True)
app.add_typer(data_app, name="data", help="Build and list versioned local datasets.")


@data_app.command("build")
def data_build(
    builder: str = typer.Argument(..., help="Builder name: synthetic|equities|polymarket|kalshi|refs13f"),
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


@app.command()
def version() -> None:
    """Print flock version."""
    from flock import __version__

    typer.echo(__version__)


if __name__ == "__main__":
    app()
