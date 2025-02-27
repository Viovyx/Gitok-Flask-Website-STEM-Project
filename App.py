import eventlet, os
eventlet.monkey_patch()
from flask import Flask, render_template, request
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from datetime import datetime, timezone


app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = os.getenv('MQTT_BROKER_URL')
app.config['MQTT_BROKER_PORT'] = int(os.getenv('MQTT_BROKER_PORT'))
app.config['MQTT_USERNAME'] = os.getenv('MQTT_USERNAME')
app.config['MQTT_PASSWORD'] = os.getenv('MQTT_PASSWORD')
app.config['MQTT_KEEPALIVE'] = int(os.getenv('MQTT_KEEPALIVE'))
app.config['MQTT_TLS_ENABLED'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
mqtt = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins='*')

def get_date():
    now = datetime.now(timezone.utc)
    return now.strftime("%m/%d/%Y %H:%M UTC")  # Remove time after testing!

@app.route('/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/live-data')
def live_data():
    return render_template('live-data.html')

@app.route('/log')
def log():
    return render_template('log.html')

@app.route('/account', methods=['GET', 'POST'])
def account():
    return render_template('account.html')

# Needed to make loadElement.js work with flask
@app.route('/get_element/<element_id>')
def get_element(element_id):
    try:
        with open(f'templates/elements/{element_id}.html') as file:
            html_content = file.read()
        return html_content
    except FileNotFoundError:
        return f"Error: {element_id}.html not found", 404

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print('MQTT Connected')
    # Handle subscription here
    mqtt.subscribe("Tapgate/feeds/scanner.action")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print(message.topic, message.payload.decode())
    # Handle received message here
    if (message.topic == "Tapgate/feeds/scanner.action"):
        socketio.emit("updateSensorGraph", {"value": message.payload.decode(), "date": get_date()})

@socketio.on('connect')
def connect():
    print('Client connected')


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected',  request.sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=False)
