import json
import os
from pathlib import Path

from flask import Flask
from jsonschema import validate

class ConfigService:
    #def validate(self, config):
    def __init__(self):
        self._config = {}
        self._config_path = Path(os.getcwd()).joinpath("config.json")

    def init_app(self,app:Flask):
        print(self._config_path)
        app.config.from_file(self._config_path, load=json.load)
        print(app.config["MQTT_BROKER_URL"])
        return app



