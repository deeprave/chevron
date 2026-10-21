from importlib.metadata import PackageNotFoundError, version
import logging

try:
    __version__ = version("chevron-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"

from .main import main, cli_main
from .renderer import compat, func, render, section
from .tokenizer import ChevronError


async def async_render(
    template="",
    data={},
    partials_path=None,
    partials_ext="mustache",
    partials_dict={},
    padding="",
    def_ldel="{{",
    def_rdel="}}",
    scopes=None,
    warn=False,
    lambdas=None,
    *,
    logger=None,
    log_level=logging.WARNING,
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
