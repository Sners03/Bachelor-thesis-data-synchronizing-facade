from datetime import timedelta
from typing import Dict
from unittest import case

import numpy as np
import pandas as pd

from src.domain.model.sensor import Sensor
from src.domain.model.sensor_state import SensorState
from src.domain.service.extrapolation_helper import ExtrapolationHelper


class SensorService(object):
    _sensors: Dict[bytes, Sensor] = {}

    def __init__(self):
        self._extrapolation_helper = ExtrapolationHelper()

    @staticmethod
    def create_sensor(lora_id) -> Sensor:
        return Sensor(device_address=lora_id)

    def add_sensor(self, sensor: Sensor):
        self._sensors[sensor.device_address] = sensor
        return self._sensors[sensor.device_address]

    def add_sensor_from_config(self, sensor_config: dict):
        device_address = bytes.fromhex(sensor_config["deviceAddress"].replace("\\x", ""))
        sensor = Sensor(device_address)
        sensor.fields = self.map_fields(sensor_config["fields"])
        sensor.expected_value_interval = pd.Timedelta(seconds=sensor_config["samplingRate_ms"]/1000.0)
        #sensor.expected_value_interval =  timedelta(milliseconds=sensor_config["samplingRate_ms"])
        return self.add_sensor(sensor)

    def map_fields(self, fields):
        return {
            field["fieldName"]: {
                "datatype": field["datatype"],
                "start": field["start"],
                "end": field["end"]
            }
            for field in fields
        }

    def add_sensor_by_id(self, lora_id):
        created_sensor = self.create_sensor(lora_id=lora_id)
        self._sensors[lora_id] = created_sensor
        return self._sensors[lora_id]

    def remove_sensor(self, lora_id):
        return self._sensors.pop(lora_id)

    def check_sensor_present(self, device_address:bytes):
        return device_address in self._sensors.keys()

    def _update_sensor_data(self, device_address, buffer):
        sensor = self._sensors[device_address]
        data = self.map_data(sensor, buffer)
        data["quality"] = SensorState.ACTIVE
        self._sensors[device_address].last_value = data

    def map_data(self, sensor, buffer):
        return_value = {}
        for field in sensor.fields:
            return_value[field] = self.map_datatype(buffer[sensor.fields[field]["start"]:sensor.fields[field]["end"]], sensor.fields[field]["datatype"])
        return return_value

    def map_datatype(self, buffer:bytes, datatype:str):
        match datatype:
            case "int":
                return int(buffer)
            case "float":
                return np.frombuffer(buffer, dtype=np.float32)[0]
            case "double":
                return np.frombuffer(buffer, dtype=np.float64)[0]
            case "string":
                return str(buffer)
        return None



    # todo with  extrapolate
    def update_sensor(self, buffer:bytes):
        device_address = buffer[2:6]
        if not self.check_sensor_present(device_address=device_address):
            return
        self._update_sensor_data(device_address=device_address, buffer=buffer)

    def get_sensors(self):
        print(self._extrapolation_helper.synchronize_data(timedelta(minutes=5), self._sensors))
        return [{lora_id: self._sensors[lora_id].last_value} for lora_id in self._sensors.keys()]
