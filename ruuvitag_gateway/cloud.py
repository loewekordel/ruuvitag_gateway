"""
Module for writing data to different cloud services.
"""

import logging
from typing import Callable

import thingspeak

from .configuration import Configuration
from .sensor_data import RuuviTagSensorData

logger = logging.getLogger(__name__)

CloudWriter = Callable[[Configuration, RuuviTagSensorData], None]


class CloudWriterError(Exception):
    """Custom exception for CloudWriter errors."""


def write_thingspeak(config: Configuration, data: RuuviTagSensorData) -> None:
    """
    Write data to ThingSpeak channel.

    :param config: Configuration object containing ThingSpeak settings
    :param data: Sensor data from Ruuvitag sensor with mac and sensor data tuple.
    :raises CloudWriterError: If there is an error writing to ThingSpeak
    """
    # Prepare fields for ThingSpeak based on configuration
    # use the configured field indexes from the configuration and map them to the data
    fields = {
        config.thingspeak.fields[key]: data[key]
        for key in config.thingspeak.fields
        if key in data
    }

    logger.info((f"Write fields thingspeak/{config.thingspeak.channel_id} = {fields}"))

    try:
        channel = thingspeak.Channel(
            id=config.thingspeak.channel_id, api_key=config.thingspeak.api_key
        )
        response = channel.update(fields)
    except Exception as e:
        raise CloudWriterError(e) from e
