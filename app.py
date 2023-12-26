from random import randint
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask_cors import CORS

gridlx = 80
gridly = 80
grid = [[0 for i in range(gridlx)] for j in range(gridly)]
for i in range(gridly):
    if i == 0 or i == gridly-1:
        grid[i] = [1 for i in range(gridlx)]
    else:
        grid[i][-1] = 1
        grid[i][0] = 1

def checkplayer(x,y):
    for i in players:
        if i.x == x and i.y == y:
            return False
    return True

class Player:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.color = [randint(0,255),randint(0,255),randint(0,255)]
    def move(self, charin):
        print(self.x,self.y)
        if charin == "W":
            if grid[self.y-1][self.x] == 0 and checkplayer(self.x,self.y-1):
                self.y-=1
        elif charin == "S":
            if grid[self.y+1][self.x] == 0 and checkplayer(self.x,self.y+1):
                self.y+=1
        elif charin == "A":
            if grid[self.y][self.x-1] == 0 and checkplayer(self.x-1,self.y):
                self.x-=1
        elif charin == "D":
            if grid[self.y][self.x+1] == 0 and checkplayer(self.x+1,self.y):
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
