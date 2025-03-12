import eventlet
eventlet.monkey_patch()
import os, flask_login, requests, json
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone


# ---------------
# Setup & Config
# ---------------
app = Flask(__name__)

load_dotenv()
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
bcrypt = Bcrypt(app)


# -----------------
# Helper Functions
# -----------------
def get_element(element_id):
    try:
        with open(f'templates/elements/{element_id}.html') as file:
            html_content = file.read()
        return html_content
    except FileNotFoundError:
        return f"Error: {element_id}.html not found", 404

def get_user_data(email):
    api_url = api_base_url + f"users?filter=Email,eq,{email}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']
    return response

def get_api_table(table):
    api_url = api_base_url + table
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']
    return response

def get_api_data(table, key, value):
    api_url = api_base_url + f"{table}?filter={key},eq,{value}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']
    return response

def post_api_data(table, data):
    api_url = api_base_url + table
    response = requests.post(api_url, data, headers=headers)
    return response

def put_api_data(table, id, data):
    api_url = api_base_url + f"{table}/{id}"
    response = requests.put(api_url, data, headers=headers)
    return response

def create_log_obj(data):
    date = datetime.now(timezone.utc)
    user_id = data["user"]
    if user_id != 0:
        user_info = get_api_data("users", "id", user_id)[0]
    else:
        user_info = {"FirstName":"Unknown", "LastName":"User"}
    
    action_id = data["action"]
    action = ["failed", "successful", "checkout"][action_id]

    log_obj = {
        "Action": action_id,
        "Description": f"Scan {action} for {user_info['FirstName']} {user_info['LastName']}",
        "Time": date
    }

    return log_obj

def update_data(data, log_obj):
    last_data = data[-1] if len(data) else {"id":-1,"Date":-1}
    id = last_data["id"]
    date = log_obj["Time"].strftime("%Y-%m-%d")
    action = log_obj["Action"]
    if last_data["Date"] == date:
        data_obj = {
            "Successful":last_data["Successful"]+1 if action else last_data["Successful"],
            "Failed":last_data["Failed"]+1 if not action else last_data["Failed"]
        }
        put_api_data("data", id, data_obj)
    else:
        data_obj = {
            "Date":date,
            "Successful":1 if action else 0,
            "Failed":1 if not action else 0
        }
        post_api_data("data", data_obj)

def getDoorsData():
    doors_db = get_api_data("devices", "Type", "lock")
    doors = []
    for door in doors_db:
        users = get_api_data("users", "Current_Door", door["id"])
        door_obj = {
            "id":door["id"],
            "Name":door["Name"],
            "Users":users
        }

        doors.append(door_obj)
    return doors


# ------------
# Flask Login
# ------------
class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if len(get_user_data(email)) == 0:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email == None:
        return

    if len(get_user_data(email)) == 0:
        return

    user = User()
    user.id = email
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/')


# -------
# Routes
# -------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if flask_login.current_user.is_authenticated:
            return redirect('/home')
        return render_template('login.html',
                                footer=get_element("footer"),
                                moon_toggle=get_element("moon-toggle"),
                                sun_toggle=get_element("sun-toggle"))
    
    email = request.form['email']
    user_data = get_user_data(email)

    if len(user_data) != 0:
        if bcrypt.check_password_hash(user_data[0]['Password'], request.form['password']):
            user = User()
            user.id = email
            flask_login.login_user(user)
            return redirect('/home')

    return redirect('/?error=bad_login')

@app.route('/home')
@flask_login.login_required
def home():
    user = get_user_data(flask_login.current_user.id)[0]
    return render_template('home.html', 
                            header=get_element("header"),
                            footer=get_element("footer"),
                            moon_toggle=get_element("moon-toggle"),
                            sun_toggle=get_element("sun-toggle"),
                            edit_panel=get_element("edit-panel"),
                            create_panel=get_element("create-panel"),
                            name=f"{user['FirstName']} {user['LastName']}",
                            keycards=get_api_table("cards"),
                            devices=get_api_table("devices"),
                            users=get_api_table("users"),
                            groups=get_api_table("groups"))

