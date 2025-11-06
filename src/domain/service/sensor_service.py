from typing import Dict
from src.domain.model.sensor import Sensor


class SensorService(object):
    _sensors:Dict[str,Sensor] = {}

    @staticmethod
    def create_sensor(lora_id) -> Sensor:
        return Sensor(lora_id=lora_id)

    def add_sensor(self, sensor:Sensor):
        self._sensors[sensor.lora_id] = sensor
        return self._sensors[sensor.lora_id]

    def add_sensor_by_id(self, lora_id):
        created_sensor = self.create_sensor(lora_id=lora_id)
        self._sensors[lora_id] = created_sensor
        return self._sensors[lora_id]

    def remove_sensor(self, lora_id):
        return self._sensors.pop(lora_id)

    # todo with receive + extrapolate
    def update_sensor(self, lora_id:str, received_data:object):
        pass

