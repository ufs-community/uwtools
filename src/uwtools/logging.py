"""
Encapsulates logging uniformity and exposes convenience methods
to enforce requirements while not coupling.

`handle_logging` method need only be called once from the root of
the application (typically in main() or equivalent).

Examples:
handle_logging() -> uses module defaults
handle_logging(level="debug", format=".....") -> overrides defaults
handle_logging(args=args) -> convenience for using argparse to determine
log level from CLI.

[See Using logging in multiple modules](https://docs.python.org/3/howto/logging-cookbook.html)
"""
import logging

LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "default": logging.INFO,
    "debug": logging.DEBUG,
}


def handle_logging(**kwargs):  # pylint: disable=unused-variable
    """handles default logging"""
    level = LEVELS["DEFAULT"]
    if "args" in kwargs:
        level = LEVELS.get(kwargs["args"].log.lower())
    if level is None:
        raise ValueError(f"log level must be one of: {' | '.join(LEVELS.keys())}")

    logging.basicConfig(
        level=level, format=LOG_FORMAT if "format" not in kwargs else kwargs["format"]
    )


if __name__ == "__main__":
    pass
