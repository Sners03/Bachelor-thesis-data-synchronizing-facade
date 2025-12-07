from flask import Blueprint, jsonify, request
import re

from src.domain.service.config_service import ConfigService
config_service:ConfigService = None

def init_config_service(service: ConfigService):
    global config_service
    config_service = service


config_rest_interface = Blueprint('config_rest_interface', __name__)
device_address_pattern = re.compile(r'^[0-9a-fA-F]{8}$')

@config_rest_interface.route('/config/sensors', methods=['GET'])
def get_config():
    return jsonify(config_service.get_sensor_config())


@config_rest_interface.route('/config/sensors', methods=['POST'])
def post_config():
    try:
        config = request.json
        config_service.update_config(config)
        return {}, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@config_rest_interface.route('/config/sensors/<device_address>', methods=['POST'])
def post_config_by_device_address(device_address):
    try:
        if len(device_address) != 8:
            return jsonify({'error': "Device Address must be an Hex Code of length 8", "provided":device_address}), 400
        if not device_address_pattern.match(device_address):
            return jsonify({'error': "Device Address must be a valid Hex Code", "provided": device_address}), 400
        device_address = device_address.upper()
        device_address = '\\x' + '\\x'.join(device_address[i:i+2] for i in range(0, 8, 2))
        config = request.json
        updated_config = config_service.update_sensor_config_by_device_address(device_address, config)
        return jsonify(updated_config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@config_rest_interface.route('/config/sensors/<device_address>/<field>', methods=['POST'])
def post_config_by_field(device_address, field):
    try:
        if len(device_address) != 8:
            return jsonify({'error': "Device Address must be an Hex Code of length 8", "provided":device_address}), 400
        if not device_address_pattern.match(device_address):
            return jsonify({'error': "Device Address must be a valid Hex Code", "provided": device_address}), 400
        device_address = device_address.upper()
        device_address = '\\x' + '\\x'.join(device_address[i:i + 2] for i in range(0, 8, 2))
        config = request.json
        updated_config = config_service.update_sensor_config_field(device_address, field, config["value"])
        return jsonify(updated_config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
