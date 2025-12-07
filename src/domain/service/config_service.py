import json
import os
from pathlib import Path

from flask import Flask
from jsonschema import validate, ValidationError

from src.domain.service.sensor_service import SensorService


class ConfigService:
    def __init__(self):
        self._sensor_service:SensorService|None = None
        self._config = {}
        self._config_path = Path(os.getcwd()).joinpath("config.json")
        self._sensor_config_path = Path(os.getcwd()).joinpath("sensor_config.json")
        self._sensor_config_schema_path = Path(os.getcwd()).joinpath("sensor_config.schema.json")
        self._sensor_config_data = {}
        self._sensor_config_schema = {}

    def init_app(self, app: Flask):
        app.config.from_file(self._config_path, load=json.load)
        print(app.config["MQTT_BROKER_URL"])
        return app

    def _create_sensors_from_config(self, config):
        for sensor in config["sensors"]:
            self._sensor_service.add_sensor_from_config(sensor)

    def load_sensors(self, sensor_service: SensorService):
        self._sensor_service = sensor_service
        self._load_sensor_config_schema()
        self._load_sensor_config()

    def get_config_index_by_device_address(self, device_address: str):
        sensor_config = self.get_sensor_config()
        for index, sensor in enumerate(sensor_config["sensors"]):
            if sensor["deviceAddress"] == device_address:
                return index
        else:
            raise Exception("Sensor can't be found")

    def _load_sensor_config(self):
        with open(self._sensor_config_path) as sensor_config_file:
            try:
                self._sensor_config_data = json.load(sensor_config_file)
                validate(self._sensor_config_data, self._sensor_config_schema)
                self._create_sensors_from_config(self._sensor_config_data)
            except ValidationError:
                self._sensor_config_data = {}
                print(
                    "json schema validation failed, please check your sensor_config.json to fit with the sensor_config.schema.json")
            except json.JSONDecodeError:
                self._sensor_config_data = {}
                print("decoding sensor_config json failed")
            except FileNotFoundError:
                self._sensor_config_data = {}
                print(f"Sensor config file not found at {self._sensor_config_path.absolute()}")

    def _load_sensor_config_schema(self):
        with open(self._sensor_config_schema_path) as schema_file:
            try:
                self._sensor_config_schema = json.load(schema_file)
            except json.JSONDecodeError:
                self._sensor_config_schema = {}

    def get_sensor_config(self):
        return self._sensor_config_data.copy()

    def add_sensor_config(self, device_address: str, config: dict):
        sensor_config = self.get_sensor_config()
        if self.is_sensor_configured(device_address):
            return False
        sensor_config["sensors"].append(config)
        validate(sensor_config, self._sensor_config_schema)
        self._sensor_service.add_sensor_from_config(config)
        self._set_config_data(sensor_config)
        return True

    def remove_config_by_device_address(self, device_address: str):
        sensor_config = self.get_sensor_config()
        if not self.is_sensor_configured(device_address):
            return {}
        index = self.get_config_index_by_device_address(device_address)
        deleted_config = sensor_config["sensors"].pop(index, None)
        validate(sensor_config, self._sensor_config_schema)
        self._sensor_service.remove_sensor(device_address)
        self._set_config_data(sensor_config)
        return deleted_config

    def update_sensor_config_by_device_address(self, device_address: str, config: dict):
        sensor_config = self.get_sensor_config()
        if not self.is_sensor_configured(device_address):
            raise Exception("Sensor not configured")
        index = self.get_config_index_by_device_address(device_address)
        sensor_config["sensors"][index] = config
        validate(sensor_config, self._sensor_config_schema)
        self._sensor_service.update_sensor_from_config(config)
        return self._set_config_data(sensor_config)

    def update_sensor_config_field(self, device_address: str, field: str, value):
        sensor_config = self.get_sensor_config()
        if not self.is_sensor_configured(device_address):
            return False
        index = self.get_config_index_by_device_address(device_address)
        sensor_config["sensors"][index][field] = value
        validate(sensor_config, self._sensor_config_schema)
        if self._sensor_service.update_sensor_from_config_field(device_address, field, value):
            self._set_config_data(sensor_config)
            return True
        return False

    def is_sensor_configured(self, device_address: str):
        return bool([sensor_config for sensor_config in self.get_sensor_config()["sensors"] if
                     device_address == sensor_config["deviceAddress"]])

    def update_config(self, config):
        validate(config, self._sensor_config_schema)
        for sensor_config in config["sensors"]:
            self._sensor_service.update_sensor_from_config(sensor_config)
        self._set_config_data(config)

    def _set_config_data(self, config):
        validate(config, self._sensor_config_schema)
        self._sensor_config_data = config
        with open(self._sensor_config_path, "w") as sensor_config_file:
            json.dump(config, sensor_config_file)
