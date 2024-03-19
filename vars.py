from flask import Flask, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import app_config
from flask_session import Session
from flask_socketio import SocketIO
import identity.web


GRID_X, GRID_Y = 80, 80
RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary']
HEALING_STATS = [4, 6, 10, 16, 24]
ARMOUR_STATS = [12, 14, 16, 19, 22]
WEAPON_TYPES = {"/sword": [8, 1, 0.3], "/spear": [4,
                                                  2, 0.25], "/axe": [14, 1, 0.5], "/bow": [6, 5, 0.5]}
WEAPON_MULTIPLIER = [1, 1.25, 1.5, 2, 3]
UPGRADE_COSTS = {'common': 20, 'uncommon': 40,
                 'rare': 80, 'epic': 160, 'legendary': ''}


class GLOBAL:
    def __init__(self) -> None:
        """all global variables and web-related stuff - socketio in here so can create multiple instances on different servers later possibly"""
        self.ally_groups, self.grid, self.messages, self.players, self.items, self.coins = [
        ], [], [], [], [], []
        self.can_run = True
        self.APP = Flask('main', static_url_path='/static')
        self.APP.secret_key = 'notVerySecret'
        self.SOCKETIO = SocketIO(self.APP, async_mode='threading')
        CORS(self.APP)
        self.APP.config.from_object(app_config)
        Session(self.APP)
        self.APP.wsgi_app = ProxyFix(self.APP.wsgi_app, x_proto=1, x_host=1)
        self.AUTH = identity.web.Auth(session=session, authority=self.APP.config.get(
            "AUTHORITY"), client_id=self.APP.config["CLIENT_ID"], client_credential=self.APP.config["CLIENT_SECRET"],)
