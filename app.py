from flask import render_template, request, redirect, url_for, session
from flask_socketio import join_room
from datetime import datetime
import identity
import identity.web
import app_config
from player import Player
import global_vars
import utils
import handle_socket
import setup  # SETS UP EVERYTHING SO DO NOT REMOVE
from flasksetup import socketio, auth, app
import zombify  # DO NOT REMOVE
import canrun  # DO NOT REMOVE
import reset  # UNUSED BUT REQUIRED AS STARTS THREADS


@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE,
        redirect_uri=url_for("auth_response", _external=True),
    ))


@app.route(app_config.REDIRECT_PATH)
def auth_response():
    auth.complete_log_in(request.args)
    session['username'] = auth.get_user().get('name')
    print(auth.get_user().get('name'))
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))


@app.route("/")
def index():
    username = session.get('username', 'Guest')
    if not username or username == 'Guest':
        return redirect(url_for("login"))
    client_id = -1
    for i in range(len(global_vars.players)):
        if username == global_vars.players[i].name:
            client_id = i
    if client_id == -1:
        global_vars.players.append(Player(username))
    session['ClientID'] = client_id
    utils.saveFiles()
    if global_vars.can_run:
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/help')
def help_info():
    """just a plain HTML with an href"""
    return render_template('help.html')


@socketio.on('connect')
def handle_connect():
    # emits everything the client needs and sends a message to everyone that they've joined
    socketio.emit('item_positions', [i.to_dict() for i in global_vars.items])
    client_id = session.get('ClientID', 'Guest')
    if global_vars.players[client_id].hp > 0:
        global_vars.players[client_id].visible = True
        global_vars.players[client_id].displayed_anywhere = True
    join_room(client_id)
    socketio.emit('coin_positions', global_vars.coins)
    socketio.emit('client_id', client_id, room=client_id)  # SIMPLIFY the emits
    socketio.emit('base_grid', global_vars.grid)
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in global_vars.players])
    socketio.emit('PlayersInfo', sorted([i.getInfoInString(
    ) for i in global_vars.players if i.displayed_anywhere], key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [
                  i.to_dict() for i in global_vars.players]})
    socketio.emit('message', global_vars.messages[len(
        global_vars.messages)-40:], room=client_id)
    socketio.emit('allies', global_vars.players[client_id].ally, room=client_id)
    global_vars.messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}{global_vars.players[client_id].name} has joined', "black"])
    socketio.emit('message', [global_vars.messages[-1]])


@socketio.on('message')
def handle_message(msg):
    handle_socket.message(msg)


@socketio.on('update_position')
def handle_update_position(data):
    handle_socket.new_position(data)


@socketio.on('upgrade_weapon')
def handle_upgrade_weapon(data):
    handle_socket.weapon_upgrade(data)


socketio.run(app, debug=True, port='5000')  # LOCALTEST
# socketio.run(app, debug=True,host='0.0.0.0',allow_unsafe_werkzeug=True, port=443, ssl_context=(app_config.FULL_CHAIN, app_config.PRIV_KEY)) # SERVER
