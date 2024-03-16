from flask import Flask, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import app_config
from flask_session import Session
from flask_socketio import SocketIO
import identity

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'notVerySecret'
socketio = SocketIO(app, async_mode='threading')
CORS(app)
app.config.from_object(app_config)
Session(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
auth = identity.web.Auth(session=session, authority=app.config.get("AUTHORITY"), client_id=app.config["CLIENT_ID"], client_credential=app.config["CLIENT_SECRET"],)