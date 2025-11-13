from collections import deque
from dataclasses import dataclass, field
from typing import Any
import datetime

from src.domain.model.sensor_state import SensorState


@dataclass
class Sensor:
    """
    A Sensor Class containing
    """
    lora_id:str
    _last_value:Any
    last_connected_time:datetime.datetime
    _last_changed_time:datetime.datetime
    expected_value_interval:datetime.timedelta
    _sensor_state:SensorState
    _last_values_queue:deque

    def __init__(self, lora_id:str):
        """
        creates a Sensor object from just the required lora_id

        :param lora_id: a string of the LoRa Id of the sender nodes device
        """
        self.lora_id = lora_id
        self._last_values_queue = deque(maxlen=5)

    @property
    def last_value(self):
        return self._last_value

    @last_value.setter
    def last_value(self, value:Any):
        self._last_value = value
        # add the last value to the queue
        self._last_values_queue.append(value)
        # update last changed time
        self._last_changed_time = datetime.datetime.now(datetime.timezone.utc)

    @property
    def last_values(self):
        return self._last_values_queue.copy()

    @property
    def last_changed_time(self):
        return self._last_changed_time



