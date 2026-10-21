#!/usr/bin/env python3

import asyncio
from argparse import ArgumentParser
from time import perf_counter
from timeit import repeat

import chevron


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


async def repeat_async(test, number, repeat_count=5):
    """Time repeated awaited calls inside one event loop."""
    timings = []
    for _ in range(repeat_count):
        started = perf_counter()
        for _ in range(number):
            await test()
        timings.append(perf_counter() - started)
    return timings


async def benchmark_async_workloads(workloads, times):
    """Benchmark every async workload within one event loop."""
    for name, workload in workloads.items():
        timings = await repeat_async(make_async_test(**workload), times)
        print(f"async {name}: {', '.join(f'{value:.6f}' for value in timings)} seconds")


def main(times, mode):
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

    def callback(text, render):
        return render(text)

    @chevron.func
    def function():
        return "{{name}}"

    @chevron.section
    def section(text):
        return text

    workloads = {
        "ordinary": args,
        "explicit-empty": {**args, "lambdas": {}},
        "partial": {
            "template": "{{>part}}",
            "data": {"name": "world"},
            "partials_dict": {"part": "hello {{name}}"},
            "expected": "hello world",
        },
    }
    for explicit in (False, True):
        for name, template, callbacks in (
            ("compat", "{{#call}}{{name}}{{/call}}", {"call": callback}),
            ("function", "{{call}}", {"call": function}),
            ("section", "{{#call}}{{name}}{{/call}}", {"call": section}),
            (
                "nested-callback",
                "{{#call}}{{#call}}{{name}}{{/call}}{{/call}}",
                {"call": callback},
            ),
        ):
            workloads[f"{name}-{'explicit' if explicit else 'permissive'}"] = {
                "template": template,
                "data": {"name": "world", **({} if explicit else callbacks)},
                "lambdas": callbacks if explicit else None,
                "expected": "world",
            }

    if mode in {"sync", "compare"}:
        benchmark_sync_workloads(workloads, times)
    if mode in {"async", "compare"}:
        asyncio.run(benchmark_async_workloads(workloads, times))


def benchmark_sync_workloads(workloads, times):
    """Benchmark synchronous workloads after validating every output."""
    for name, workload in workloads.items():
        timings = repeat(make_test(**workload), number=times, repeat=5)
        print(f"sync {name}: {', '.join(f'{value:.6f}' for value in timings)} seconds")


if __name__ == "__main__":
    parser = ArgumentParser(description="Benchmark validated Chevron workloads")
    parser.add_argument("times", nargs="?", type=int, default=10000)
    parser.add_argument(
        "--mode", choices=("sync", "async", "compare"), default="compare"
    )
    options = parser.parse_args()
    main(options.times, options.mode)
