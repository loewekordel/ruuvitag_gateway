"""RuuviTagGateway module.

Handles RuuviTag sensor data and writes it to cloud services or databases.
"""

from ruuvitag_sensor.ruuvi import RunFlag, RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import MacAndSensorData

from .cloud import CloudWriter, CloudWriterError
from .configuration import Configuration
from .database import DatabaseWriter, DatabaseWriterError


class RuuviTagGatewayError(Exception):
    """Custom exception for RuuviTagGateway errors."""


class RuuviTagGateway:
    """RuuviTagGateway class to handle the RuuviTag sensor data and write it to InfluxDB and ThingSpeak."""

    def __init__(
        self,
        config: Configuration,
        db_writer: DatabaseWriter | None,
        cloud_writer: CloudWriter | None,
    ):
        """Initialize the RuuviTagGateway with configuration and optional writers.

        :param config: Configuration object containing settings for the gateway.
        :param db_writer: Function to write data to the database (InfluxDB).
        :param cloud_writer: Function to write data to the cloud (ThingSpeak).
        """
        self.config = config
        self.db_writer = db_writer
        self.cloud_writer = cloud_writer
        self._run_flag = RunFlag()

    def callback(self, data: MacAndSensorData) -> None:
        """Handle environment data received from RuuviTagSensor.

        :param data: Tuple containing MAC address and sensor data.
        :raises ExceptionGroup: If writing to database or cloud fails.
        """
        mac = data[0]
        sensor_data = data[1]
        exceptions: list[Exception] = []

        if self.db_writer:
            try:
                self.db_writer(self.config, sensor_data)
            except DatabaseWriterError as e:
                exceptions.append(e)

        if self.cloud_writer:
            try:
                self.cloud_writer(self.config, sensor_data)
            except CloudWriterError as e:
                exceptions.append(e)

        self._run_flag.running = False

        if exceptions:
            raise ExceptionGroup(f"sensor[{mac}] write errors", exceptions)

    def run(self) -> None:
        """Run the RuuviTagSensor to collect data and call the callback function.

        :raises RuuviTagGatewayError: If there is an error in RuuviTagSensor.
        """
        try:
            RuuviTagSensor.get_data(
                self.callback,
                [self.config.ruuvitag.device.mac],
                self._run_flag,
            )
        except RuntimeError as e:
            raise RuuviTagGatewayError(
                f"Error in RuuviTagSensor "
                f"{self.config.ruuvitag.device.name}[{self.config.ruuvitag.device.mac}]: {e}"
            ) from e
