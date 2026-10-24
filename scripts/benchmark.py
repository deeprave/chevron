#!/usr/bin/env python3

"""Measure equivalent validated Chevron workloads across supported runtimes."""

from argparse import ArgumentParser, ArgumentTypeError, Namespace
from datetime import datetime, timezone
from importlib.util import find_spec
import json
from math import ceil, isfinite
from pathlib import Path
import platform
from statistics import median, stdev
from subprocess import run
import sys
from time import perf_counter

import chevron


_CALIBRATION_ITERATIONS = 10


def make_test(template=None, data=None, expected=None, **options):
    def test():
        result = chevron.render(template, data, **options)
        if result != expected:
            error = "Test failed:\n-- got --\n{}\n-- expected --\n{}"
            raise AssertionError(error.format(result, expected))

    return test


def make_async_test(template=None, data=None, expected=None, **options):
    async def test():
        result = await chevron.async_render(template, data, **options)
        if result != expected:
            error = "Test failed:\n-- got --\n{}\n-- expected --\n{}"
            raise AssertionError(error.format(result, expected))

    return test


def run_sync(test, iterations):
    started = perf_counter()
    for _ in range(iterations):
        test()
    return perf_counter() - started


async def run_async(test, iterations):
    started = perf_counter()
    for _ in range(iterations):
        await test()
    return perf_counter() - started


def calibrate_sync(test, target_milliseconds):
    target_seconds = target_milliseconds / 1_000
    elapsed = run_sync(test, _CALIBRATION_ITERATIONS)
    return max(1, ceil(target_seconds * _CALIBRATION_ITERATIONS / elapsed))


async def calibrate_async(test, target_milliseconds):
    target_seconds = target_milliseconds / 1_000
    elapsed = await run_async(test, _CALIBRATION_ITERATIONS)
    return max(1, ceil(target_seconds * _CALIBRATION_ITERATIONS / elapsed))


def summarise(samples, iterations):
    samples_milliseconds = [sample * 1_000 for sample in samples]
    per_render = [sample / iterations for sample in samples_milliseconds]
    return {
        "iterations": iterations,
        "samples_milliseconds": samples_milliseconds,
        "statistics": {
            "median_milliseconds_per_render": median(per_render),
            "sample_standard_deviation_milliseconds_per_render": stdev(per_render),
        },
    }


def benchmark_sync_workloads(workloads, warmup, samples, target_milliseconds):
    """Warm, calibrate, and time each synchronous workload."""
    results = {}
    for name, workload in workloads.items():
        test = make_test(**workload)
        run_sync(test, warmup)
        iterations = calibrate_sync(test, target_milliseconds)
        timings = [run_sync(test, iterations) for _ in range(samples)]
        results[name] = summarise(timings, iterations)
        print(".", end="", file=sys.stderr, flush=True)
    return results


async def benchmark_async_workloads(workloads, warmup, samples, target_milliseconds):
    """Warm, calibrate, and time each asynchronous workload in one runtime."""
    results = {}
    for name, workload in workloads.items():
        test = make_async_test(**workload)
        await run_async(test, warmup)
        iterations = await calibrate_async(test, target_milliseconds)
        timings = [await run_async(test, iterations) for _ in range(samples)]
        results[name] = summarise(timings, iterations)
        print(".", end="", file=sys.stderr, flush=True)
    return results


def require_backend(backend):
    if find_spec("anyio") is None:
        raise RuntimeError(
            f"The {backend} benchmark requires the optional AnyIO dependency"
        )
    if backend == "trio" and find_spec("trio") is None:
        raise RuntimeError("The Trio benchmark requires the optional Trio dependency")


def benchmark_async_backend(workloads, backend, warmup, samples, target_milliseconds):
    """Run asynchronous workloads through one explicitly selected AnyIO backend."""
    require_backend(backend)
    import anyio

    return anyio.run(
        benchmark_async_workloads,
        workloads,
        warmup,
        samples,
        target_milliseconds,
        backend=backend,
    )


