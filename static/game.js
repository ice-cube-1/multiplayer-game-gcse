var canvas = document.getElementById("canvas");
    var scale = 40
    var ctx = canvas.getContext("2d");
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var id;
    var grid;
    var gridToRender = [];
    var screensize = [20,20];
    socket.on('base_grid', function(data) {
        grid = data
    });
    socket.on('item_positions', function(data) {
        items = data
    });
    socket.on('client_id', function(data) {
        id = data
        console.log('Your client ID is: ' + data);
    });
    socket.on('new_positions', function(data) {
        var playerpos = data.objects;
        screenxoffset = playerpos[id]['x']-screensize[0]/2
        screenyoffset = playerpos[id]['y']-screensize[1]/2
        if (screenxoffset < 0) {
            screenxoffset = 0
        } else if (screenxoffset + screensize[0] >= grid[0].length) {
            screenxoffset = grid[0].length-screensize[0]
        }
        if (screenyoffset < 0) {
            screenyoffset = 0
        } else if (screenyoffset + screensize[1] >= grid.length) {
            screenyoffset = grid.length-screensize[1]
        }
        for (let i = 0; i < screensize[1]; i++) {
            gridToRender[i] = [];
            for (let j = 0; j < screensize[0]; j++) {
                if (grid[i+screenyoffset][j+screenxoffset] == 0) {
                    gridToRender[i][j] = [255,255,255];
                } else {
                    gridToRender[i][j] = [0,0,0];
                }
            }
        }
        for (let i = 0; i<playerpos.length; i++) {
            if ((0 <= playerpos[i]['x'] - screenxoffset && playerpos[i]['x'] - screenxoffset < screensize[0]) && (0 <= playerpos[i]['y'] - screenyoffset && playerpos[i]['y'] - screenyoffset < screensize[1])) {
                gridToRender[playerpos[i]['y']-screenyoffset][playerpos[i]['x']-screenxoffset] = playerpos[i]['color'];
            }
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (var i = 0; i < screensize[1]; i++) {
            for (var j = 0; j < screensize[0]; j++) {
                var x = j * scale;
                var y = i * scale;
                ctx.fillStyle = `rgb(${gridToRender[i][j].join(',')})`; // Convert RGB array to string
                ctx.fillRect(x, y, scale, scale);
            }
        }
        for (let i = 0; i<items.length; i++) {
            if ((0 <= items[i]['x'] - screenxoffset && items[i]['x'] - screenxoffset < screensize[0]) && (0 <= items[i]['y'] - screenyoffset && items[i]['y'] - screenyoffset < screensize[1])) {
                var img = new Image();
                img.src = `static/items-images/${items[i]['type']}${items[i]['weapontype']}/${items[i]['rarity']}.png`;
                ctx.drawImage(img, (items[i]['x'] - screenxoffset) * scale, (items[i]['y'] - screenyoffset) * scale,scale,scale);
            }
        }
    });
    $(document).keydown(function(e) {
        var direction = '';
        switch(e.which) {
            case 87:
                direction = 'W';
                break;
            case 65:
                direction = 'A';
                break;
            case 83:
                direction = 'S';
                break;
            case 68:
                direction = 'D';
                break;
            case 32:
                direction = "Space";
                break;
            default:
                return;
        }
        socket.emit('update_position', { direction: direction, id: id});
    });
