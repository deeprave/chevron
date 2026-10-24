#!/usr/bin/env python3

"""Render a Chevron benchmark JSON report as readable Mermaid bar charts."""

from argparse import ArgumentParser, Namespace
from decimal import Decimal, ROUND_DOWN
import json
from pathlib import Path


BACKENDS = ("sync", "asyncio", "trio")
PLOT_COLOURS = "#4c78a8, #f58518, #54a24b"


def quoted(value):
    return json.dumps(value)


def values(values):
    return "[" + ", ".join(f"{value:.12g}" for value in values) + "]"


def categories(values):
    return "[" + ", ".join(quoted(value) for value in values) + "]"


def milliseconds(value):
    rounded_down = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
    return f"{rounded_down:.4f}"


def medians(report):
    backends = [backend for backend in BACKENDS if backend in report]
    if not backends:
        raise ValueError("the benchmark report contains no recognised runtime results")

    workloads = list(report[backends[0]])
    if not workloads:
        raise ValueError("the benchmark report contains no workloads")

    results = {}
    for backend in backends:
        measurements = report[backend]
        if list(measurements) != workloads:
            raise ValueError(f"{backend} workloads do not match the other runtimes")
        results[backend] = [
            float(
                measurements[workload]["statistics"]["median_milliseconds_per_render"]
            )
            for workload in workloads
        ]
    return workloads, results


def chart_header(title):
    return [
        "---",
        "config:",
        "  themeVariables:",
        "    xyChart:",
        f"      plotColorPalette: {quoted(PLOT_COLOURS)}",
        "---",
        "xychart-beta",
        f"  title {quoted(title)}",
    ]


def render_bar_chart(title, modes, values_for_modes, upper_bound):
    lines = chart_header(title) + [
        f"  x-axis {quoted('Rendering mode')} {categories(modes)}",
        f"  y-axis {quoted('Median milliseconds per render')} 0 --> {upper_bound:.12g}",
    ]
    lines.extend(
        f"  bar {quoted(mode)} "
        f"{values([value if index == position else 0 for index in range(len(modes))])}"
        for position, (mode, value) in enumerate(zip(modes, values_for_modes))
    )
    return "\n".join(lines) + "\n"


def render_table(workloads, results):
    modes = list(results)
    lines = [
        "| Classification | " + " | ".join(f"{mode} (ms)" for mode in modes) + " |",
        "| --- | " + " | ".join("---:" for _ in modes) + " |",
    ]
    lines.extend(
        "| "
        + workload
        + " | "
        + " | ".join(milliseconds(results[mode][index]) for mode in modes)
        + " |"
        for index, workload in enumerate(workloads)
    )
    return "\n".join(lines)


def render_document(title, workloads, results):
    upper_bound = max(max(series) for series in results.values()) * 1.1
    charts = []
    modes = list(results)
    for index, workload in enumerate(workloads):
        chart_title = f"{title}: {workload}"
        values_for_modes = [results[mode][index] for mode in modes]
        chart = render_bar_chart(chart_title, modes, values_for_modes, upper_bound)
        charts.append(f"## {workload}\n\n```mermaid\n{chart}```")
    return (
        f"# {title}\n\n{render_table(workloads, results)}\n\n"
        + "\n\n".join(charts)
        + "\n"
    )


def parse_options():
    parser = ArgumentParser(
        description="Translate Chevron benchmark median values into a Markdown benchmark report"
    )
    parser.add_argument("report", type=Path, help="benchmark JSON report")
    parser.add_argument("--title", help="chart title (defaults to the report filename)")
    parser.add_argument("--output", type=Path, help="write the report to this file")
    return parser.parse_args()


def main(options: Namespace):
    report = json.loads(options.report.read_text())
    workloads, results = medians(report)
    title = options.title or f"Chevron benchmark medians: {options.report.stem}"
    chart = render_document(title, workloads, results)
    if options.output is None:
        print(chart, end="")
    else:
        options.output.write_text(chart)


if __name__ == "__main__":
    main(parse_options())
