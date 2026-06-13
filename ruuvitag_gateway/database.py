"""Module for writing data to different databases."""

import logging
from typing import Any

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from ruuvitag_sensor.ruuvi_types import SensorData

from .configuration import Configuration, RuuviTagDevice
from .writer import WriterError

logger = logging.getLogger(__name__)

_COMMON: tuple[str, ...] = ("temperature", "humidity", "pressure")

# Complete field list per data_format, common fields first.
_FORMAT_FIELDS: dict[int, tuple[str, ...]] = {
    5: (*_COMMON, "battery", "tx_power", "rssi"),
    6: (*_COMMON, "co2", "voc", "nox", "pm_2_5", "luminosity"),
    0xE1: (*_COMMON, "co2", "voc", "nox", "pm_2_5", "luminosity", "pm_1", "pm_4", "pm_10"),
}


def _extract_fields(data: SensorData) -> dict[str, float | int]:
    """Extract the relevant fields from the sensor data based on the data format.

    :param data: Sensor data payload.
    :return: A dictionary of the extracted fields.
    """
    raw: dict[str, Any] = data  # type: ignore[assignment]
    return {
        key: val
        for key in _FORMAT_FIELDS.get(raw.get("data_format", -1), ())
        if (val := raw.get(key)) is not None
    }


def write_influxdb(config: Configuration, device: RuuviTagDevice, mac: str, data: SensorData) -> None:
    """Write sensor data to InfluxDB.

    :param config: Gateway configuration.
    :param device: The configured device this reading came from.
    :param mac: The MAC address reported by the sensor.
    :param data: Sensor data payload.
    :raises WriterError: If there is an error writing to InfluxDB.
    """
    measurement: Any = config.influxdb.measurements.get(device.name, device.name)
    fields: dict[str, float | int] = _extract_fields(data)
    tags: dict[str, str] = {"mac": mac, "device": device.name}

    try:
        client: InfluxDBClient = InfluxDBClient(host=config.influxdb.host, port=config.influxdb.port)
        client.create_database(config.influxdb.database)
        client.switch_database(config.influxdb.database)

        logger.info(
            "Write influxdb/%s/%s tags=%s fields=%s",
            config.influxdb.database,
            measurement,
            tags,
            fields,
        )

        result: bool = client.write_points([{"measurement": measurement, "tags": tags, "fields": fields}])
        if not result:
            raise WriterError("Write to InfluxDB failed")

    except WriterError:
        raise
    except (InfluxDBClientError, OSError) as e:
        raise WriterError(f"InfluxDB error: {e}") from e
