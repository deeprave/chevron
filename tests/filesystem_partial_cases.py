"""Chevron-owned public behavior cases for ordinary filesystem partials."""

from rendering_cases import FilesystemPartialRenderCase


FILESYSTEM_PARTIAL_CASES = (
    FilesystemPartialRenderCase(
        name="filesystem partial uses default extension",
        template="Hello, {{>greeting}}!",
        data={"name": "Ada"},
        filesystem_partials={"greeting.mustache": "{{name}}"},
        expected="Hello, Ada!",
    ),
    FilesystemPartialRenderCase(
        name="filesystem partial uses configured extension",
        template="{{>greeting}}",
        filesystem_partials={"greeting.template": "configured extension"},
        partials_ext="template",
        expected="configured extension",
    ),
    FilesystemPartialRenderCase(
        name="filesystem partial resolves nested relative name",
        template="{{>layouts/header}}",
        filesystem_partials={"layouts/header.mustache": "nested header"},
        expected="nested header",
    ),
    FilesystemPartialRenderCase(
        name="configured partial takes precedence over filesystem partial",
        template="{{>greeting}}",
        partials={"greeting": "configured partial"},
        filesystem_partials={"greeting.mustache": "filesystem partial"},
        expected="configured partial",
    ),
    FilesystemPartialRenderCase(
        name="missing filesystem partial renders empty",
        template="before{{>missing}}after",
        expected="beforeafter",
    ),
)
