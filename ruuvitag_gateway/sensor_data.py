"""
RuuviTag sensor data format.
"""

RuuviTagSensorData = dict[str, str | int | float]

"""
Sensor data tuple format:
{
    "data_format": int,
    "humidity": float,
    "temperature": float,
    "pressure": float,
    "acceleration": float,
    "acceleration_x": int,
    "acceleration_y": int,
    "acceleration_z": int,
    "tx_power": int,
    "battery": int,
    "movement_counter": int,
    "measurement_sequence_number": int,
    "mac": str,
    "rssi": int
}
"""
