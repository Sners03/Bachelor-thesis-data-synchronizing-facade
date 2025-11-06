from collections import deque
from dataclasses import dataclass
import typing
import datetime

from src.domain.model.sensor_state import SensorState


@dataclass
class Sensor:
    """
    A Sensor Class containing
    """
    lora_id:str
    _last_value:typing.Any
    last_connected_time:datetime.time
    last_changed_time:datetime.time
    expected_value_interval:datetime.timedelta
    _sensor_state:SensorState
    _last_values_queue:deque = deque(maxlen=5)

    def __init__(self, lora_id:str):
        """
        creates a Sensor object from just the required lora_id

        :param lora_id: a string of the LoRa Id of the sender nodes device
        """
        self.lora_id = lora_id

    @property
    def last_value(self):
        return self.last_value

    @last_value.setter
    def last_value(self, value:typing.Any):
        self._last_value = value
        # add the last value to the queue
        self._last_values_queue.append(value)

    @property
    def last_values(self):
        return self._last_values_queue.copy()



