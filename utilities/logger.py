import logging
import logging.handlers
import os
from pathlib import Path

import pandas as pd

from loader import engine
from npl_planner.utilities.utils import timestamp


class LogDBHandler(logging.Handler):
    """Customized logging handler that puts logs to the database
    """
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            log_df = pd.DataFrame(
                [{
                    "run_id": int(os.environ["run_id"]),
                    "level": record.levelname,
                    "message": record.msg,
                    "add_time": record.asctime,
                }]
            )

            log_df.to_sql(
                "log",
                con=engine,
                schema="param",
                index=False,
                if_exists="append",
            )


def setup_global_logger(log_filepath=None):
    """Setup logger for logging

    Args:
        log_filepath: log file path. If not specified, only log to console

    Returns:
        logger that can log message at different level
    """
    logger = logging.getLogger(__name__)

    try:
        if not logger.handlers:
            logger.propagate = False
            logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(levelname)s:[%(asctime)s] - %(message)s")

            logging.getLogger("tornado").propagate = False
            logging.getLogger("livereload").propagate = False

            # Add sysout handler
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            # Add DB handler
            logger.addHandler(LogDBHandler())

            if log_filepath:
                formatter = logging.Formatter(
                    "%(levelname)s:[%(asctime)s] - "
                    + "[%(filename)s, line-%(lineno)d] - %(message)s"
                )
                # Add file handler
                Path("logs").mkdir(parents=True, exist_ok=True)
                fh = logging.handlers.TimedRotatingFileHandler(
                    Path("logs") / log_filepath, when="midnight", interval=1
                )
                fh.suffix = "%Y%m%d"
                fh.setFormatter(formatter)
                logger.addHandler(fh)

    except Exception as ex:
        logger.error(ex)

    return logger


logger = setup_global_logger(f"NPL-{timestamp()}.log")
