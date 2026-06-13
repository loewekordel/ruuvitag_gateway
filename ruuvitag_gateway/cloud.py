"""Module for writing data to different cloud services."""

import logging

import thingspeak
from ruuvitag_sensor.ruuvi_types import SensorData

from .configuration import Configuration, RuuviTagDevice
from .writer import WriterError

logger = logging.getLogger(__name__)


def write_thingspeak(config: Configuration, device: RuuviTagDevice, mac: str, data: SensorData) -> None:
    """Write sensor data to a ThingSpeak channel.

    :param config: Gateway configuration.
    :param device: The configured device this reading came from.
    :param mac: The MAC address reported by the sensor.
    :param data: Sensor data payload.
    :raises WriterError: If there is an error writing to ThingSpeak.
    """
    # Map the sensor data to ThingSpeak fields based on the configuration.
    fields: dict[int, float | int] = {
        config.thingspeak.fields[key]: data[key]  # type: ignore[literal-required]
        for key in config.thingspeak.fields
        if key in data
    }

    logger.info("Write thingspeak/%s device=%s fields=%s", config.thingspeak.channel_id, device.name, fields)

    try:
        channel: thingspeak.Channel = thingspeak.Channel(
            id=config.thingspeak.channel_id, api_key=config.thingspeak.api_key
        )
        response: int = channel.update(fields)
        if response == 0:
            raise WriterError("ThingSpeak update returned 0 — write failed")
    except WriterError:
        raise
    except Exception as e:
        raise WriterError(f"ThingSpeak error: {e}") from e
