"""Exception hierarchy for everythingtohtml.

The layout mirrors the ergonomics of well-behaved conversion libraries: a single
base class so callers can ``except EverythingToHtmlException`` and catch anything
the library raises on purpose.
"""

from __future__ import annotations

__all__ = [
    "EverythingToHtmlException",
    "UnsupportedFormatException",
    "FileConversionException",
    "MissingDependencyException",
]


class EverythingToHtmlException(Exception):
    """Base class for all exceptions raised by everythingtohtml."""


class MissingDependencyException(EverythingToHtmlException):
    """Raised when a converter needs an optional dependency that is not installed.

    The message tells the user exactly which extra to install, e.g.::

        pip install everythingtohtml[docx]
    """


class UnsupportedFormatException(EverythingToHtmlException):
    """Raised when no registered converter is able to handle the input."""


class FailedConversionAttempt:
    """Bookkeeping for a converter that accepted the input but then failed.

    Collected so :class:`FileConversionException` can report every attempt rather
    than only the last traceback, which makes debugging multi-converter inputs far
    easier.
    """

    def __init__(self, converter: object, exc_info: object | None = None) -> None:
        self.converter = converter
        self.exc_info = exc_info


class FileConversionException(EverythingToHtmlException):
    """Raised when one or more converters accepted the input but all failed."""

    def __init__(
        self,
        message: str | None = None,
        attempts: list[FailedConversionAttempt] | None = None,
    ) -> None:
        self.attempts = attempts or []
        if message is None:
            if self.attempts:
                names = ", ".join(type(a.converter).__name__ for a in self.attempts)
                message = f"All converters that accepted the input failed: {names}"
            else:
                message = "File conversion failed."
        super().__init__(message)
