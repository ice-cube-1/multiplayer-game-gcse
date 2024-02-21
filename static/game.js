var canvas = document.getElementById("gameCanvas");
var infoCanvas = document.getElementById("infoCanvas");
var scale = 40
var ctx = canvas.getContext("2d");
var infoctx = infoCanvas.getContext('2d')
ctx.font = "15px Arial";
infoctx.font = '15px Arial'
ctx.textAlign = "center";
var socket = io.connect(document.location.protocol + '//' + document.domain + ':' + location.port);
var id;
var grid;
var playerpos;
var gridToRender = [];
var screensize = [20, 20];
var lastAttack = Date.now()
var playersinfo = [];
var ul = document.getElementById('messages');
var messageCount = 0;
var allies = []

socket.on('PlayersInfo', function (data) {
    console.log(id,'hi')
    // gets the info but doesn't do anything with it
    playersinfo = data
});
socket.on('specificPlayerInfo', function (data) {
    infoctx.clearRect(0, 0, infoCanvas.width, infoCanvas.height);
    for (let i = 0; i < playersinfo.length; i++) { // writes stuff on the leaderboard in the correct color
        infoctx.fillStyle = playersinfo[i][1];
        infoctx.fillText(playersinfo[i][0], 10, (i + 1) * 20)
    }
    info = data[id]
    infoctx.fillStyle = 'black'
    for (let i = 0; i < 2; i++) { // gives more specific info about the player
        info[i] = info[i].split('\n')
        for (var j = 0; j < info[i].length; j++) {
            infoctx.fillText(info[i][j], (i * 150) + 10, 600 + (j + 1) * 20)
        }
    }
    for (let i = 0; i < info[2].length; i++) { // adds images of equipped items
        var img = new Image();
        img.src = `static/items-images/${info[2][i]['type']}${info[2][i]['weapontype']}/${info[2][i]['rarity']}.png`;
        infoctx.drawImage(img, (i * 150) + 10, 700, 60, 60)
    }
});
var inputFocused = false;

function setInputFocus(isFocused) {
    // is the textbox in focus
    inputFocused = isFocused;
}

socket.on('message', function (msgs) {
    for (var i = 0; i < msgs.length; i++) { // displays the messages
        var msg = msgs[i]
        console.log(msg)
        var li = document.createElement('li');
        li.appendChild(document.createTextNode(msg[0]));
        li.style.color = msg[1];
        ul.appendChild(li)
        messageCount++;
        if (messageCount > 40) {
            var lastLi = ul.firstChild;
            ul.removeChild(lastLi);
            messageCount--;
        }
    }
});
document.getElementById('form').onsubmit = function () { // sends the messages
    var input = document.getElementById('input');
    socket.emit('message', [playerpos[id]['name'] + ': ' + input.value, playerpos[id]['color']]);
    input.value = '';
    return false;
};

socket.on('redirect', function (data) {
    window.location = data.url;
});

socket.on('allies',function (data) {
    allies=data
});

