import json
import os
from pathlib import Path

from flask import Flask
from jsonschema import validate, ValidationError
from src.domain.service.sensor_service import SensorService

from src.domain.model.sensor import Sensor


class ConfigService:
    def __init__(self):
        self._sensor_service = None
        self._config = {}
        self._config_path = Path(os.getcwd()).joinpath("config.json")
        self._sensor_config_path = Path(os.getcwd()).joinpath("sensor_config.json")
        self._sensor_config_schema_path = Path(os.getcwd()).joinpath("sensor_config.schema.json")
        self._sensor_config_data = {}
        self._sensor_config_schema = {}

    def init_app(self,app:Flask):
        print(self._config_path)
        app.config.from_file(self._config_path, load=json.load)
        print(app.config["MQTT_BROKER_URL"])
        return app

    def _create_sensors_from_config(self, config):
        print(config)
        for sensor in config["sensors"]:
            self._sensor_service.add_sensor_from_config(sensor)


    def load_sensors(self, sensor_service: SensorService):
        self._sensor_service = sensor_service
        self._load_sensor_config_schema()
        self._load_sensor_config()

    def _load_sensor_config(self):
        with open(self._sensor_config_path) as sensor_config_file:
            try:
                self.sensor_config_data = json.load(sensor_config_file)
                print(self.sensor_config_data)
                validate(self.sensor_config_data, self._sensor_config_schema)
                print(self.sensor_config_data)
                self._create_sensors_from_config(self.sensor_config_data)
            except ValidationError:
                self.sensor_config_data = {}
                print(
                    "json schema validation failed, please check your sensor_config.json to fit with the sensor_config.schema.json")
            except json.JSONDecodeError:
                self.sensor_config_data = {}
                print("decoding sensor_config json failed")
            except FileNotFoundError:
                self.sensor_config_data = {}
                print(f"Sensor config file not found at {self._sensor_config_path.absolute()}")

    def _load_sensor_config_schema(self):
        with open(self._sensor_config_schema_path) as schema_file:
            try:
                self._sensor_config_schema = json.load(schema_file)
            except json.JSONDecodeError:
                self._sensor_config_schema = {}





