from flask import Response, render_template, request, redirect, url_for, session
from flask_socketio import join_room
from datetime import datetime
import identity
import app_config
from player import Player
import utils
import handle_socket
import setup
import vars
import zombify
import canrun
import reset

# gets globals and starts threads
global_vars = vars.GLOBAL()
setup.start(global_vars)
reset.start(global_vars)
zombify.start(global_vars)
canrun.start(global_vars)


@global_vars.APP.route("/login")
def login() -> str:
    """returns the login page - from here user can signin with microsoft, 
    if all is setup correctly they'll rarely see this page as it should auto-login"""
    return render_template("login.html", version=identity.__version__, **global_vars.AUTH.log_in(
        scopes=app_config.SCOPE,
        redirect_uri=url_for("auth_response", _external=True),
    ))


@global_vars.APP.route(app_config.REDIRECT_PATH)
def auth_response() -> Response:
    """gets user's name from their microsoft account and uses this as their name from here onwards"""
    global_vars.AUTH.complete_log_in(request.args)
    session['username'] = global_vars.AUTH.get_user().get('name')
    print(global_vars.AUTH.get_user().get('name'))
    return redirect(url_for("index"))


@global_vars.APP.route("/logout")
def logout() -> Response:
    """entirely managed by OAuth"""
    return redirect(global_vars.AUTH.log_out(url_for("index", _external=True)))


@global_vars.APP.route("/")
def index() -> str | Response:
    """If they are not logged in or it is during the times the game should be blocked it redirects 
    them to the login page, otherwise loads the game, creating a new player if nobody with their
    name is saved"""
    username = session.get('username', 'Guest')
    if not username or username == 'Guest':
        return redirect(url_for("login"))
    client_id = -1
    for i in range(len(global_vars.players)):
        if username == global_vars.players[i].name:
            client_id = i
    if client_id == -1:
        global_vars.players.append(Player(global_vars, username))
    session['ClientID'] = client_id
    utils.saveFiles(global_vars)
    if global_vars.can_run:
        return render_template('index.html')
    else:
        return render_template('login.html')


@global_vars.APP.route('/help')
def help_info() -> str:
    """Plain HTML page with info on how the game works - links back to the main site with a HREF"""
    return render_template('help.html')


@global_vars.SOCKETIO.on('connect')
def handle_connect() -> None:
    """emits everything the client needs and sends a message to everyone that they've joined, 
    plus some other information that would be useful for other players like new info"""
    global_vars.SOCKETIO.emit(
        'item_positions', [i.to_dict() for i in global_vars.items])
    client_id = session.get('ClientID', 'Guest')
    if global_vars.players[client_id].hp > 0:
        global_vars.players[client_id].visible = True
        global_vars.players[client_id].displayed_anywhere = True
    join_room(client_id)
    global_vars.SOCKETIO.emit('coin_positions', global_vars.coins)
    global_vars.SOCKETIO.emit('client_id', client_id,
                              room=client_id)
    global_vars.SOCKETIO.emit('base_grid', global_vars.grid)
    global_vars.SOCKETIO.emit('specificPlayerInfo', [
        i.getInfoForSpecificPlayer() for i in global_vars.players])
    global_vars.SOCKETIO.emit('PlayersInfo', sorted([i.getInfoInString(
    ) for i in global_vars.players if i.displayed_anywhere], key=lambda x: int(x[2]), reverse=True))
    global_vars.SOCKETIO.emit('new_positions', {"objects": [
        i.to_dict() for i in global_vars.players]})
    global_vars.SOCKETIO.emit('message', global_vars.messages[len(
        global_vars.messages)-40:], room=client_id)
    global_vars.SOCKETIO.emit(
        'allies', global_vars.players[client_id].ally, room=client_id)
    global_vars.messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}{global_vars.players[client_id].name} has joined', "black"])
    global_vars.SOCKETIO.emit('message', [global_vars.messages[-1]])


@global_vars.SOCKETIO.on('message')
def handle_message(msg: list[str]) -> None:
    """when a message is recieved - processing entirely controlled by another function"""
    handle_socket.message(global_vars, msg)


@global_vars.SOCKETIO.on('update_position')
def handle_update_position(data: dict[str, str | int]) -> None:
    """when W A S D E [space] is recieved - passes on the processing"""
    handle_socket.new_position(global_vars, data)


@global_vars.SOCKETIO.on('upgrade_weapon')
def handle_upgrade_weapon(data: list[int]) -> None:
    """On an upgrade weapon button press - just passes the signal"""
    handle_socket.weapon_upgrade(global_vars, data)


# actually runs the app
global_vars.SOCKETIO.run(global_vars.APP, debug=True, port='5000')  # LOCALTEST
# global_vars.SOCKETIO.run(global_vars.APP, debug=True,host='0.0.0.0',allow_unsafe_werkzeug=True, port=443, ssl_context=(app_config.FULL_CHAIN, app_config.PRIV_KEY)) # SERVER
