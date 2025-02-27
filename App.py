import eventlet
eventlet.monkey_patch()
import os, flask_login, requests
from flask import Flask, render_template, request, redirect
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from datetime import datetime, timezone


# ---------------
# Setup & Config
# ---------------
app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = os.getenv('MQTT_BROKER_URL')
app.config['MQTT_BROKER_PORT'] = int(os.getenv('MQTT_BROKER_PORT'))
app.config['MQTT_USERNAME'] = os.getenv('MQTT_USERNAME')
app.config['MQTT_PASSWORD'] = os.getenv('MQTT_PASSWORD')
app.config['MQTT_KEEPALIVE'] = int(os.getenv('MQTT_KEEPALIVE'))
app.config['MQTT_TLS_ENABLED'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

headers = {"X-API-KEY":os.getenv('API_KEY')}
api_base_url = "https://api.tapgate.tech/api.php/records/"

mqtt = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins='*')

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


# ------------
# Flask Login
# ------------
class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    api_url = api_base_url + f"users?filter=Email,eq,{email}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']

    if len(response) == 0:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email == None:
        return

    api_url = api_base_url + f"users?filter=Email,eq,{email}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']

    if len(response) == 0:
        return

    user = User()
    user.id = email
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/')


# ----------
# Helper Functions
# ----------
def get_date():
    now = datetime.now(timezone.utc)
    return now.strftime("%m/%d/%Y %H:%M UTC")  # Remove time after testing!


# -------
# Routes
# -------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if flask_login.current_user.is_authenticated:
            return redirect('/home')
        return render_template('login.html')
    
    email = request.form['email']
    api_url = api_base_url + f"users?filter=Email,eq,{email}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']

    if len(response) != 0:
        if request.form['password'] == response[0]['Password']:
            user = User()
            user.id = email
            flask_login.login_user(user)
            return redirect('/home')

    return redirect('/?error=bad_login')

@app.route('/home')
@flask_login.login_required
def home():
    return render_template('home.html')

@app.route('/live-data')
@flask_login.login_required
def live_data():
    return render_template('live-data.html')

@app.route('/log')
@flask_login.login_required
def log():
    return render_template('log.html')

@app.route('/account', methods=['GET', 'POST'])
@flask_login.login_required
def account():
    return render_template('account.html')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')

# Needed to make loadElement.js work with flask
@app.route('/get_element/<element_id>')
def get_element(element_id):
    try:
        with open(f'templates/elements/{element_id}.html') as file:
            html_content = file.read()
        return html_content
    except FileNotFoundError:
        return f"Error: {element_id}.html not found", 404


# ------------------
# MQTT and SocketIO
# ------------------
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


# --------
# Run App
# --------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=False)
