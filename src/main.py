import struct

from flask import Flask
import threading
import time

from werkzeug.datastructures import Range

from src.application.interface.mqtt_manager import MqttManager
from src.domain.service.config_service import ConfigService
from src.domain.service.sensor_service import SensorService
from src.application.interface.rest import sensor_rest_interface
from src.lib.lora_packet_python.LoraPacket import LoraPacket

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

config_service = ConfigService()
app = config_service.init_app(app)

sensor_service = SensorService()
sensor_rest_interface.init_sensor_service(sensor_service)

config_service.load_sensors(sensor_service)

MqttManager.mqtt_init_app(app)

app.register_blueprint(sensor_rest_interface.sensor_rest_interface)

def map_message_hardcoded(message: bytes):
    dev_addr = message[2:6]
    ax = struct.unpack('f', message[11:15])
    ay = struct.unpack('f', message[15:19])
    az = struct.unpack('f', message[19:23])
    return dev_addr, ax, ay, az

def publish_message():
    """Publishes a message to the MQTT broker periodically."""
    msg_count = 1
    while True:
        try:
            #print(f"{app.config['TOPIC_PUBLISH']['NAME']}-{msg_count}")
            MqttManager.mqtt.publish(app.config["TOPIC_PUBLISH"]["NAME"], f"{msg_count}: {sensor_service.get_sensors()}\n")
            msg_count += 1
        except Exception as e:
            print(f"Error publishing message: {e}")
        time.sleep(app.config["TOPIC_PUBLISH"]["RATE_S"])  # Publish every 5 seconds


@MqttManager.mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected to broker")
    for topic in app.config["TOPIC_SUBSCRIBE"]:
        print(f"Subscribing to topic: {topic}")
        MqttManager.subscribe(topic)

@MqttManager.mqtt.on_message()
def on_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload
    )
    #mapped = map_message_hardcoded(data['payload'])
    #sensor_service.update_sensor(mapped[0], (mapped[1], mapped[2], mapped[3]))
    sensor_service.update_sensor(data['payload'])
    print('Received message on topic: {topic} with payload: {payload}'.format(**data))

# Create and start the background thread
publisher_thread = threading.Thread(target=publish_message)
publisher_thread.daemon = True  # Allow the thread to exit with the main program
publisher_thread.start()

if __name__ == '__main__':

    # flask-mqtt requires the no_reload parameter to be set to True
    app.run(host='0.0.0.0', port=5000, debug=False, no_reload=True)