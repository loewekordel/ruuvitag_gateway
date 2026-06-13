"""RuuviTag Sensor Data Logger.

Collect data from a RuuviTag sensor and log it to InfluxDB and ThingSpeak.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ruuvitag_gateway.configuration import Configuration, ConfigurationError, load_configuration_from_file
from ruuvitag_gateway.gateway import RuuviTagGateway, RuuviTagGatewayError
from ruuvitag_gateway.services import SERVICE_MAP

try:
    from importlib.metadata import PackageNotFoundError, version
    __version__ = version("ruuvitag-gateway")
except PackageNotFoundError:
    import tomllib
    with open(Path(__file__).with_name("pyproject.toml"), "rb") as _f:
        __version__ = tomllib.load(_f)["project"]["version"]

logger = logging.getLogger(__name__)

SCRIPT_NAME = "ruuvitag_gateway"
LOG_FILE_SIZE = 100 * 1024  # 100 KB
LOG_BACKUP_COUNT = 10  # Number of backup log files to keep


def configure_logging(log_name: str, debug: bool = False) -> None:
    """Configure logging to use a rotating file handler.

    :param log_name: The name of the log file.
    """
    log_file = Path(__file__).with_name(f"{log_name}.log")

    # Create a RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        logging.Formatter("%(asctime)s|%(levelname)s| %(message)s")
    )

    # Create a StreamHandler for console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s| %(message)s")
    )  # No asctime for console

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        handlers=[
            file_handler,  # File handler for detailed logs
            console_handler,  # Console handler for real-time logs
        ],
    )


def main() -> int:
    """Run the RuuviTag gateway.

    :return: Exit code, 0 for success, 1 for failure.
    """
    # Configure logging
    configure_logging(SCRIPT_NAME)

    # Load configuration
    config_file: Path = Path(__file__).with_name("config.yaml")
    try:
        config: Configuration = load_configuration_from_file(config_file)
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    writers = [
        writer
        for name in (config.services.database, config.services.cloud)
        if name and (writer := SERVICE_MAP.get(name))
    ]

    try:
        gateway: RuuviTagGateway = RuuviTagGateway(config=config, writers=writers)
        gateway.run()

    except RuuviTagGatewayError as e:
        logger.error(e)
        return 1
    except ExceptionGroup as eg:
        for exc in eg.exceptions:
            logger.error(exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
