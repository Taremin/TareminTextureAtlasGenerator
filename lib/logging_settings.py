import os
from logging import config, getLogger

# DEFAULT_LEVEL = "DEBUG"
DEFAULT_LEVEL = "WARN"
LOG_PATH = "../log"


def get_logger(name=__name__, level=DEFAULT_LEVEL):
    logging_settings(name, level)
    return getLogger(name)


def logging_settings(name=__name__, level=DEFAULT_LEVEL):
    console_formatter_name = name + ".formatter"
    console_handler_name = name + ".console"
    error_formatter_name = name + ".errorformatter"
    error_handler_name = name + ".error"
    base_log_dir = os.path.join(os.path.dirname(__file__), LOG_PATH)
    configure = {
        "version": 1,
        "formatters": {
            console_formatter_name: {
                "format": "[%(levelname)s]\t%(name)s:\t%(message)s"
            },
            error_formatter_name: {
                "format": "\t".join([
                    "%(asctime)s",
                    "[%(levelname)s]",
                    "%(name)s:",
                    "%(message)s"
                ])
            }
        },
        "handlers": {
            console_handler_name: {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": console_formatter_name,
            },
            error_handler_name: {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "filename": os.path.join(base_log_dir, "error.log"),
                "maxBytes": 1024 * 1024,
                "backupCount": 5,
                "formatter": error_formatter_name,
            }
        },
        "loggers": {
            name: {
                "level": level,
                "handlers": [
                    error_handler_name,
                ],
                "propagate": False
            }
        },
        "disable_existing_loggers": False
    }
    config.dictConfig(configure)
