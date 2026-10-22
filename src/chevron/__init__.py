from importlib.metadata import PackageNotFoundError, version
import logging
from pathlib import Path

try:
    __version__ = version("chevron-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"

from .main import main, cli_main
from .renderer import (
    LambdaRegistry,
    Logger,
    PartialMapping,
    ScopeSequence,
    TemplateData,
    TemplateInput,
    compat,
    func,
    render,
    section,
)
from .tokenizer import ChevronError


async def async_render(
    template: TemplateInput = "",
    data: TemplateData = {},
    partials_path: str | Path | None = None,
    partials_ext: str = "mustache",
    partials_dict: PartialMapping = {},
    padding: str = "",
    def_ldel: str = "{{",
    def_rdel: str = "}}",
    scopes: ScopeSequence | None = None,
    warn: TemplateData = False,
    lambdas: LambdaRegistry | None = None,
    *,
    logger: Logger | None = None,
    log_level: int = logging.WARNING,
) -> str:
    """Render asynchronously when the optional AnyIO support is installed."""
    try:
        from .async_renderer import async_render as render_with_anyio
    except ModuleNotFoundError as error:
        if error.name != "anyio":
            raise
        raise RuntimeError(
            "async_render() requires AnyIO; install chevron-ng[anyio] "
            "or chevron-ng[trio]"
        ) from error
    return await render_with_anyio(
        template,
        data,
        partials_path,
        partials_ext,
        partials_dict,
        padding,
        def_ldel,
        def_rdel,
        scopes,
        warn,
        lambdas,
        logger=logger,
        log_level=log_level,
    )


__all__ = [
    "main",
    "render",
    "async_render",
    "cli_main",
    "ChevronError",
    "compat",
    "func",
    "section",
    "__version__",
]
