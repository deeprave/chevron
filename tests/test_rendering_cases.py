"""Shared source-template behavior exercised through Chevron's sync API."""

import pytest

import chevron
from filesystem_partial_cases import FILESYSTEM_PARTIAL_CASES
from rendering_cases import FilesystemPartialRenderCase, LambdaRenderCase, RenderCase
from rendering_case_sets import SYNC_RENDER_CASES


@pytest.mark.parametrize("case", SYNC_RENDER_CASES, ids=lambda case: case.name)
def test_sync_rendering_case(case: RenderCase) -> None:
    """Render every shared source-template case through the public sync API."""
    lambdas = case.render_lambdas() if isinstance(case, LambdaRenderCase) else None
    def_ldel, def_rdel = case.initial_delimiters
    assert (
        chevron.render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            scopes=case.scopes,
            lambdas=lambdas,
            def_ldel=def_ldel,
            def_rdel=def_rdel,
        )
        == case.expected
    )


@pytest.mark.parametrize("case", FILESYSTEM_PARTIAL_CASES, ids=lambda case: case.name)
def test_sync_filesystem_partial_case(
    tmp_path, case: FilesystemPartialRenderCase
) -> None:
    """Render every ordinary filesystem partial case through the sync API."""
    case.materialise_partials(tmp_path)
    def_ldel, def_rdel = case.initial_delimiters
    assert (
        chevron.render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            partials_path=tmp_path,
            partials_ext=case.partials_ext,
            scopes=case.scopes,
            def_ldel=def_ldel,
            def_rdel=def_rdel,
        )
        == case.expected
    )
