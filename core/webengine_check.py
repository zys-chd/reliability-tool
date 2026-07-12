"""Check if QWebEngine is available on this platform.

On some Windows / Python environments, the Qt WebEngine DLLs may be missing
or incompatible. This module provides a single function to detect availability
at runtime so callers can fall back gracefully (e.g. open HTML in browser).
"""

import logging

_LOGGER = logging.getLogger(__name__)


def is_webengine_available() -> bool:
    """Return True if PySide6.QtWebEngineWidgets can be imported.

    Also logs a warning if not available so it's visible in startup logs.
    """
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
        return True
    except ImportError as exc:
        _LOGGER.warning(
            "QWebEngine is not available (%s). "
            "HTML plots will be opened in the system browser instead.",
            exc,
        )
        return False
    except Exception as exc:
        _LOGGER.warning(
            "Unexpected error while checking QWebEngine: %s", exc
        )
        return False
