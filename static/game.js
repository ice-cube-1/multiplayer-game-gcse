var canvas = document.getElementById("gameCanvas");
var infoCanvas = document.getElementById("infoCanvas");
var scale = 40
var ctx = canvas.getContext("2d");
var info_ctx = infoCanvas.getContext('2d')
ctx.font = "15px Arial";
info_ctx.font = '15px Arial'
ctx.textAlign = "center";
var socket = io.connect(document.location.protocol + '//' + document.domain + ':' + location.port);
var id;
var grid;
var player_pos;
var gridToRender = [];
var screensize = [20, 20];
var lastAttack = Date.now()
var players_info = [];
var ul = document.getElementById('messages');
var messageCount = 0;
var allies = []
var coins = []
var preloaded = {}

document.getElementById('Upgrade1').onclick = function () { // sends the messages
    console.log(0,'help test')
    socket.emit('upgrade_weapon',[0,id])
}
document.getElementById('Upgrade2').onclick = function () { // sends the messages
    console.log(1,'help test')
    socket.emit('upgrade_weapon',[1,id])
}
socket.on('players_info', function (data) {
    console.log(id,'hi')
    // gets the info but doesn't do anything with it
    players_info = data
});
socket.on('specificPlayerInfo', function (data) {
    info_ctx.clearRect(0, 0, infoCanvas.width, infoCanvas.height);
    for (let i = 0; i < players_info.length; i++) { // writes stuff on the leaderboard in the correct color
        info_ctx.fillStyle = players_info[i][1];
        info_ctx.fillText(players_info[i][0], 10, (i + 1) * 20)
    }
    info = data[id]
    info_ctx.fillStyle = 'black'
    for (let i = 0; i < 2; i++) { // gives more specific info about the player
        info[i] = info[i].split('\n')
        for (var j = 0; j < info[i].length; j++) {
            info_ctx.fillText(info[i][j], (i * 200) + 10, 570 + (j + 1) * 20)
        }
    }
    for (let i = 0; i < info[2].length; i++) { // adds images of equipped items
        if (!(`static/items-images/${info[2][i]['type']}${info[2][i]['weapon_type']}/${info[2][i]['rarity']}.png` in preloaded)) {
            preloaded[`static/items-images/${info[2][i]['type']}${info[2][i]['weapon_type']}/${info[2][i]['rarity']}.png`] = new Image()
            preloaded[`static/items-images/${info[2][i]['type']}${info[2][i]['weapon_type']}/${info[2][i]['rarity']}.png`].src = `static/items-images/${info[2][i]['type']}${info[2][i]['weapon_type']}/${info[2][i]['rarity']}.png`
        }
        info_ctx.drawImage(preloaded[`static/items-images/${info[2][i]['type']}${info[2][i]['weapon_type']}/${info[2][i]['rarity']}.png`], (i * 200) + 10, 700, 60, 60)
    }
});
var inputFocused = false;