socket.on('base_grid', function (data) { // gets server updates
    grid = data
});
socket.on('item_positions', function (data) {
    items = data
});
socket.on('client_id', function (data) {
    id = data
    console.log('Your client ID is: ' + data);
});
socket.on('new_positions', function (data) {
    playerpos = data.objects;
    // works out where to draw the screen
    screenxoffset = playerpos[id]['x'] - screensize[0] / 2
    screenyoffset = playerpos[id]['y'] - screensize[1] / 2
    if (screenxoffset < 0) {
        screenxoffset = 0
    } else if (screenxoffset + screensize[0] >= grid[0].length) {
        screenxoffset = grid[0].length - screensize[0]
    }
    if (screenyoffset < 0) {
        screenyoffset = 0
    } else if (screenyoffset + screensize[1] >= grid.length) {
        screenyoffset = grid.length - screensize[1]
    }
    // sets rectangles representing walls / open ground
    for (let i = 0; i < screensize[1]; i++) {
        gridToRender[i] = [];
        for (let j = 0; j < screensize[0]; j++) {
            if (grid[i + screenyoffset][j + screenxoffset] == 0) {
                gridToRender[i][j] = "white";
            } else {
                gridToRender[i][j] = "black";
            }
        }
    }
    for (let i = 0; i < playerpos.length; i++) { // puts characters on the grid
        if ((0 <= playerpos[i]['x'] - screenxoffset && playerpos[i]['x'] - screenxoffset < screensize[0]) && (0 <= playerpos[i]['y'] - screenyoffset && playerpos[i]['y'] - screenyoffset < screensize[1]) && playerpos[i]['visible'] == true) {
            gridToRender[playerpos[i]['y'] - screenyoffset][playerpos[i]['x'] - screenxoffset] = playerpos[i]['color'];
        }
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < screensize[1]; i++) { // actually draws the rectangles
        for (var j = 0; j < screensize[0]; j++) {
            var x = j * scale;
            var y = i * scale;
            ctx.fillStyle = gridToRender[i][j];
            if (gridToRender[i][j] != 'black' && gridToRender[i][j] != 'white'){
                ctx.fillRect(x+(0.2*scale), y+(0.2*scale), scale*0.4, scale*0.6);
            } else {
                ctx.fillRect(x, y, scale, scale);
            }
        }
    }
    for (let i = 0; i < playerpos.length; i++) { // puts text on characters displaying HP
        if ((0 <= playerpos[i]['x'] - screenxoffset && playerpos[i]['x'] - screenxoffset < screensize[0]) && (0 <= playerpos[i]['y'] - screenyoffset && playerpos[i]['y'] - screenyoffset < screensize[1]) && playerpos[i]['visible'] == true) {
            var img = new Image();
            img.src = `static/items-images/other/character.png`;
            ctx.drawImage(img, (playerpos[i]['x'] - screenxoffset) * scale, (playerpos[i]['y'] - screenyoffset) * scale, scale*(13/18), scale);  
            if (playerpos[i]['armour'] != false) {
                var img = new Image();
                img.src = `static/items-images/armour/${playerpos[i]['armour']}.png`
                ctx.drawImage(img, (playerpos[i]['x'] - screenxoffset +(1/18)) * scale, (playerpos[i]['y'] - screenyoffset-(3/18)) * scale,scale*(15/18),scale*(15/18))
            }
            if (playerpos[i]['weapon'] != false) {
                var img = new Image();
                img.src = `static/items-images/weapon${playerpos[i]['weapon']}/${playerpos[i]['weaponrarity']}.png`;
                ctx.drawImage(img, (playerpos[i]['x'] - screenxoffset +(11/18)) * scale, (playerpos[i]['y'] - screenyoffset+(3/18)) * scale,scale*(10/18),scale*(10/18))
            }
            ctx.fillStyle = 'black';
            ctx.fillText(playerpos[i]['hp'], (playerpos[i]['x'] - screenxoffset + 0.85) * scale, (playerpos[i]['y'] - screenyoffset) * scale)
            console.log(allies,playerpos[i]['name'],playerpos[i]['name'] in allies)
            if (allies.includes(playerpos[i]['name'])) {
                console.log('ally detected')
                var img = new Image();
                img.src = `static/items-images/other/heart.png`;
                ctx.drawImage(img, (playerpos[i]['x'] - screenxoffset + 0.5) * scale, (playerpos[i]['y'] - screenyoffset + 0.5) * scale + 10,scale/2,scale/2)
            }
        }
    }
    for (let i = 0; i < items.length; i++) { // draws items
        if ((0 <= items[i]['x'] - screenxoffset && items[i]['x'] - screenxoffset < screensize[0]) && (0 <= items[i]['y'] - screenyoffset && items[i]['y'] - screenyoffset < screensize[1])) {
            var img = new Image();
            img.src = `static/items-images/${items[i]['type']}${items[i]['weapontype']}/${items[i]['rarity']}.png`;
            ctx.drawImage(img, (items[i]['x'] - screenxoffset) * scale, (items[i]['y'] - screenyoffset) * scale, scale, scale);
        }
    }
});
$(document).keydown(function (e) { // sends a movement to the server to be processed
    if (inputFocused) {
        return;
    }
    var direction = '';
    var currentTime = Date.now();
    switch (e.which) {
        case 87: direction = 'W'; break;
        case 65: direction = 'A'; break;
        case 83: direction = 'S'; break;
        case 68: direction = 'D'; break;
        case 69: direction = 'E'; break;
        case 32:
            if (currentTime - lastAttack < playerpos[id]['attackSpeed']) { return; }
            lastAttack = currentTime;
            direction = "Space";
            break;
        default: return;
    }
    socket.emit('update_position', { direction: direction, id: id });
});
