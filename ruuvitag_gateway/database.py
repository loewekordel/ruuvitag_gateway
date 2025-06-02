"""
Module for writing data to different databases.
"""

import logging
from typing import Callable

from influxdb import InfluxDBClient

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
    """
    Write data to InfluxDB.

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
        # Setup database connection
        client = InfluxDBClient(host=config.influxdb.host, port=config.influxdb.port)

        # Check if database exists, create if not
        dbs = [n["name"] for n in client.get_list_database()]
        if config.influxdb.database.name not in dbs:
            logger.info(f"Create database '{config.influxdb.database.name}'")
            client.create_database(config.influxdb.database.name)
        client.switch_database(config.influxdb.database.name)

        logger.info(
            (
                "Write fields influxdb/"
                f"{config.influxdb.database.name}/{config.influxdb.database.measurement} = "
                f"{fields}"
            )
        )

        # Write points to InfluxDB
        result = client.write_points(
            [
                {
                    "measurement": config.influxdb.database.measurement,
                    "fields": fields,
                }
            ]
        )

        if not result:
            raise DatabaseWriterError("Write to InfluxDB failed")

    except Exception as e:
        raise DatabaseWriterError(e) from e
