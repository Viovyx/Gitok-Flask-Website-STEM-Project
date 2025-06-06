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
api_base_url = os.getenv('API_URL')

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
    return response if len(response) else False

def get_api_table(table):
    api_url = api_base_url + table
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        response = response.json()['records']
        return response
    else:
        return False

def get_api_data(table, key, value):
    api_url = api_base_url + f"{table}?filter={key},eq,{value}"
    response = requests.get(api_url, headers=headers)
    response = response.json()['records']
    return response

def post_api_data(table, data):
    api_url = api_base_url + table
    try:
        response = requests.post(api_url, data, headers=headers)
        return response
    except:
        return False

def put_api_data(table, id, data):
    api_url = api_base_url + f"{table}/{id}"
    try:
        response = requests.put(api_url, data, headers=headers)
        return response
    except:
        return False
    
def delete_api_data(table, id):
    api_url = api_base_url + f"{table}/{id}"
    response = requests.delete(api_url, headers=headers)
    return response

def reset_door_states():
    doors = get_api_data("devices", "Type", "lock")
    for door in doors:
        put_api_data("devices", door["id"], {"Status":0})

def post_log(description, user):
    log_obj = {
        "Description": description,
        "User": user,
        "Time": datetime.now(timezone.utc)
    }
    post_api_data("logs", log_obj)

def create_log_description(data):
    date = datetime.now(timezone.utc)
    user_id = data["user"]
    if user_id:
        user_info = get_api_data("users", "id", user_id)[0]
    else:
        user_info = {"FirstName":"Unknown", "LastName":"User"}
    
    door_info = get_api_data("devices", "IP", data["door_ip"])
    if len(door_info):
        door_info = door_info[0]
        scanner_info = [scanner for scanner in get_api_table("devices") if scanner["Type"] == "scanner" and scanner["Door_Id"] == door_info["id"]]
        if len(scanner_info):
            scanner_info = scanner_info[0]
        else:
            door_info = False
            scanner_info = False

    else:
        door_info = {"Name":"Unknown Door"}

    action_id = data["action"]
    action = ["failed", "successful", "checkout"][action_id]

    if door_info and scanner_info:
        description = f"Scan {action} for '{user_info['FirstName']} {user_info['LastName']}' for door '{door_info["Name"]}' with scanner '{scanner_info["Name"]}'."
    else:
        description = f"Scan {action}. Unknown Keycard or Scanner used."

    return description

