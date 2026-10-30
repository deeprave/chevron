"""Process-wide configuration for optional Chevron extensions."""

from enum import FlagBoundary, IntFlag, auto


class Extension(IntFlag, boundary=FlagBoundary.STRICT):
    """Optional non-standard Chevron behaviour configured at application startup."""

    NONE = 0
    INVERTED_ITERATORS = auto()
    ALL = INVERTED_ITERATORS

    @classmethod
    def enable(cls, extensions: "Extension") -> None:
        """Enable one or more extensions for the application."""
        global _enabled_extensions
        _enabled_extensions |= cls(extensions)

    @classmethod
    def disable(cls, extensions: "Extension") -> None:
        """Disable one or more extensions for the application."""
        global _enabled_extensions
        _enabled_extensions &= ~cls(extensions)

    @classmethod
    def is_enabled(cls, extensions: "Extension") -> bool:
        """Return whether every requested extension is enabled."""
        requested = cls(extensions)
        return (_enabled_extensions & requested) == requested


_enabled_extensions = Extension.NONE
