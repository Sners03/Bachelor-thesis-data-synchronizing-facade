from collections import deque
from dataclasses import dataclass, field
from typing import Any
import datetime

import pandas as pd

from src.domain.model.sensor_state import SensorState


@dataclass
class Sensor:
    """
    A Sensor Class containing
    """
    device_address:bytes
    _last_value:Any
    _last_changed_time:pd.Timestamp
    expected_value_interval:pd.Timedelta
    #_sensor_state:SensorState not needed in current implementation
    _last_values_queue:deque
    _last_values_buffer_size:int
    fields = []

    def __init__(self, device_address:bytes):
        """
        creates a Sensor object from just the required lora_id

        :param device_address: a string of the LoRa Id of the sender nodes device
        """
        self.device_address = device_address
        self._last_values_queue = deque(maxlen=100)

    @property
    def last_value(self):
        return self._last_value

    @last_value.setter
    def last_value(self, value:Any):
        current_time:pd.Timestamp = pd.Timestamp.now()
        value["receive_time"] = current_time
        self._last_value = value
        # add the last value to the queue
        self._last_values_queue.append(value)
        # update last changed time
        self._last_changed_time = current_time

    @property
    def last_values(self):
        return self._last_values_queue.copy()

    @property
    def last_values_buffer_size(self):
        return self._last_values_buffer_size

    @last_values_buffer_size.setter
    def last_values_buffer_size(self, size:int):
        self._last_values_buffer_size = size
        self._last_values_queue = deque(self._last_values_queue, maxlen=size)

    @property
    def last_changed_time(self):
        return self._last_changed_time



