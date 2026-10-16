from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chevron-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"

from .main import main, cli_main
from .renderer import render
from .tokenizer import ChevronError

__all__ = ["main", "render", "cli_main", "ChevronError", "__version__"]