def workloads():
    args = {
        "template": """\
{{# comments }}
<div class=comment>
    <span class=user>{{ user }}</span>
    <span class=body>{{ body }}</span>
    <span class=vote>{{ vote }}</span>
</div>
{{/ comments }}
""",
        "data": {
            "comments": [
                {
                    "user": "tommy",
                    "body": "If this gets to the front page I'll eat my hat!",
                    "vote": 625,
                },
                {"user": "trololol", "body": "this", "vote": -142},
                {
                    "user": "mctom",
                    "body": "I wish thinking of test phrases was easier",
                    "vote": 83,
                },
                {
                    "user": "the_thinker",
                    "body": "Why is /u/trololol's post higher than ours?",
                    "vote": 36,
                },
            ]
        },
        "expected": """\
<div class=comment>
    <span class=user>tommy</span>
    <span class=body>If this gets to the front page I'll eat my hat!</span>
    <span class=vote>625</span>
</div>
<div class=comment>
    <span class=user>trololol</span>
    <span class=body>this</span>
    <span class=vote>-142</span>
</div>
<div class=comment>
    <span class=user>mctom</span>
    <span class=body>I wish thinking of test phrases was easier</span>
    <span class=vote>83</span>
</div>
<div class=comment>
    <span class=user>the_thinker</span>
    <span class=body>Why is /u/trololol's post higher than ours?</span>
    <span class=vote>36</span>
</div>
""",
    }

    def compatibility(text, render):
        return render(text)

    @chevron.func
    def function():
        return "{{name}}"

    @chevron.section
    def section(text):
        return text

    result = {
        "list-section": ("4 mapped comment rows", args),
        "explicit-empty-policy": (
            "4 rows with empty explicit lambdas",
            {**args, "lambdas": {}},
        ),
        "mapped-partial": (
            "Mapped partial",
            {
                "template": "{{>part}}",
                "data": {"name": "world"},
                "partials_dict": {"part": "hello {{name}}"},
                "expected": "hello world",
            },
        ),
    }
    for explicit in (False, True):
        source = "explicit" if explicit else "permissive"
        for name, template, callbacks in (
            (
                "compatibility-section-lambda",
                "{{#call}}{{name}}{{/call}}",
                {"call": compatibility},
            ),
            (
                "function-interpolation-lambda",
                "{{call}}",
                {"call": function},
            ),
            (
                "standard-section-lambda",
                "{{#call}}{{name}}{{/call}}",
                {"call": section},
            ),
            (
                "nested-compatibility-lambda",
                "{{#call}}{{#call}}{{name}}{{/call}}{{/call}}",
                {"call": compatibility},
            ),
        ):
            result[f"{name}-{source}"] = (
                f"{name.replace('-', ' ')} ({source})",
                {
                    "template": template,
                    "data": {"name": "world", **({} if explicit else callbacks)},
                    "lambdas": callbacks if explicit else None,
                    "expected": "world",
                },
            )

    partial_depth = 100
    partials = {
        f"partial-{index}": f"{{{{>partial-{index + 1}}}}}"
        for index in range(partial_depth)
    }
    partials[f"partial-{partial_depth}"] = "complete"
    result["partial-chain"] = (
        f"{partial_depth} nested partials",
        {
            "template": "{{>partial-0}}",
            "partials_dict": partials,
            "expected": "complete",
        },
    )

    lambda_depth = 100
    lambda_callbacks = {}
    for index in range(lambda_depth):

        @chevron.func
        def expansion(index=index):
            return f"{{{{lambda-{index + 1}}}}}"

        lambda_callbacks[f"lambda-{index}"] = expansion

    @chevron.func
    def complete():
        return "complete"

    lambda_callbacks[f"lambda-{lambda_depth}"] = complete
    result["function-lambda-chain"] = (
        f"{lambda_depth} nested function lambdas",
        {
            "template": "{{lambda-0}}",
            "lambdas": lambda_callbacks,
            "expected": "complete",
        },
    )

    partial_count = 200
    result["flat-partials"] = (
        f"{partial_count} flat partial tags",
        {
            "template": "row {{>part}}\n" * partial_count,
            "partials_dict": {"part": "value"},
            "expected": "row value\n" * partial_count,
        },
    )

    item_count = 1_000
    result["large-list-section"] = (
        f"{item_count:,} section rows",
        {
            "template": "{{#items}}{{name}},{{/items}}",
            "data": {"items": [{"name": "item"}] * item_count},
            "expected": "item," * item_count,
        },
    )
    return (
        {name: workload[1] for name, workload in result.items()},
        {name: workload[0] for name, workload in result.items()},
    )


