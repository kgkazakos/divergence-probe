"""
CLI entry point for divergence-probe.

Commands:
    dp scan   — analyse a single transcript file
    dp batch  — analyse a directory of transcripts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import detect_gaps_from_file
from .models import DivergenceReport, GapType, Severity

console = Console()

_SEVERITY_COLOR = {
    Severity.HIGH: "bold red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "dim",
}

_GAP_ICON = {
    GapType.CONTRADICTION: "⚡",
    GapType.PARTIAL: "⚠ ",
    GapType.UNCERTAIN: "?  ",
}


def _report_to_dict(report: DivergenceReport) -> dict:
    return {
        "source_file": report.source_file,
        "total_sentences": report.total_sentences,
        "say_count": report.say_count,
        "do_count": report.do_count,
        "gap_count": len(report.gaps),
        "contradiction_count": report.contradiction_count,
        "partial_count": report.partial_count,
        "high_severity_count": report.high_severity_count,
        "gap_rate": round(report.gap_rate, 3),
        "gaps": [
            {
                "gap_type": g.gap_type.value,
                "severity": g.severity.value,
                "confidence": round(g.confidence, 3),
                "topic_overlap_score": round(g.topic_overlap_score, 3),
                "llm_enriched": g.llm_enriched,
                "say": {
                    "text": g.say_statement.text,
                    "speaker": g.say_statement.speaker,
                    "line_no": g.say_statement.line_no,
                    "polarity": g.say_statement.polarity,
                },
                "do": {
                    "text": g.do_statement.text,
                    "speaker": g.do_statement.speaker,
                    "line_no": g.do_statement.line_no,
                    "polarity": g.do_statement.polarity,
                },
                "explanation": g.explanation,
                "suggested_probe": g.suggested_probe,
            }
            for g in report.gaps
        ],
    }


def _render_rich(report: DivergenceReport) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]divergence-probe[/bold]  ·  {report.source_file}",
            subtitle=(
                f"{report.total_sentences} sentences  ·  "
                f"{report.say_count} habitual claims  ·  {report.do_count} episodic reports"
            ),
            style="blue",
            expand=False,
        )
    )

    if not report.gaps:
        console.print("[green]✓  No significant divergences detected.[/green]\n")
        return

    console.print(
        f"\n[bold]Summary[/bold]  "
        f"[bold white]{len(report.gaps)}[/bold white] divergences  ·  "
        f"[bold red]{report.contradiction_count}[/bold red] contradictions  ·  "
        f"[yellow]{report.partial_count}[/yellow] partial  ·  "
        f"[bold red]{report.high_severity_count}[/bold red] high severity\n"
    )

    for i, gap in enumerate(report.gaps, 1):
        sev_style = _SEVERITY_COLOR[gap.severity]
        icon = _GAP_ICON.get(gap.gap_type, "·  ")
        enriched_badge = "[dim green] ✦LLM[/dim green]" if gap.llm_enriched else ""

        console.print(
            f"[bold]{i}. {icon}[/bold]"
            f"[bold]{gap.gap_type.value.upper()}[/bold]  "
            f"[{sev_style}]{gap.severity.value.upper()}[/{sev_style}]  "
            f"confidence=[cyan]{gap.confidence:.2f}[/cyan]  "
            f"overlap=[cyan]{gap.topic_overlap_score:.2f}[/cyan]"
            f"{enriched_badge}"
        )

        if gap.say_statement.speaker:
            console.print(f"   [dim]Speaker: {gap.say_statement.speaker}[/dim]")

        console.print(
            f"   [blue]CLAIM[/blue] [dim](line {gap.say_statement.line_no})[/dim]: "
            f"{gap.say_statement.text}"
        )
        console.print(
            f"   [orange3]REPORT[/orange3] [dim](line {gap.do_statement.line_no})[/dim]: "
            f"{gap.do_statement.text}"
        )
        console.print(f"   [dim]{gap.explanation}[/dim]")

        if gap.suggested_probe:
            console.print(
                f"   [italic green]↳ Probe: {gap.suggested_probe}[/italic green]"
            )
        console.print()


@click.group()
@click.version_option(package_name="divergence-probe")
def cli() -> None:
    """divergence-probe — Habitual-claim vs episodic-report divergence detection.

    No graph database required. Runs fully rule-based offline.
    Add --llm-backend to enrich results with GPT-4o-mini, Claude, or Gemini.
    """


@cli.command()
@click.argument("transcript", type=click.Path(exists=True, path_type=Path))
@click.option("--min-overlap", default=0.05, show_default=True,
              help="Minimum Jaccard keyword overlap to pair statements (0–1).")
@click.option("--min-confidence", default=0.30, show_default=True,
              help="Minimum confidence to include a divergence (0–1).")
@click.option("--max-window", default=60, show_default=True,
              help="Max sentence distance between a claim and report pair.")
@click.option("--llm-backend", type=click.Choice(["openai", "anthropic", "gemini"]),
              default=None, help="Optional LLM backend for enrichment.")
@click.option("--top-n", default=5, show_default=True,
              help="Number of top divergences to send to the LLM.")
@click.option("--json-output", is_flag=True, help="Emit results as JSON.")
def scan(
    transcript: Path,
    min_overlap: float,
    min_confidence: float,
    max_window: int,
    llm_backend: Optional[str],
    top_n: int,
    json_output: bool,
) -> None:
    """Detect divergences in a single TRANSCRIPT file."""
    report = detect_gaps_from_file(
        transcript,
        min_overlap=min_overlap,
        min_confidence=min_confidence,
        max_window=max_window,
    )

    if llm_backend:
        from .llm import enrich_report
        report = enrich_report(report, backend=llm_backend, top_n=top_n)

    if json_output:
        click.echo(json.dumps(_report_to_dict(report), indent=2))
    else:
        _render_rich(report)


@cli.command()
@click.argument("directory",
                type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--pattern", default="*.txt", show_default=True,
              help="Glob pattern for transcript files.")
@click.option("--min-overlap", default=0.05, show_default=True)
@click.option("--min-confidence", default=0.30, show_default=True)
@click.option("--max-window", default=60, show_default=True)
@click.option("--json-output", is_flag=True)
def batch(
    directory: Path,
    pattern: str,
    min_overlap: float,
    min_confidence: float,
    max_window: int,
    json_output: bool,
) -> None:
    """Detect divergences across a DIRECTORY of transcript files."""
    files = sorted(directory.glob(pattern))
    if not files:
        console.print(
            f"[red]No files matching '{pattern}' found in {directory}[/red]"
        )
        sys.exit(1)

    reports = []
    for f in files:
        report = detect_gaps_from_file(
            f,
            min_overlap=min_overlap,
            min_confidence=min_confidence,
            max_window=max_window,
        )
        reports.append(report)
        if not json_output:
            _render_rich(report)

    if json_output:
        payload = {
            "total_files": len(reports),
            "total_gaps": sum(len(r.gaps) for r in reports),
            "total_contradictions": sum(r.contradiction_count for r in reports),
            "total_high_severity": sum(r.high_severity_count for r in reports),
            "reports": [_report_to_dict(r) for r in reports],
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        table = Table(title="Batch Summary", box=box.SIMPLE_HEAD)
        table.add_column("File", style="dim")
        table.add_column("Divergences", justify="right")
        table.add_column("Contradictions", justify="right", style="red")
        table.add_column("Partial", justify="right", style="yellow")
        table.add_column("High Sev.", justify="right")

        for r in reports:
            table.add_row(
                r.source_file,
                str(len(r.gaps)),
                str(r.contradiction_count),
                str(r.partial_count),
                str(r.high_severity_count),
            )
        console.print(table)


def main() -> None:
    cli()
