"""RuuviTagGateway module.

Handles RuuviTag sensor data and writes it to cloud services or databases.
"""

import asyncio
import logging

from ruuvitag_sensor.ruuvi import RuuviTagSensor

from .configuration import Configuration, RuuviTagDevice
from .writer import Writer, WriterError

logger = logging.getLogger(__name__)


class RuuviTagGatewayError(Exception):
    """Custom exception for RuuviTagGateway errors."""


class RuuviTagGateway:
    """Collects one reading per configured device and writes it to all registered writers."""

    def __init__(self, config: Configuration, writers: list[Writer]):
        """Initialize the gateway.

        :param config: The gateway configuration.
        :param writers: A list of writers to which sensor data will be written.
        """
        self.config: Configuration = config
        self.writers: list[Writer] = writers
        self._mac_to_device: dict[str, RuuviTagDevice] = {
            d.mac.upper(): d for d in config.ruuvitag.devices
        }

    def run(self) -> None:
        """Scan for all configured devices, then pass each reading to every registered writer.

        :raises RuuviTagGatewayError: If the BLE scan fails.
        :raises ExceptionGroup: If any writer fails.
        """
        macs: list[str] = [d.mac for d in self.config.ruuvitag.devices]
        try:
            results = asyncio.run(
                RuuviTagSensor.get_data_for_sensors_async(
                    macs=macs,
                    search_duration_sec=self.config.ruuvitag.scan_duration_sec,
                )
            )
        except RuntimeError as e:
            raise RuuviTagGatewayError(f"BLE scan failed: {e}") from e

        exceptions: list[Exception] = []
        for mac, sensor_data in results.items():
            device: RuuviTagDevice | None = self._mac_to_device.get(mac.upper())
            if device is None:
                logger.debug("unknown mac %s, skipping", mac)
                continue

            for writer in self.writers:
                try:
                    writer(self.config, device, mac, sensor_data)
                except WriterError as e:
                    exceptions.append(e)

        if exceptions:
            raise ExceptionGroup("sensor write errors", exceptions)
