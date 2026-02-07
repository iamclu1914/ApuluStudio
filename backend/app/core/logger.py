"""Structured logging for the API."""

import json
import sys
from datetime import datetime
from typing import Any


class Logger:
    """Structured JSON logger with context support."""

    def __init__(self, name: str = "apulu"):
        self.name = name

    def _log(
        self,
        level: str,
        message: str,
        context: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        """Internal log method that outputs structured JSON."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
        }

        if context:
            entry.update(context)

        if error:
            entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
            if hasattr(error, "__traceback__") and error.__traceback__:
                import traceback
                entry["error"]["stack"] = "".join(
                    traceback.format_tb(error.__traceback__)
                )

        # Output to stdout for info/debug, stderr for warn/error
        output = sys.stderr if level in ("error", "warn") else sys.stdout
        print(json.dumps(entry), file=output)

    def info(self, message: str, **context: Any) -> None:
        """Log info level message."""
        self._log("info", message, context if context else None)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug level message."""
        self._log("debug", message, context if context else None)

    def warn(self, message: str, **context: Any) -> None:
        """Log warning level message."""
        self._log("warn", message, context if context else None)

    def error(self, message: str, error: Exception | None = None, **context: Any) -> None:
        """Log error level message with optional exception."""
        self._log("error", message, context if context else None, error)

    def request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **context: Any,
    ) -> None:
        """Log an HTTP request."""
        self._log(
            "info",
            f"{method} {path} {status_code}",
            {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                **context,
            },
        )


# Default logger instance
logger = Logger()
