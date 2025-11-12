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

    def check_sensor_present(self, lora_id):
        return lora_id in self._sensors.keys()

    def _update_sensor_data(self, lora_id, data):
        self._sensors[lora_id].last_value = data

    # todo with receive + extrapolate
    def update_sensor(self, lora_id:str, received_data:object):
        if not self.check_sensor_present(lora_id=lora_id):
            self.add_sensor_by_id(lora_id=lora_id)
            self._update_sensor_data(lora_id=lora_id, data=received_data)

    def get_sensors(self):
        return [{lora_id:self._sensors[lora_id].last_value} for lora_id in self._sensors.keys()]

