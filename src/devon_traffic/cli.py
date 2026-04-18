"""Click-based CLI for devon-traffic."""

from __future__ import annotations

import json
from pathlib import Path

import click

from . import __version__
from .data import SynthConfig, get_bundle


@click.group(help="Devon traffic dashboard — synthetic GPS/OD analytics.")
@click.version_option(__version__, prog_name="devon-traffic")
def cli():
    pass


@cli.command(help="Run the FastHTML dashboard server.")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=5001, show_default=True, type=int)
def serve(host: str, port: int):
    import uvicorn
    from .app import app
    click.echo(f"Starting Devon Traffic dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


@cli.command("generate-data", help="Generate synthetic datasets and cache to disk as parquet.")
@click.option("--out", default="data", type=click.Path(file_okay=False, path_type=Path))
@click.option("--seed", default=42, show_default=True, type=int)
@click.option("--days", default=14, show_default=True, type=int)
def generate_data(out: Path, seed: int, days: int):
    out.mkdir(parents=True, exist_ok=True)
    cfg = SynthConfig(seed=seed, days=days)
    bundle = get_bundle(cfg)
    for name, df in bundle.items():
        path = out / f"{name}.parquet"
        df.to_parquet(path, index=False)
        click.echo(f"  {name:10s} -> {path}  ({len(df):,} rows)")
    click.echo(click.style("Done.", fg="green"))


@cli.command("export", help="Export a specific table as CSV.")
@click.argument("table", type=click.Choice(["zones", "od", "journey", "speed", "gps"]))
@click.option("--out", "-o", default="-", help="Output path or '-' for stdout.")
def export(table: str, out: str):
    bundle = get_bundle()
    df = bundle[table]
    if out == "-":
        click.echo(df.to_csv(index=False))
    else:
        Path(out).write_text(df.to_csv(index=False))
        click.echo(f"Wrote {len(df):,} rows to {out}")


@cli.command("summary", help="Print a compact JSON summary of the synthetic data.")
def summary():
    b = get_bundle()
    out = {
        "zones": len(b["zones"]),
        "regions": sorted(b["zones"].region.unique().tolist()),
        "od_pairs": len(b["od"]),
        "total_trips_per_day": int(b["od"].trips_per_day.sum()),
        "speed_rows": len(b["speed"]),
        "journey_observations": len(b["journey"]),
        "gps_pings": len(b["gps"]),
        "mean_network_speed_mph": round(float(b["speed"].mean_speed_mph.mean()), 2),
        "median_journey_time_min": round(float(b["journey"].journey_time_min.median()), 2),
    }
    click.echo(json.dumps(out, indent=2))


def main():
    cli()


if __name__ == "__main__":
    main()
