"""
Module for RuuviTagGateway to handle sensor data and write it to
different cloud services or databases.
"""

from ruuvitag_sensor.ruuvi import RunFlag
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import MacAndSensorData

from .cloud import CloudWriter
from .cloud import CloudWriterError
from .configuration import Configuration
from .database import DatabaseWriter
from .database import DatabaseWriterError

# RunFlag for stopping execution at desired time
run_flag = RunFlag()


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
        """
        Initialize the RuuviTagGateway with configuration and optional writers.

        :param config: Configuration object containing settings for the gateway.
        :param db_writer: Function to write data to the database (InfluxDB).
        :param cloud_writer: Function to write data to the cloud (ThingSpeak).
        """
        self.config = config
        self.db_writer = db_writer
        self.cloud_writer = cloud_writer

    def callback(self, config: Configuration, data: MacAndSensorData) -> None:
        """
        Callback function to handle environment data from RuuviTagSensor.
        This function is called when data is received from the sensor.
        It writes the data to the database and cloud if the respective writers are provided.

        :param config: Configuration object.
        :param data: Tuple containing MAC address and sensor data.
        raises RuuviTagGatewayError: If there is an error in writing data to the database or cloud.
        """

        errors: list[str] = []

        # etract the sensor data from the tuple
        mac = data[0]
        sensor_data = data[1]

        if self.db_writer:
            try:
                self.db_writer(config, sensor_data)
            except DatabaseWriterError as e:
                errors.append(f"DatabaseWriterError[{self.db_writer.__name__}]: {e}")

        if self.cloud_writer:
            try:
                self.cloud_writer(config, sensor_data)
            except CloudWriterError as e:
                errors.append(f"CloudWriterError[{self.cloud_writer.__name__}]: {e}")

        # Stop the run_flag to prevent further data collection
        run_flag.running = False

        # If there are any errors, raise an exception
        if errors:
            raise RuuviTagGatewayError(
                f"Errors writing data from sensor[{mac}]: {', '.join(errors)}"
            )

    def run(self):
        """
        Run the RuuviTagSensor to collect data and call the callback function.

        :raises RuuviTagGatewayError: If there is an error in RuuviTagSensor.
        """
        try:
            RuuviTagSensor.get_data(
                lambda data: self.callback(self.config, data),
                [self.config.ruuvitag.device.mac],
                run_flag,
            )

        except RuntimeError as e:
            raise RuuviTagGatewayError(
                (
                    "Error in RuuviTagSensor "
                    f"{self.config.ruuvitag.device.name}[{self.config.ruuvitag.device.mac}]: {e}"
                )
            ) from e