def update_data(data, action):
    last_data = data[-1] if len(data) else {"id":-1,"Date":-1}
    id = last_data["id"]
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
    states = ["warning", "closed", "open"]
    doors_db = get_api_data("devices", "Type", "lock")
    doors = []
    for door in doors_db:
        users = get_api_data("users", "Current_Door", door["id"])
        door_obj = {
            "id":door["id"],
            "IP":door["IP"],
            "Name":door["Name"],
            "Status":states[door["Status"]],
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
    if not get_user_data(email):
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email == None:
        return

    if not get_user_data(email):
        return

    user = User()
    user.id = email
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/')


# ---------------
# Error Handling
# ---------------
@app.errorhandler(404)
def page_not_found(e):
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
    if not user_data:
        post_log(f"Login failed for '{email}'. No user found.", "Unknown User")
        return redirect('/?error=bad_login')

    if len(user_data) != 0:
        user_data = user_data[0]
        group_info = get_api_data("groups", "id", user_data["Group_id"])
        if group_info[0]["Admin"] == 1:
            if bcrypt.check_password_hash(user_data['Password'], request.form['password']):
                user = User()
                user.id = email
                flask_login.login_user(user)
                post_log(f"Login successful for '{user_data["FirstName"]} {user_data["LastName"]}'.", email)
                return redirect('/home')
            post_log(f"Login failed for '{user_data["FirstName"]} {user_data["LastName"]}'. Incorrect password.", email)
            return redirect('/?error=bad_login')
        post_log(f"Login failed for '{user_data["FirstName"]} {user_data["LastName"]}'. Not an admin.", email)
        return redirect('/?error=no_admin')


@app.route('/home', methods=['GET', 'POST'])
@flask_login.login_required
def home():
    if request.method == 'GET':
        user = get_user_data(flask_login.current_user.id)[0]
        devices=get_api_table("devices")

        return render_template('home.html', 
                                header=get_element("header"),
                                footer=get_element("footer"),
                                moon_toggle=get_element("moon-toggle"),
                                sun_toggle=get_element("sun-toggle"),
                                panel=get_element("panel"),
                                name=f"{user['FirstName']} {user['LastName']}",
                                keycards=get_api_table("cards"),
                                scanners=[scanner for scanner in devices if scanner["Type"] == "scanner"],
                                doors=[door for door in devices if door["Type"] == "lock"],
                                users=[{key: value for key, value in user.items() if key != "Password"} for user in get_api_table("users")],
                                groups=get_api_table("groups"))
    
    fields = request.form
    table = fields["table"]
    id = int(fields["id"])

    if fields["delete_input"] == "true":
        delete_api_data(fields["table"], id)
        post_log(f"Item deleted. Table: '{table}' - id: '{id}'", flask_login.current_user.id)
        return redirect("/home")
    else:
        data = {}
        with open("./static/js/panel_fields.json") as f:
            field_args = json.load(f)
        properties = [field_args[arg] for arg in field_args if field_args[arg]["table"] == table][0]

        for field in fields:
            if field not in ("delete_input", "action", "table", "id"):
                field_prop = properties[field]
                value = fields[field]
                
                if field_prop["index"] == "unique":
                    all_items = get_api_table(table)
                    for item in all_items:
                        if item[field] == value and item["id"] != id:
                            post_log(f"Item {"edit" if fields["action"] == "edit" else "create"} error. Duplicate key value. Table: '{table}' {("- id: '" + str(id) + "'") if id else ""}", flask_login.current_user.id)
                            return redirect('/home?error=duplicate_key')

                match field_prop["type"]:
                    case "checkbox":
                        print(value, type(value))
                        data[field] = 1 if fields.get(field) == "true" else 0
                    case "number":
                        data[field] = int(value)
                    case "select":
                        data[field] = int(value)
                    case "password":
                        data[field] = bcrypt.generate_password_hash(value)
                    case _:
                        data[field] = fields[field]
        
        if (put_api_data(table, id, data) if fields["action"] == "edit" else post_api_data(table, data)):
            print(data)
            post_log(f"Item {"edited" if fields["action"] == "edit" else "created"} successfully. Table: '{table}' {("- id: '" + str(id) + "'") if id else ""}", flask_login.current_user.id)
            return redirect("/home")
        else:
            post_log(f"Item {"edit" if fields["action"] == "edit" else "create"} error. Invalid value. Table: '{table}' {("- id: '" + str(id) + "'") if id else ""}", flask_login.current_user.id)
            return redirect("/home?error=invalid_field")

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

@app.route('/log', methods=['GET', 'POST'])
@flask_login.login_required
def log():
    logs = get_api_table("logs")[::-1]
    type_logs = logs
    user_logs = logs

    page = int(request.args.get("page", 1))
    shown = int(request.args.get("shown", 20))
    type = request.args.get("type", "All").strip('"')
    user = request.args.get("user", "All").strip('"')

    start = shown * (page-1)
    end = start + shown

    if type != "All":
        type_logs = [log for log in logs if log["Description"].split(" ")[0].lower() == type.lower()]
    if user != "All":
        user_logs = [log for log in logs if log["User"].lower() == user.lower()]

    users = list(set(log["User"] for log in type_logs))
    users.sort()
    types = list(set(log["Description"].split(" ")[0] for log in user_logs))
    types.sort()

    logs = [log for log in type_logs if log in user_logs][start:end]
    if not len(logs):
        return redirect("/log")
    
    return render_template('log.html',
                            header=get_element("header"),
                            footer=get_element("footer"),
                            moon_toggle=get_element("moon-toggle"),
                            sun_toggle=get_element("sun-toggle"),
                            logs=logs,
                            info={"page":page, "shown":shown, "type":type, "user":user, "users":users, "types":types})

@app.route('/account', methods=['GET', 'POST'])
@flask_login.login_required
def account():
    user_data = get_user_data(flask_login.current_user.id)[0]
    
    if request.method == 'GET':

        return render_template('account.html',
                                header=get_element("header"),
                                footer=get_element("footer"),
                                moon_toggle=get_element("moon-toggle"),
                                sun_toggle=get_element("sun-toggle"),
                                user = user_data)

    match request.args.get("action"):
        case "profile":
            if bcrypt.check_password_hash(user_data['Password'], request.form['password']):
                email = request.form["email"] if request.form["email"] else user_data["Email"]
                firstname = request.form["first-name"] if request.form["first-name"] else user_data["FirstName"]
                lastname = request.form["last-name"] if request.form["last-name"] else user_data["LastName"]

                put_api_data("users", user_data["id"], {"Email":email, "FirstName":firstname, "LastName":lastname})
                post_log(f"Profile info updated successfully for '{user_data["FirstName"]} {user_data["LastName"]}'.", email)
                return redirect("/account")
            else:
                post_log(f"Profile info update failed for '{user_data["FirstName"]} {user_data["LastName"]}'.", email)
                return redirect("/account?error=bad_pass")
        
        case "pass":
            if request.form["new-password"] != request.form["confirm-password"]:
                return redirect("/account?error=match_pass")
            if bcrypt.check_password_hash(user_data["Password"], request.form["current-password"]):
                flask_login.logout_user()
                pass_hash = bcrypt.generate_password_hash(request.form["new-password"])
                put_api_data("users", user_data["id"], {"Password":pass_hash})
                post_log(f"Profile password updated successfully for '{user_data["FirstName"]} {user_data["LastName"]}'.", user_data["Email"])
                return redirect("/")
            else:
                post_log(f"Profile password update failed for '{user_data["FirstName"]} {user_data["LastName"]}'.", user_data["Email"])
                return redirect("/account?error=bad_pass")


@app.route('/logout')
def logout():
    user_data = get_user_data(flask_login.current_user.id)[0]
    post_log(f"Logout successful for '{user_data["FirstName"]} {user_data["LastName"]}'.", user_data["Email"])
    flask_login.logout_user()
    return redirect('/')


# ------------------
# MQTT and SocketIO
# ------------------
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print('[MQTT] MQTT Connected')
    # Handle subscription here
    mqtt.subscribe("Tapgate/feeds/scanner.action")
    mqtt.subscribe("Tapgate/feeds/scanner.checkcard")
    mqtt.subscribe("Tapgate/feeds/scanner.setcardpass")
    mqtt.subscribe("Tapgate/feeds/lock.status")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print("[MQTT]", message.topic, message.payload.decode())
    # Handle received message here
    match message.topic:
        case "Tapgate/feeds/scanner.action":
            action_data = json.loads(message.payload.decode())  # {"user":1, "action":1, "door_ip":"192.168.0.11"}
            user_id = action_data["user"]
            action = action_data["action"]
            door_ip = action_data["door_ip"]

            email = "Unknown User"
            if user_id:
                user_info = get_api_data("users", "id", user_id)[0]
                email = user_info["Email"]
                new_door_id = get_api_data("devices", "IP", door_ip if action != 2 else 0)

                if len(new_door_id):
                    new_door_id = new_door_id[0]["id"]

                    if action != 0:
                        socketio.emit("updateDoorUser", {"user_id":user_id, "first_name":user_info["FirstName"], "last_name":user_info["LastName"], "new_door":new_door_id})
                        put_api_data("users", user_info["id"], {"Current_Door":new_door_id})
                        
                        # Open door
                        if action == 1:
                            open_feed = "Tapgate/feeds/lock.open"
                            mqtt.publish(open_feed, door_ip)

            log_description = create_log_description(action_data)
            post_log(log_description, email)

            data = get_api_table("data")
            update_data(data, action)

            socketio.emit("updateSensorGraph", {"value": action, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")})

        case "Tapgate/feeds/scanner.checkcard":
            data = json.loads(message.payload.decode())  # {"uid":"[255.255.255.255]", "pass":"DSQDad", "ip":"192.168.0.10"}

            card_uid = data["uid"].replace(".", ",")
            card_pass = data["pass"]
            card_info = get_api_data("cards", "CardUID", card_uid)

            scanner_ip = data["ip"]
            scanner = get_api_data("devices", "IP", scanner_ip)

            if len(scanner) and len(card_info):
                scanner = scanner[0]
                card_info = card_info[0]
                authenticated = card_pass == card_info["UniquePass"]

                user_info = get_api_data("users", "id", card_info["User_id"])
                if len(user_info):
                    user_info = user_info[0]

                door_info = door_info = get_api_data("devices", "id", scanner["Door_Id"])
                if len(door_info):
                    door_info = door_info[0]
            
            else:
                authenticated = False
                user_info = {"id":0}
                door_info = {"IP":0}

            action = 0
            if authenticated and user_info["id"] and door_info["IP"]:
                group_info = get_api_data("groups", "id", user_info["Group_id"])[0]

                admin = group_info["Admin"]
                access = group_info["Access"]

                if user_info["Current_Door"] != 1 or door_info["id"] == 1:  # User is still checked in or choose to checkout => check out
                    action = 2
                
                if user_info["Current_Door"] != scanner["Door_Id"] and door_info["id"] != 1:  # Make sure to not checkin to same door again and trying to checkout
                    action = 1 if admin or access >= door_info["Access"] else 0

            action_feed = "Tapgate/feeds/scanner.action"
            mqtt.publish(action_feed, str({"user":user_info["id"],"action":action,"door_ip":str(door_info["IP"])}).replace("'", '"'))


        case "Tapgate/feeds/scanner.setcardpass":
            data = json.loads(message.payload.decode())  # {"uid":"[255,255,255,255]", "pass":"DSQDad", "user":1}
            card_info = get_api_data("cards", "CardUID", data["uid"])

            if len(card_info):
                card_info = card_info[0]
                # Edit existing card pass
                put_api_data("cards", card_info["id"], {"UniquePass": data["pass"]})
            else:
                # Create new card
                user = get_api_data("users", "id", data["user"])

                if len(user):
                    card_obj = {
                        "CardUID": data["uid"],
                        "UniquePass": data["pass"],
                        "User_id": user[0]["id"]
                    }
                    post_api_data("cards", card_obj)

        case "Tapgate/feeds/lock.status":
            data = json.loads(message.payload.decode())  # {"status":0, "door_ip":"192.168.0.11"}
            door_info = get_api_data("devices", "IP", data["door_ip"])

            if len(door_info):
                door_info = door_info[0]
                socketio.emit("updateDoorState", {"door_id":door_info["id"], "status":data["status"]})
                put_api_data("devices", door_info["id"], {"Status":data["status"]})

        case _:
            print("[MQTT] Unknown message topic recieved: " + message.topic)

@socketio.on('connect')
def connect():
    print('[SocketIO] Client connected')


@socketio.on('disconnect')
def disconnect():
    print('[SocketIO] Client disconnected',  request.sid)

@socketio.on("getSelectItems")
def handle_get_select_items(data):
    table = data.get("table")
    index = data.get("index")

    try:
        match table:
            case "doors":
                items = [door for door in get_api_table("devices") if door["Type"] == "lock"]
            case _:
                items = get_api_table(table)
        if items:
            select_items = [{"id":item["id"], "value":item[index]} for item in items]
            socketio.emit("selectItemsResponse", {"items": select_items})
        else:
            raise Exception("Table not found.")
    except Exception as e:
        socketio.emit("selectItemsResponse", {"error": str(e)})

@socketio.on("openDoor")
def open_door(data):
    IP = data.get("IP")
    open_feed = "Tapgate/feeds/lock.open"
    mqtt.publish(open_feed, IP)

# --------
# Run App
# --------
if __name__ == "__main__":
    reset_door_states()
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=False)
