"""Topic collections assembled for the sync and async public API runners."""

from async_cases import ASYNC_ITERABLE_CASES
from inheritance_cases import ASYNC_INHERITANCE_CASES, INHERITANCE_CASES
from lambda_cases import (
    ASYNC_LAMBDA_CASES,
    EXPLICIT_MAPPING_LAMBDA_CASES,
    SYNC_LAMBDA_CASES,
)
from partial_cases import PARTIAL_CASES
from rendering_cases import RenderCase
from scope_cases import SCOPE_CASES
from section_cases import SECTION_CASES
from value_cases import VALUE_CASES
from whitespace_cases import WHITESPACE_CASES


SYNC_RENDER_CASES: tuple[RenderCase, ...] = (
    VALUE_CASES
    + SCOPE_CASES
    + SECTION_CASES
    + PARTIAL_CASES
    + INHERITANCE_CASES
    + WHITESPACE_CASES
    + SYNC_LAMBDA_CASES
    + EXPLICIT_MAPPING_LAMBDA_CASES
)
ASYNC_RENDER_CASES: tuple[RenderCase, ...] = (
    SYNC_RENDER_CASES
    + ASYNC_INHERITANCE_CASES
    + ASYNC_ITERABLE_CASES
    + ASYNC_LAMBDA_CASES
)
