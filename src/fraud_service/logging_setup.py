import logging
import sys

import structlog

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "national_id",
    "card_number",
    "registry_token",
}


def _mask_sensitive(
    _logger,
    _method_name,
    event_dict,
):
    for key in list(event_dict):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "***MASKED***"

    return event_dict


def configure_logging(level: str = "INFO") -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        stream=sys.stdout,
        level=numeric_level,
        format="%(message)s",
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(
                fmt="iso",
                utc=True,
            ),
            _mask_sensitive,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            numeric_level
        ),
        logger_factory=structlog.PrintLoggerFactory(
            file=sys.stdout
        ),
        cache_logger_on_first_use=True,
    )