@app.route('/live-data')
@flask_login.login_required
def live_data():
    data = get_api_table("data")
    last_week_data = data[-7:]
    doors = getDoorsData()

    return render_template('live-data.html',
                            header=get_element("header"),
                            footer=get_element("footer"),
                            moon_toggle=get_element("moon-toggle"),
                            sun_toggle=get_element("sun-toggle"),
                            data=last_week_data,
                            doors=doors)

@app.route('/log')
@flask_login.login_required
def log():
    return render_template('log.html',
                            header=get_element("header"),
                            footer=get_element("footer"),
                            moon_toggle=get_element("moon-toggle"),
                            sun_toggle=get_element("sun-toggle"),
                            logs=get_api_table("logs")[::-1])

@app.route('/account', methods=['GET', 'POST'])
@flask_login.login_required
def account():
    return render_template('account.html',
                            header=get_element("header"),
                            footer=get_element("footer"),
                            moon_toggle=get_element("moon-toggle"),
                            sun_toggle=get_element("sun-toggle"))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')


# ------------------
# MQTT and SocketIO
# ------------------
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print('MQTT Connected')
    # Handle subscription here
    mqtt.subscribe("Tapgate/feeds/scanner.action")
    mqtt.subscribe("Tapgate/feeds/scanner.checkcard")
    mqtt.subscribe("Tapgate/feeds/scanner.setcardpass")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print(message.topic, message.payload.decode())
    # Handle received message here
    match message.topic:
        case "Tapgate/feeds/scanner.action":
            action_data = json.loads(message.payload.decode())  # {"user":1, "action":1}
            log_obj = create_log_obj(action_data)
            post_api_data("logs", log_obj)

            data = get_api_table("data")
            update_data(data, log_obj)

            action = log_obj["Action"]
            date = log_obj["Time"].strftime("%Y-%m-%d")
            socketio.emit("updateSensorGraph", {"value": action, "date": date})

        case "Tapgate/feeds/scanner.checkcard":
            action_feed = "Tapgate/feeds/scanner.action"
            data = json.loads(message.payload.decode())  # {"uid":"[255,255,255,255]", "pass":"DSQDad", "door":1}
            card_uid = data["uid"]
            card_pass = data["pass"]
            card_info = get_api_data("cards", "CardUID", card_uid)
            doors = get_api_data("devices", "Type", "lock")
            door = next((door_obj for door_obj in doors if door_obj["id"] == data["door"]), None)

            if len(card_info) > 0 and door != None:
                card_info = card_info[0]
                user_info = get_api_data("users", "id", card_info["User_id"])[0]
                group_info = get_api_data("groups", "id", user_info["Group_id"])[0]
                authenticated = card_pass == card_info["UniquePass"]
            else:
                authenticated = False
                user_info = {"id":0}
            
            action = 0
            if authenticated:
                admin = group_info["Admin"]
                access = group_info["Access"]

                if user_info["Current_Door"] != 1 or door["id"] == 1:  # User is still checked in or choose to checkout => check out
                    action = 2
                
                if user_info["Current_Door"] != data["door"] and door["id"] != 1:  # Make sure to not checkin to same door again and trying to checkout
                    if not admin:
                        if access >= door["Access"]:  # access allowed
                            action = 1
                        else:
                            action = 0
                    else:  # User is admin
                        action = 1

            if action == 1:
                put_api_data("users", user_info["id"], {"Current_Door":door["id"]})
            else:
                put_api_data("users", user_info["id"], {"Current_Door":1})

            mqtt.publish(action_feed, str({"user":user_info["id"],"action":action}).replace("'", '"'))

        case "Tapgate/feeds/scanner.setcardpass":
            data = json.loads(message.payload.decode())  # {"uid":"[255,255,255,255]", "pass":"DSQDad", "user":1}
            card_info = get_api_data("cards", "CardUID", data["uid"])

            if len(card_info) > 0 and card_info[0]["CardUID"] == data["uid"]:
                card_info = card_info[0]
                # Edit existing card pass
                put_api_data("cards", card_info["id"], {"UniquePass": data["pass"]})
            else:
                # Create new card
                card_obj = {
                    "CardUID": data["uid"],
                    "UniquePass": data["pass"],
                    "User_id": data["user"]
                }
                post_api_data("cards", card_obj)

        case _:
            print("[MQTT] Unknown message topic recieved: " + message.topic)

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
