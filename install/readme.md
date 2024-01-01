1. sudo pip install flask flask_socketio flask_cors jsonpickle
2. comment out "localtest" line and uncomment the "server" line - its the last two lines of the app.py file
3. copy the service file to target machine and change paths
4. sudo systemctl daemon-reload
5. sudo systemctl enable multiplayer-game.service
6. sudo systemctl start multiplayer-game.service

To refresh the server data:
sudo systemctl stop multiplayer-game.service
git stash
git pull
nano app.py
[swap commenting of last lines], save, exit
sudo rm -r data
sudo systemctl start multiplayer-game.service
sudo systemctl status multiplayer-game.service
