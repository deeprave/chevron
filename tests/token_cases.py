"""Public direct-token validation cases shared by sync and async tests."""

from typing import TypeAlias


TokenSequence: TypeAlias = tuple[tuple[str, str], ...]
TokenValidationCase: TypeAlias = tuple[str, TokenSequence, str]


TOKEN_VALIDATION_CASES: tuple[TokenValidationCase, ...] = (
    (
        "unopened end",
        (("end", "body"),),
        'Token 1: trying to close tag "body", but it was not opened',
    ),
    (
        "mismatched end",
        (("section", "outer"), ("end", "inner")),
        'Token 2: trying to close tag "inner"; last open tag is "outer" at token 1',
    ),
    (
        "unclosed opener",
        (("parent", "layout"),),
        'Unexpected EOF in template tokens: tag "layout" opened at token 1 was never closed',
    ),
)


MALFORMED_RESERVED_TAG_TEMPLATES: tuple[str, ...] = (
    "{{$body}}unclosed block",
    "{{<layout}}unclosed parent",
)
