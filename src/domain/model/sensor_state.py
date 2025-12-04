from enum import Enum

class SensorState(Enum):
    ACTIVE = 0
    EXTRAPOLATED = 1
    INTERPOLATED = 2
    MISSING = 3