function setInputFocus(isFocused) {
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
    socket.emit('message', [player_pos[id]['name'] + ': ' + input.value, player_pos[id]['color']]);
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
socket.on('coin_positions',function (data) {
    coins=data
});

socket.on('client_id', function (data) {
    id = data
});

socket.on('new_positions', function (data) {
    player_pos = data.objects;
    // works out where to draw the screen
    screen_x_offset = player_pos[id]['x'] - screensize[0] / 2
    screen_y_offset = player_pos[id]['y'] - screensize[1] / 2
    if (screen_x_offset < 0) {
        screen_x_offset = 0
    } else if (screen_x_offset + screensize[0] >= grid[0].length) {
        screen_x_offset = grid[0].length - screensize[0]
    }
    if (screen_y_offset < 0) {
        screen_y_offset = 0
    } else if (screen_y_offset + screensize[1] >= grid.length) {
        screen_y_offset = grid.length - screensize[1]
    }
    // sets rectangles representing walls / open ground
    for (let i = 0; i < screensize[1]; i++) {
        gridToRender[i] = [];
        for (let j = 0; j < screensize[0]; j++) {
            if (grid[i + screen_y_offset][j + screen_x_offset] == 0) {
                gridToRender[i][j] = "white";
            } else {
                gridToRender[i][j] = "black";
            }
        }
    }
    for (let i = 0; i < player_pos.length; i++) { // puts characters on the grid
        if ((0 <= player_pos[i]['x'] - screen_x_offset && player_pos[i]['x'] - screen_x_offset < screensize[0]) && (0 <= player_pos[i]['y'] - screen_y_offset && player_pos[i]['y'] - screen_y_offset < screensize[1]) && player_pos[i]['visible'] == true) {
            gridToRender[player_pos[i]['y'] - screen_y_offset][player_pos[i]['x'] - screen_x_offset] = player_pos[i]['color'];
        }
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < screensize[1]; i++) { // actually draws the rectangles
        for (var j = 0; j < screensize[0]; j++) {
            var x = j * scale;
            var y = i * scale;
            ctx.fillStyle = gridToRender[i][j];
            if (gridToRender[i][j] != 'black') {
                if (!('static/items-images/other/floor.png' in preloaded)) {
                    preloaded['static/items-images/other/floor.png'] = new Image()
                    preloaded['static/items-images/other/floor.png'].src = 'static/items-images/other/floor.png'  
                }              
                ctx.drawImage(preloaded['static/items-images/other/floor.png'], x, y, scale, scale);
            } else {
                if (!('static/items-images/other/bricks.png' in preloaded)) {
                    preloaded['static/items-images/other/bricks.png'] = new Image()
                    preloaded['static/items-images/other/bricks.png'].src = 'static/items-images/other/bricks.png'  
                }              
                ctx.drawImage(preloaded['static/items-images/other/bricks.png'], x, y, scale, scale); 
            }
            if (gridToRender[i][j] != 'black' && gridToRender[i][j] != 'white'){
                ctx.fillRect(x+(0.2*scale), y+(0.2*scale), scale*0.4, scale*0.6);
            } 
        }
    }
    for (let i = 0; i < player_pos.length; i++) { // puts text on characters displaying HP
        if ((0 <= player_pos[i]['x'] - screen_x_offset && player_pos[i]['x'] - screen_x_offset < screensize[0]) && (0 <= player_pos[i]['y'] - screen_y_offset && player_pos[i]['y'] - screen_y_offset < screensize[1]) && player_pos[i]['visible'] == true) {
            if (!(`static/items-images/other/character.png` in preloaded)) {
                preloaded[`static/items-images/other/character.png`] = new Image()
                preloaded[`static/items-images/other/character.png`].src = `static/items-images/other/character.png`  
            }              
            ctx.drawImage(preloaded[`static/items-images/other/character.png`], (player_pos[i]['x'] - screen_x_offset) * scale, (player_pos[i]['y'] - screen_y_offset) * scale, scale*(13/18), scale);  
            if (player_pos[i]['armour'] != false) {
                if (!(`static/items-images/armour/${player_pos[i]['armour']}.png` in preloaded)) {
                    preloaded[`static/items-images/armour/${player_pos[i]['armour']}.png`] = new Image()
                    preloaded[`static/items-images/armour/${player_pos[i]['armour']}.png`].src =`static/items-images/armour/${player_pos[i]['armour']}.png`  
                }  
                ctx.drawImage(preloaded[`static/items-images/armour/${player_pos[i]['armour']}.png`], (player_pos[i]['x'] - screen_x_offset +(1/18)) * scale, (player_pos[i]['y'] - screen_y_offset-(3/18)) * scale,scale*(15/18),scale*(15/18))
            }
            if (player_pos[i]['weapon'] != false) {
                if (!(`static/items-images/weapon${player_pos[i]['weapon']}/${player_pos[i]['weapon_rarity']}.png` in preloaded)) {
                    preloaded[`static/items-images/weapon${player_pos[i]['weapon']}/${player_pos[i]['weapon_rarity']}.png`] = new Image()
                    preloaded[`static/items-images/weapon${player_pos[i]['weapon']}/${player_pos[i]['weapon_rarity']}.png`].src = `static/items-images/weapon${player_pos[i]['weapon']}/${player_pos[i]['weapon_rarity']}.png`  
                }              
                ctx.drawImage(preloaded[`static/items-images/weapon${player_pos[i]['weapon']}/${player_pos[i]['weapon_rarity']}.png`], (player_pos[i]['x'] - screen_x_offset +(11/18)) * scale, (player_pos[i]['y'] - screen_y_offset+(3/18)) * scale,scale*(10/18),scale*(10/18))
            }
            ctx.fillStyle = 'black';
            ctx.fillText(player_pos[i]['hp'], (player_pos[i]['x'] - screen_x_offset + 0.85) * scale, (player_pos[i]['y'] - screen_y_offset) * scale)
            if (allies.includes(player_pos[i]['name'])) {
                var img = new Image();
                img.src = `static/items-images/other/heart.png`;
                if (!(`static/items-images/other/heart.png` in preloaded)) {
                    preloaded[`static/items-images/other/heart.png`] = new Image()
                    preloaded[`static/items-images/other/heart.png`].src = `static/items-images/other/heart.png`
                }                  
                ctx.drawImage(preloaded[`static/items-images/other/heart.png`], (player_pos[i]['x'] - screen_x_offset + 0.5) * scale, (player_pos[i]['y'] - screen_y_offset + 0.5) * scale + 10,scale/2,scale/2)
            }
        }
    }
    for (let i = 0; i < items.length; i++) { // draws items
        if ((0 <= items[i]['x'] - screen_x_offset && items[i]['x'] - screen_x_offset < screensize[0]) && (0 <= items[i]['y'] - screen_y_offset && items[i]['y'] - screen_y_offset < screensize[1])) {
            if (!(`static/items-images/${items[i]['type']}${items[i]['weapon_type']}/${items[i]['rarity']}.png` in preloaded)) {
                preloaded[`static/items-images/${items[i]['type']}${items[i]['weapon_type']}/${items[i]['rarity']}.png`] = new Image()
                preloaded[`static/items-images/${items[i]['type']}${items[i]['weapon_type']}/${items[i]['rarity']}.png`].src = `static/items-images/${items[i]['type']}${items[i]['weapon_type']}/${items[i]['rarity']}.png`
            }              
            ctx.drawImage(preloaded[`static/items-images/${items[i]['type']}${items[i]['weapon_type']}/${items[i]['rarity']}.png`], (items[i]['x'] - screen_x_offset) * scale, (items[i]['y'] - screen_y_offset) * scale, scale, scale);
        }
    }
    if (!(`static/items-images/other/coin.png` in preloaded)) {
        preloaded[`static/items-images/other/coin.png`] = new Image()
        preloaded[`static/items-images/other/coin.png`].src = `static/items-images/other/coin.png`
    }   
    for (let i=0; i<coins.length; i++) {
        if ((0 <= coins[i]['x'] - screen_x_offset && coins[i]['x'] - screen_x_offset < screensize[0]) && (0 <= coins[i]['y'] - screen_y_offset && coins[i]['y'] - screen_y_offset < screensize[1])) {
            ctx.drawImage(preloaded[`static/items-images/other/coin.png`], (coins[i]['x'] - screen_x_offset+0.25) * scale, (coins[i]['y'] - screen_y_offset+0.25) * scale, scale/2, scale/2);
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
            if (currentTime - lastAttack < player_pos[id]['attackSpeed']) { return; }
            lastAttack = currentTime;
            direction = "Space";
            break;
        default: return;
    }
    socket.emit('update_position', { direction: direction, id: id });
});
