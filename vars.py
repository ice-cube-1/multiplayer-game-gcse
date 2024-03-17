from flask import Flask, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import app_config
from flask_session import Session
from flask_socketio import SocketIO
import identity.web

class consts:
    def __init__(self) -> None:
        self.GRIX_X, self.GRID_Y = 80, 80
        self.RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        self.HEALING_STATS = [4, 6, 10, 16, 24]
        self.ARMOUR_STATS = [12, 14, 16, 19, 22]
        self.WEAPON_TYPES = {"/sword": [8, 1, 0.3], "/spear": [4, 2, 0.25], "/axe": [14, 1, 0.5], "/bow": [6, 5, 0.5]}
        self.WEAPON_MULTIPLIER = [1, 1.25, 1.5, 2, 3]
        self.UPGRADE_COSTS = {'common': 20, 'uncommon': 40, 'rare': 80, 'epic': 160, 'legendary': ''}

ally_groups, grid, messages, players, items, coins = [], [], [], [], [], []
can_run = True


APP = Flask('main', static_url_path='/static')
APP.secret_key = 'notVerySecret'
SOCKETIO = SocketIO(APP, async_mode='threading')
CORS(APP)
APP.config.from_object(app_config)
Session(APP)
APP.wsgi_app = ProxyFix(APP.wsgi_app, x_proto=1, x_host=1)
AUTH = identity.web.Auth(session=session, authority=APP.config.get("AUTHORITY"), client_id=APP.config["CLIENT_ID"], client_credential=APP.config["CLIENT_SECRET"],)

