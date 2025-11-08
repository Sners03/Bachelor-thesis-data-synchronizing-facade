from flask import Flask
import threading
import time

from src.application.interface.mqtt_manager import MqttManager
from src.domain.service.sensor_service import SensorService
from src.application.interface.rest import sensor_rest_interface

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

MqttManager.mqtt_init_app(app)
sensor_service = SensorService()
sensor_rest_interface.init_sensor_service(sensor_service)

app.register_blueprint(sensor_rest_interface.sensor_rest_interface)

def publish_message():
    """Publishes a message to the MQTT broker periodically."""
    msg_count = 1
    while True:
        try:
            MqttManager.mqtt.publish("test_2", f"lol {msg_count}")
            msg_count += 1
        except Exception as e:
            print(f"Error publishing message: {e}")
        time.sleep(5)  # Publish every 5 seconds


@MqttManager.mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected to broker")
    MqttManager.subscribe("test")

@MqttManager.mqtt.on_message()
def on_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    sensor_service.update_sensor("test", data)
    print('Received message on topic: {topic} with payload: {payload}'.format(**data))

# Create and start the background thread
publisher_thread = threading.Thread(target=publish_message)
publisher_thread.daemon = True  # Allow the thread to exit with the main program
publisher_thread.start()

if __name__ == '__main__':

    # flask-mqtt requires the no_reload parameter to be set to True
    app.run(host='0.0.0.0', port=5000, debug=False, no_reload=True)