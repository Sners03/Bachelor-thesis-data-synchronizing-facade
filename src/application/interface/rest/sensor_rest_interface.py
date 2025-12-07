from flask import Blueprint, jsonify

from src.domain.service.sensor_service import SensorService

sensor_service:SensorService = None

def init_sensor_service(service: SensorService):
    global sensor_service
    sensor_service = service


sensor_rest_interface = Blueprint('sensor_rest_interface', __name__)


@sensor_rest_interface.route('/sensor', methods=['GET'])
def get_sensors():
    return jsonify(sensor_service.get_synchronized_sensors())