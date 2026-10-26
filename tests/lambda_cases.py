"""Chevron-owned public behavior cases for declared lambda rendering."""

from typing import Any
from collections import ChainMap
from types import MappingProxyType

import chevron
from rendering_cases import LambdaMapping, LambdaRenderCase


class _SyncLambdaFactories:
    @staticmethod
    def configured_initial_delimiters() -> LambdaMapping:
        @chevron.func
        def value() -> str:
            return "<<planet>>"

        return {"value": value}

    @staticmethod
    def parent_delimiters() -> LambdaMapping:
        @chevron.func
        def value() -> str:
            return "{{name}}"

        return {"value": value}

    @staticmethod
    def escaped_markup() -> LambdaMapping:
        @chevron.func
        def markup() -> str:
            return "{{value}} >"

        return {"markup": markup}

    @staticmethod
    def indented_partial() -> LambdaMapping:
        @chevron.func
        def value() -> str:
            return "a\nb"

        return {"value": value}

    @staticmethod
    def opening_delimiters() -> LambdaMapping:
        @chevron.section
        def repeat(text: str) -> str:
            return text

        return {"repeat": repeat}

    @staticmethod
    def precedence() -> LambdaMapping:
        @chevron.func
        def value() -> str:
            return "registered"

        return {"value": value}

    @staticmethod
    def nested_partial() -> LambdaMapping:
        @chevron.func
        def value() -> str:
            return "{{message}}"

        return {"value": value}

    @staticmethod
    def returned_partial() -> LambdaMapping:
        @chevron.section
        def include(_text: str) -> str:
            return "|>part|"

        return {"include": include}

    @staticmethod
    def recursively_rendered_text() -> LambdaMapping:
        @chevron.func
        def outer() -> str:
            return "{{inner}}"

        @chevron.func
        def inner() -> str:
            return "rendered"

        return {"outer": outer, "inner": inner}


class _AsyncLambdaFactories:
    @staticmethod
    def declared_protocols() -> LambdaMapping:
        @chevron.func
        async def interpolation() -> str:
            return "{{name}}"

        @chevron.section
        async def section(body: str) -> str:
            return body

        @chevron.compat
        async def compatibility(body: str, render: Any) -> str:
            return await render(body, {"name": "compatibility"})

        return {
            "interpolation": interpolation,
            "section": section,
            "compatibility": compatibility,
        }

    @staticmethod
    def parent_delimiters() -> LambdaMapping:
        @chevron.func
        async def value() -> str:
            return "{{name}}"

        return {"value": value}

    @staticmethod
    def awaitable_result() -> LambdaMapping:
        async def result() -> str:
            return "value"

        @chevron.func
        def value() -> Any:
            return result()

        return {"value": value}

    @staticmethod
    def indented_partial() -> LambdaMapping:
        @chevron.func
        async def value() -> str:
            return "a\nb"

        return {"value": value}

    @staticmethod
    def falsey_temporary_data() -> LambdaMapping:
        @chevron.compat
        async def value(text: str, render: Any) -> str:
            return await render(text, {})

        return {"value": value}

    @staticmethod
    def synchronous_compatibility_callback() -> LambdaMapping:
        @chevron.compat
        def value(text: str, render: Any) -> Any:
            return render(text, {"message": "forwarded"})

        return {"value": value}


class _ExplicitMappingLambdaFactories:
    @staticmethod
    def action(_text: str, _render: Any) -> str:
        return "registered"

    @staticmethod
    def render_body(text: str, render: Any) -> str:
        return render(text)

    @staticmethod
    def outer(_text: str, _render: Any) -> str:
        return "outer"

    @staticmethod
    def inner(_text: str, _render: Any) -> str:
        return "inner"

    @staticmethod
    def action_mapping() -> LambdaMapping:
        return {"action": _ExplicitMappingLambdaFactories.action}

    @staticmethod
    def dotted_partial_mapping() -> LambdaMapping:
        return {"workflow.contains": _ExplicitMappingLambdaFactories.render_body}

    @staticmethod
    def scope_precedence_mapping() -> LambdaMapping:
        return {"action": _ExplicitMappingLambdaFactories.outer}

    @staticmethod
    def bound_method_mapping() -> LambdaMapping:
        class Handler:
            def action(self, _text: str, _render: Any) -> str:
                return "called"

        return {"action": Handler().action}

    @staticmethod
    def class_bound_method_mapping() -> LambdaMapping:
        class Handler:
            @classmethod
            def action(cls, _text: str, _render: Any) -> str:
                return "called"

        return {"action": Handler.action}

    @staticmethod
    def chain_map() -> LambdaMapping:
        return ChainMap({"callback": _ExplicitMappingLambdaFactories.action})

    @staticmethod
    def mapping_proxy() -> LambdaMapping:
        return MappingProxyType({"callback": _ExplicitMappingLambdaFactories.action})