def current_revision():
    try:
        completed = run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            check=False,
            text=True,
        )
        dirty = run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None, None
    if completed.returncode != 0 or dirty.returncode != 0:
        return None, None
    return completed.stdout.strip(), bool(dirty.stdout.strip())


def render_text(result):
    metadata = result["metadata"]
    print("Chevron benchmark")
    print(f"Started: {metadata['started_at']}")
    print(f"Completed: {metadata['completed_at']}")
    print(f"Elapsed: {metadata['elapsed_seconds']:.3f} seconds")
    print(
        "Parameters: "
        f"warm-up={metadata['parameters']['warm']}, "
        f"samples={metadata['parameters']['samples']}, "
        f"target={metadata['parameters']['sample_milliseconds']} milliseconds"
    )
    print("Legend:")
    for name, description in result["legend"].items():
        print(f"  {name}: {description}")
    for backend in ("sync", "asyncio", "trio"):
        workloads_result = result.get(backend)
        if workloads_result is None:
            continue
        print(f"{backend}:")
        for name, measurement in workloads_result.items():
            statistics = measurement["statistics"]
            raw_samples = ", ".join(
                f"{sample:.3f}" for sample in measurement["samples_milliseconds"]
            )
            print(
                f"  {name}: {measurement['iterations']} iterations/sample; "
                f"median {statistics['median_milliseconds_per_render']:.6f}ms/render; "
                f"standard deviation "
                f"{statistics['sample_standard_deviation_milliseconds_per_render']:.6f}; "
                f"samples [{raw_samples}]ms"
            )


def positive_integer(value):
    parsed = int(value)
    if parsed < 2:
        raise ArgumentTypeError("must be at least two")
    return parsed


def nonnegative_integer(value):
    parsed = int(value)
    if parsed < 0:
        raise ArgumentTypeError("must not be negative")
    return parsed


def positive_milliseconds(value):
    parsed = float(value)
    if not isfinite(parsed) or parsed <= 0:
        raise ArgumentTypeError("must be a positive finite number")
    return parsed


def parse_options():
    parser = ArgumentParser(description="Benchmark validated Chevron workloads")
    parser.add_argument("--warm", type=nonnegative_integer, default=3)
    parser.add_argument("--samples", type=positive_integer, default=10)
    parser.add_argument("--sample", type=positive_milliseconds, default=100)
    parser.add_argument("--json", action="store_true", dest="json_output")
    selectors = parser.add_mutually_exclusive_group()
    selectors.add_argument(
        "--sync", action="store_const", const=("sync",), dest="modes"
    )
    selectors.add_argument(
        "--async", action="store_const", const=("asyncio",), dest="modes"
    )
    selectors.add_argument(
        "--trio", action="store_const", const=("trio",), dest="modes"
    )
    selectors.add_argument(
        "--compare",
        action="store_const",
        const=("sync", "asyncio", "trio"),
        dest="modes",
    )
    parser.set_defaults(modes=("sync", "asyncio", "trio"))
    options = parser.parse_args()
    try:
        for backend in options.modes:
            if backend != "sync":
                require_backend(backend)
    except RuntimeError as error:
        parser.error(str(error))
    return options


def main(options: Namespace):
    started = datetime.now(timezone.utc)
    selected_workloads, legend = workloads()
    commit, dirty = current_revision()
    results = {}
    if "sync" in options.modes:
        results["sync"] = benchmark_sync_workloads(
            selected_workloads,
            options.warm,
            options.samples,
            options.sample,
        )
    if "asyncio" in options.modes:
        results["asyncio"] = benchmark_async_backend(
            selected_workloads,
            "asyncio",
            options.warm,
            options.samples,
            options.sample,
        )
    if "trio" in options.modes:
        results["trio"] = benchmark_async_backend(
            selected_workloads,
            "trio",
            options.warm,
            options.samples,
            options.sample,
        )
    completed = datetime.now(timezone.utc)
    result = {
        "metadata": {
            "commit": commit,
            "dirty": dirty,
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "parameters": {
                "warm": options.warm,
                "samples": options.samples,
                "sample_milliseconds": options.sample,
            },
            "started_at": started.isoformat(),
            "completed_at": completed.isoformat(),
            "elapsed_seconds": (completed - started).total_seconds(),
        },
        "legend": legend,
        **results,
    }
    print(file=sys.stderr)
    if options.json_output:
        print(json.dumps(result, indent=2))
    else:
        render_text(result)


if __name__ == "__main__":
    main(parse_options())
