import time

from flask import Flask
from flask_mqtt import Mqtt

mqtt = Mqtt()

def init_app(app):
    mqtt.init_app(app)

    @mqtt.on_connect()
    def on_connect(client, userdata, flags, rc):
        print("Connected to broker")
        MqttManager.subscribe("test")

    @mqtt.on_message()
    def on_message(client, userdata, message):
        data = dict(
            topic=message.topic,
            payload=message.payload.decode()
        )

        print('Received message on topic: {topic} with payload: {payload}'.format(**data))

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

class MqttManager():
    """
    wrapper class for flask mqtt
    """
    topic_list: list[str] = []
    mqtt = Mqtt()

    @staticmethod
    def mqtt_init_app(app: Flask):
        MqttManager.mqtt.init_app(app)

    @staticmethod
    def subscribe(topic: str):
        MqttManager.topic_list.append(topic)
        MqttManager.mqtt.subscribe(topic)

    @staticmethod
    def unsubscribe(topic: str):
        MqttManager.topic_list.remove(topic)
        MqttManager.mqtt.unsubscribe(topic)

    @staticmethod
    def subscribe_to_all(topic_list:list[str]):
        [MqttManager.subscribe(topic) for topic in topic_list]