SYNC_LAMBDA_CASES = (
    LambdaRenderCase(
        name="declared function uses configured initial delimiters",
        template="<<=| |=>>|value|",
        data={"planet": "Earth"},
        expected="Earth",
        initial_delimiters=("<<", ">>"),
        lambdas_factory=_SyncLambdaFactories.configured_initial_delimiters,
    ),
    LambdaRenderCase(
        name="declared function expansion resumes parent delimiters",
        template="{{#item}}{{=<% %>=}}<%value%>|<%name%><%/item%>",
        data={"item": {"name": "inner"}},
        expected="inner|inner",
        lambdas_factory=_SyncLambdaFactories.parent_delimiters,
    ),
    LambdaRenderCase(
        name="declared function renders escaped and unescaped interpolation",
        template="{{markup}}|{{{markup}}}",
        data={"value": "<tag>"},
        expected="&amp;lt;tag&amp;gt; &gt;|&lt;tag&gt; >",
        lambdas_factory=_SyncLambdaFactories.escaped_markup,
    ),
    LambdaRenderCase(
        name="declared function renders in an indented partial",
        template="  {{>part}}\n",
        partials={"part": "{{value}}\n"},
        expected="  a\nb\n",
        lambdas_factory=_SyncLambdaFactories.indented_partial,
    ),
    LambdaRenderCase(
        name="declared section uses opening delimiters after body changes them",
        template="{{=| |=}}|#repeat||planet||= {{ }} =|{{planet}}{{/repeat}}",
        data={"planet": "Earth"},
        expected="EarthEarth",
        lambdas_factory=_SyncLambdaFactories.opening_delimiters,
    ),
    LambdaRenderCase(
        name="declared function takes precedence over template data",
        template="{{value}}",
        data={"value": "template data"},
        expected="registered",
        lambdas_factory=_SyncLambdaFactories.precedence,
    ),
    LambdaRenderCase(
        name="declared function remains available in nested partial",
        template="{{>partial}}",
        data={"message": "rendered"},
        partials={"partial": "{{value}}"},
        expected="rendered",
        lambdas_factory=_SyncLambdaFactories.nested_partial,
    ),
    LambdaRenderCase(
        name="declared section returning partial uses render default delimiters",
        template="{{=| |=}}|#include|ignored|/include|",
        data={"value": "rendered"},
        partials={"part": "{{value}}"},
        expected="rendered",
        lambdas_factory=_SyncLambdaFactories.returned_partial,
    ),
    LambdaRenderCase(
        name="declared functions remain available in recursively rendered text",
        template="{{outer}}",
        expected="rendered",
        lambdas_factory=_SyncLambdaFactories.recursively_rendered_text,
    ),
)


ASYNC_LAMBDA_CASES = (
    LambdaRenderCase(
        name="async declared lambda protocols render their results",
        template=(
            "{{interpolation}}|{{#section}}{{name}}{{/section}}|"
            "{{#compatibility}}{{name}}{{/compatibility}}"
        ),
        data={"name": "declared"},
        expected="declared|declared|compatibility",
        lambdas_factory=_AsyncLambdaFactories.declared_protocols,
    ),
    LambdaRenderCase(
        name="async declared function expansion resumes parent delimiters",
        template="{{#item}}{{=<% %>=}}<%value%>|<%name%><%/item%>",
        data={"item": {"name": "inner"}},
        expected="inner|inner",
        lambdas_factory=_AsyncLambdaFactories.parent_delimiters,
    ),
    LambdaRenderCase(
        name="async renderer awaits declared function awaitable result",
        template="{{value}}",
        expected="value",
        lambdas_factory=_AsyncLambdaFactories.awaitable_result,
    ),
    LambdaRenderCase(
        name="async declared function renders in an indented partial",
        template="  {{>part}}\n",
        partials={"part": "{{value}}\n"},
        expected="  a\nb\n",
        lambdas_factory=_AsyncLambdaFactories.indented_partial,
    ),
    LambdaRenderCase(
        name="async compatibility callback keeps parent data for falsey temporary data",
        template="{{#value}}{{message}}{{/value}}",
        data={"message": "outer"},
        expected="outer",
        lambdas_factory=_AsyncLambdaFactories.falsey_temporary_data,
    ),
    LambdaRenderCase(
        name="synchronous compatibility callback forwards async render callback",
        template="{{#value}}{{message}}{{/value}}",
        expected="forwarded",
        lambdas_factory=_AsyncLambdaFactories.synchronous_compatibility_callback,
    ),
)


