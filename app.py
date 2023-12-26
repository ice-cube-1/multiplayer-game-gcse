from random import randint
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask_cors import CORS

gridlx = 16
gridly = 16
grid = [[0 for i in range(gridlx)] for j in range(gridly)]

class Player:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.color = [randint(0,255),randint(0,255),randint(0,255)]
    def move(self, charin):
        if charin == "W":
            self.y+=1
        elif charin == "S":
            self.y-=1
        elif charin == "A":
            self.x-=1
        elif charin == "D":
            self.x+=1
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color
        }

players = []


app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global players
    players.append(Player(randint(0,gridlx-1),randint(0,gridly-1)))
    client_id = len(players)-1
    join_room(client_id)
    socketio.emit('client_id', client_id, room=client_id)
    socketio.emit('base_grid', grid)
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})


@socketio.on('update_position')
def handle_update_position(data):
    players[data['id']].move(data['direction'])
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})
    

if __name__ == '__main__':
    socketio.run(app, debug=True)
