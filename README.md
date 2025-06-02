# RuuviTag Gateway

The `ruuvitag_gateway` module collects environmental data from RuuviTag sensors and logs it to configurable database and cloud services (e.g., InfluxDB, ThingSpeak). It is designed to run on a Raspberry Pi or any system capable of running Python.

## Features

- Collects data from RuuviTag sensors.
- Logs data to a database (e.g. InfluxDB).
- Sends data to a cloud service (e.g. ThingSpeak).
- Configurable via a `config.yaml` file.
- Supports logging with log rotation.

## Requirements

The module requires the following Python dependencies, which are listed in the [`requirements.txt`](requirements.txt) file:

- `influxdb`
- `jsonschema`
- `pyyaml`
- `ruuvitag_sensor==2.3.1`
- `thingspeak`

Install the dependencies using:

```sh
pip install -r requirements.txt
```

## Configuration
Create a `config.yaml` file in the project root.
Below is an example with explanations for each section and option:
```yaml
ruuvitag:
  device:
    mac: "XX:XX:XX:XX:XX:XX"      # MAC address of your RuuviTag sensor
    name: "outdoor"               # Name for the sensor

services:
  database: influxdb              # Database service to use (must match a key in SERVICE_MAP)
  cloud: thingspeak               # Cloud service to use (must match a key in SERVICE_MAP)

influxdb:
  host: "localhost"               # InfluxDB server hostname or IP
  port: 8086                      # InfluxDB server port
  database:
    name: "databaseX"             # InfluxDB database name
    measurement: "outdoor"        # InfluxDB measurement name

thingspeak:
  channelId: XXXXXX               # ThingSpeak channel ID
  apiKey: "XXXXXXXXXXXXXXXX"      # ThingSpeak API key for writing data
  fields:                         # Mapping of sensor data keys to ThingSpeak field numbers
    temperature: 3                # e.g., temperature data will be sent to field3
    humidity: 4
    pressure: 5
    battery: 6
```

- **Service selection:**  
  The `services` section determines which database and cloud writers are used.  
  The names must match those in the `SERVICE_MAP` in [`ruuvitag_gateway/services.py`](ruuvitag_gateway/services.py).

- **InfluxDB:**  
  Data is written to the specified InfluxDB instance, database, and measurement.

- **ThingSpeak:**  
  Data is mapped to ThingSpeak fields as configured.  
  You can change which sensor value goes to which field by editing the `fields` mapping.

## Services

### Supported services
- Database
  - InfluxDB
- Cloud
  - ThingSpeak

### Adding new services

To add a new database or cloud service:
1. Implement a writer function (see `write_influxdb` or `write_thingspeak`).
2. Add it to `SERVICE_MAP` in [`ruuvitag_gateway/services.py`](ruuvitag_gateway/services.py).
3. Add the configuration section to `config.yaml`.

## Usage
Run the script using the following command:

```sh
python main.py
```

Alternatively, you can use the provided shell script to run the notifier (setup virtual environment required):

```sh
./ruuvitag_gateway.sh
```

## Logging
Logs are stored in a file named `ruuvitag_gateway.log` in the same directory as the script. Logs are rotated daily, and up to 14 days of logs are retained.

## Deployment
To run the script periodically, you can use a cron job. For example, to execute the script every hour:

1. Open the crontab editor:
    ```sh
    crontab -e
    ```

2. Add the following entry:
    ```sh
    */10 * * * * /path/to/ruuvitag_gateway.sh > /path/to/ruuvitag_gateway.log 2>&1
    ```

## License
This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.

## Acknowledgments
- RuuviTag Sensor Library for Bluetooth communication.
- InfluxDB for time-series data storage.
- ThingSpeak for IoT data visualization.