EXPLICIT_MAPPING_LAMBDA_CASES = (
    LambdaRenderCase(
        name="explicit mapping supplies section callable without template data",
        template="{{#action}}body{{/action}}",
        expected="registered",
        lambdas_factory=_ExplicitMappingLambdaFactories.action_mapping,
    ),
    LambdaRenderCase(
        name="explicit dotted mapping remains available inside partial",
        template="{{>included}}",
        data_factory=lambda: {
            "workflow": {"contains": _ExplicitMappingLambdaFactories.render_body},
            "value": "rendered",
        },
        partials={"included": "{{#workflow.contains}}{{value}}{{/workflow.contains}}"},
        expected="rendered",
        lambdas_factory=_ExplicitMappingLambdaFactories.dotted_partial_mapping,
    ),
    LambdaRenderCase(
        name="explicit mapping remains available in iterable section scope",
        template="{{#items}}{{#action}}{{value}}{{/action}}{{/items}}",
        data_factory=lambda: {
            "items": [
                {
                    "action": _ExplicitMappingLambdaFactories.render_body,
                    "value": "first",
                }
            ]
        },
        expected="first",
        lambdas_factory=lambda: {"action": _ExplicitMappingLambdaFactories.render_body},
    ),
    LambdaRenderCase(
        name="explicit mapping works with scopes",
        template="{{#callback}}body{{/callback}}",
        scopes=({"callback": _ExplicitMappingLambdaFactories.action},),
        expected="registered",
        lambdas_factory=lambda: {"callback": _ExplicitMappingLambdaFactories.action},
    ),
    LambdaRenderCase(
        name="explicit mapping precedes scope lookup",
        template="{{#action}}body{{/action}}",
        scopes=(
            {"action": _ExplicitMappingLambdaFactories.inner},
            {"action": _ExplicitMappingLambdaFactories.outer},
        ),
        expected="outer",
        lambdas_factory=_ExplicitMappingLambdaFactories.scope_precedence_mapping,
    ),
    LambdaRenderCase(
        name="registered callable is truthy in inverted section",
        template="{{^callback}}fallback{{/callback}}",
        data_factory=lambda: {"callback": _ExplicitMappingLambdaFactories.action},
        expected="",
        lambdas_factory=lambda: {"callback": _ExplicitMappingLambdaFactories.action},
    ),
    LambdaRenderCase(
        name="explicit mapping supplies bound method without template data",
        template="{{#action}}body{{/action}}",
        expected="called",
        lambdas_factory=_ExplicitMappingLambdaFactories.bound_method_mapping,
    ),
    LambdaRenderCase(
        name="explicit mapping supplies class-bound method",
        template="{{#action}}body{{/action}}",
        expected="called",
        lambdas_factory=_ExplicitMappingLambdaFactories.class_bound_method_mapping,
    ),
    LambdaRenderCase(
        name="explicit mapping accepts ChainMap",
        template="{{#callback}}body{{/callback}}",
        data_factory=lambda: {"callback": _ExplicitMappingLambdaFactories.action},
        expected="registered",
        lambdas_factory=_ExplicitMappingLambdaFactories.chain_map,
    ),
    LambdaRenderCase(
        name="explicit mapping accepts mapping proxy",
        template="{{#callback}}body{{/callback}}",
        data_factory=lambda: {"callback": _ExplicitMappingLambdaFactories.action},
        expected="registered",
        lambdas_factory=_ExplicitMappingLambdaFactories.mapping_proxy,
    ),
)
