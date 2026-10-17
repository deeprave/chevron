from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chevron-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"

from .main import main, cli_main
from .renderer import compat, func, render, section
from .tokenizer import ChevronError

__all__ = [
    "main",
    "render",
    "cli_main",
    "ChevronError",
    "compat",
    "func",
    "section",
    "__version__",
]
