from datetime import timedelta
from typing import Dict

import numpy as np
import pandas as pd

from src.domain.model.sensor import Sensor
from src.domain.model.sensor_state import SensorState
from src.domain.service.extrapolation_helper import ExtrapolationHelper


class SensorService(object):
    _sensors: Dict[bytes, Sensor] = {}

    def __init__(self):
        self._extrapolation_timespan = timedelta(seconds=600)

############# Sensor Management #################
    @staticmethod
    def create_sensor(lora_id) -> Sensor:
        return Sensor(device_address=lora_id)

    def remove_sensor(self, device_address_str: str):
        device_address = self.get_device_adress_from_string(device_address_str)
        return self._sensors.pop(device_address)

    def get_device_adress_from_string(self, device_address: str) -> bytes:
        return bytes.fromhex(device_address.replace("\\x", ""))

    def check_sensor_present(self, device_address:bytes):
        return device_address in self._sensors.keys()

    def add_sensor(self, sensor: Sensor):
        self._sensors[sensor.device_address] = sensor
        return self._sensors[sensor.device_address]

    def add_sensor_by_id(self, lora_id):
        created_sensor = self.create_sensor(lora_id=lora_id)
        self._sensors[lora_id] = created_sensor
        return self._sensors[lora_id]


###### Sensor Config ######
    def set_extrapolation_timespan(self, timespan_seconds: int):
        self._extrapolation_timespan = timedelta(seconds=timespan_seconds)

    def add_sensor_from_config(self, sensor_config: dict):
        device_address = self.get_device_adress_from_string(sensor_config["deviceAddress"])
        sensor = Sensor(device_address)
        sensor.last_values_buffer_size = sensor_config["real_datapoints_buffer_size"]
        sensor.fields = self.map_fields(sensor_config["fields"])
        sensor.expected_value_interval = pd.Timedelta(seconds=sensor_config["samplingRate_ms"]/1000.0)
        #sensor.expected_value_interval =  timedelta(milliseconds=sensor_config["samplingRate_ms"])
        return self.add_sensor(sensor)

    def update_sensor_from_config(self, sensor_config: dict):
        try:
            device_address = self.get_device_adress_from_string(sensor_config["deviceAddress"])
            if not self.check_sensor_present(device_address=device_address):
                self.add_sensor_from_config(sensor_config)
                return sensor_config
            self._sensors[device_address].last_values_buffer_size = sensor_config["real_datapoints_buffer_size"]
            self._sensors[device_address].fields = self.map_fields(sensor_config["fields"])
            self._sensors[device_address].expected_value_interval = pd.Timedelta(seconds=sensor_config["samplingRate_ms"] / 1000.0)
            return sensor_config
        except:
            raise Exception(f"sensor couldn't be updated: {sensor_config}")

    def update_sensor_from_config_field(self, device_address:str, config_field: str, config_value):
        try:
            device_address = bytes.fromhex(device_address.replace("\\x", ""))
            if not self.check_sensor_present(device_address=device_address):
                return False
            match config_field:
                case "real_datapoints_buffer_size":
                    self._sensors[device_address].last_values_buffer_size = config_value
                case "samplingRate_ms":
                    self._sensors[device_address].expected_value_interval = pd.Timedelta(seconds=config_value / 1000.0)
                case "fields":
                    self._sensors[device_address].fields = self.map_fields(config_value)
            return True
        except:
            return False


    def map_fields(self, fields):
        return {
            field["fieldName"]: {
                "datatype": field["datatype"],
                "start": field["start"],
                "end": field["end"]
            }
            for field in fields
        }

########### Data Update ##############
    def map_data(self, sensor, buffer):
        return_value = {}
        for field in sensor.fields:
            return_value[field] = self.map_datatype(buffer[sensor.fields[field]["start"]:sensor.fields[field]["end"]], sensor.fields[field]["datatype"])
        return return_value

    def _update_sensor_data(self, device_address, buffer):
        sensor = self._sensors[device_address]
        data = self.map_data(sensor, buffer)
        data["quality"] = SensorState.ACTIVE
        self._sensors[device_address].last_value = data

    def map_datatype(self, buffer:bytes, datatype:str):
        match datatype:
            case "int":
                return int.from_bytes(buffer)
            case "float":
                return np.frombuffer(buffer, dtype=np.float32)[0]
            case "double":
                return np.frombuffer(buffer, dtype=np.float64)[0]
            case "string":
                return str(buffer)
        return None

    def update_sensor(self, buffer:bytes):
        device_address = buffer[2:6]
        if not self.check_sensor_present(device_address=device_address):
            return
        self._update_sensor_data(device_address=device_address, buffer=buffer)

    def get_synchronized_sensors(self):
        synchronized_sensors = ExtrapolationHelper.synchronize_data(self._extrapolation_timespan, self._sensors)
        return synchronized_sensors
