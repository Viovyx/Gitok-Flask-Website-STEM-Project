import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request
from flask_mqtt import Mqtt
from flask_socketio import SocketIO


app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = 'io.adafruit.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'Tapgate'
app.config['MQTT_PASSWORD'] = 'aio_SVVQ61HhuAzANAn0gjaTixoF0KMy'
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['SECRET_KEY'] = 'secret!'
mqtt = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def homepage():
    return("Hello World")

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print('MQTT Connected')
    # Handle subscription here

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print(message.payload.decode())
    # Handle received message here

@socketio.on('connect')
def connect():
    print('Client connected')


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected',  request.sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=False)
