"""Module for writing data to different databases."""

import logging
from collections.abc import Callable

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

from .configuration import Configuration
from .sensor_data import RuuviTagSensorData

logger = logging.getLogger(__name__)

DatabaseWriter = Callable[[Configuration, RuuviTagSensorData], None]


class DatabaseWriterError(Exception):
    """Custom exception for DatabaseWriter errors."""


def write_influxdb(
    config: Configuration,
    data: RuuviTagSensorData,
) -> None:
    """Write data to InfluxDB.

    :param config: Configuration object containing InfluxDB settings.
    :param data: Sensor data from RuuviTag sensor with mac and sensor data tuple.
    :raises DatabaseWriterError: If there is an error writing to InfluxDB
    """
    # Prepare fields for InfluxDB
    fields = {
        "humidity": data["humidity"],
        "temperature": data["temperature"],
        "pressure": data["pressure"],
        "battery": data["battery"],
    }

    try:
        client = InfluxDBClient(host=config.influxdb.host, port=config.influxdb.port)
        client.create_database(config.influxdb.database.name)  # idempotent
        client.switch_database(config.influxdb.database.name)

        logger.info(
            "Write fields influxdb/"
            f"{config.influxdb.database.name}/{config.influxdb.database.measurement} = {fields}"
        )

        result = client.write_points([{"measurement": config.influxdb.database.measurement, "fields": fields}])
        if not result:
            raise DatabaseWriterError("Write to InfluxDB failed")

    except DatabaseWriterError:
        raise
    except (InfluxDBClientError, OSError) as e:
        raise DatabaseWriterError(f"InfluxDB error: {e}") from e
