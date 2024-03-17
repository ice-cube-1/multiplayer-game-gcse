from flask import Response, render_template, request, redirect, url_for, session
from flask_socketio import join_room
from datetime import datetime
import identity
import app_config
from player import Player
import utils
import handle_socket
import setup  # SETS UP EVERYTHING SO DO NOT REMOVE
import vars
import zombify  # DO NOT REMOVE
import canrun  # DO NOT REMOVE
import reset  # UNUSED BUT REQUIRED AS STARTS THREADS

CONSTS = vars.consts()


@vars.APP.route("/login")
def login() -> str:
    return render_template("login.html", version=identity.__version__, **vars.AUTH.log_in(
        scopes=app_config.SCOPE,
        redirect_uri=url_for("auth_response", _external=True),
    ))


@vars.APP.route(app_config.REDIRECT_PATH)
def auth_response() -> Response:
    vars.AUTH.complete_log_in(request.args)
    session['username'] = vars.AUTH.get_user().get('name')
    print(vars.AUTH.get_user().get('name'))
    return redirect(url_for("index"))


@vars.APP.route("/logout")
def logout() -> Response:
    return redirect(vars.AUTH.log_out(url_for("index", _external=True)))


@vars.APP.route("/")
def index() -> str | Response:
    username = session.get('username', 'Guest')
    if not username or username == 'Guest':
        return redirect(url_for("login"))
    client_id = -1
    for i in range(len(vars.players)):
        if username == vars.players[i].name:
            client_id = i
    if client_id == -1:
        vars.players.append(Player(username))
    session['ClientID'] = client_id
    utils.saveFiles()
    if vars.can_run:
        return render_template('index.html')
    else:
        return render_template('login.html')


@vars.APP.route('/help')
def help_info() -> str:
    """just a plain HTML with an href"""
    return render_template('help.html')


@vars.SOCKETIO.on('connect')
def handle_connect() -> None:
    # emits everything the client needs and sends a message to everyone that they've joined
    vars.SOCKETIO.emit('item_positions', [i.to_dict() for i in vars.items])
    client_id = session.get('ClientID', 'Guest')
    if vars.players[client_id].hp > 0:
        vars.players[client_id].visible = True
        vars.players[client_id].displayed_anywhere = True
    join_room(client_id)
    vars.SOCKETIO.emit('coin_positions', vars.coins)
    vars.SOCKETIO.emit('client_id', client_id, room=client_id)  # SIMPLIFY the emits
    vars.SOCKETIO.emit('base_grid', vars.grid)
    vars.SOCKETIO.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in vars.players])
    vars.SOCKETIO.emit('PlayersInfo', sorted([i.getInfoInString(
    ) for i in vars.players if i.displayed_anywhere], key=lambda x: int(x[2]), reverse=True))
    vars.SOCKETIO.emit('new_positions', {"objects": [
                  i.to_dict() for i in vars.players]})
    vars.SOCKETIO.emit('message', vars.messages[len(
        vars.messages)-40:], room=client_id)
    vars.SOCKETIO.emit('allies', vars.players[client_id].ally, room=client_id)
    vars.messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}{vars.players[client_id].name} has joined', "black"])
    vars.SOCKETIO.emit('message', [vars.messages[-1]])


@vars.SOCKETIO.on('message')
def handle_message(msg: list[str]) -> None:
    handle_socket.message(msg)


@vars.SOCKETIO.on('update_position')
def handle_update_position(data: dict[str, str | int]) -> None:
    handle_socket.new_position(data)


@vars.SOCKETIO.on('upgrade_weapon')
def handle_upgrade_weapon(data: list[int]) -> None:
    handle_socket.weapon_upgrade(data)


vars.SOCKETIO.run(vars.APP, debug=True, port='5000')  # LOCALTEST
# vars.SOCKETIO.run(vars.APP, debug=True,host='0.0.0.0',allow_unsafe_werkzeug=True, port=443, ssl_context=(app_config.FULL_CHAIN, app_config.PRIV_KEY)) # SERVER
