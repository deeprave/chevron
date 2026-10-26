"""Chevron-owned public behavior cases for delimiter state and whitespace."""

from rendering_cases import RenderCase


WHITESPACE_CASES = (
    RenderCase(
        name="initial custom delimiters render interpolation",
        template="<<name>>",
        data={"name": "Ada"},
        expected="Ada",
        initial_delimiters=("<<", ">>"),
    ),
    RenderCase(
        name="initial custom delimiters render partial expansion",
        template="<<>part>>",
        data={"name": "Ada"},
        partials={"part": "<<name>>"},
        expected="Ada",
        initial_delimiters=("<<", ">>"),
    ),
    RenderCase(
        name="partial resets to render default delimiters after a change",
        template="{{=| |=}}|#items||>part||/items|",
        data={"items": [{"value": "rendered"}]},
        partials={"part": "{{value}}"},
        expected="rendered",
    ),
    RenderCase(
        name="skipped section propagates delimiter changes",
        template="{{#off}}{{=| |=}}|value||/off||value|",
        data={"off": False, "value": "skipped"},
        expected="skipped",
    ),
    RenderCase(
        name="iterated section propagates delimiter changes",
        template="{{#items}}{{=| |=}}|value||/items||value|",
        data={"items": [{"value": "item"}], "value": "outer"},
        expected="itemouter",
    ),
)
