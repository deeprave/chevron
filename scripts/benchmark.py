#!/usr/bin/env python3

from sys import argv
from timeit import repeat

import chevron


def make_test(template=None, data=None, expected=None, **options):
    def test():
        result = chevron.render(template, data, **options)
        if result != expected:
            error = "Test failed:\n-- got --\n{}\n-- expected --\n{}"
            raise AssertionError(error.format(result, expected))

    return test


def main(times):
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

    for name, workload in workloads.items():
        timings = repeat(make_test(**workload), number=times, repeat=5)
        print(f"{name}: {', '.join(f'{value:.6f}' for value in timings)} seconds")


if __name__ == "__main__":
    try:
        main(int(argv[1]))
    except IndexError:
        main(10000)
