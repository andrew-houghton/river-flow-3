document.getElementById("loading").remove()

// Create pixi app
const app = new PIXI.Application({
    backgroundColor: 0x000000,
    resolution: window.devicePixelRatio || 1
});
document.body.appendChild(app.view);
const colour_sprite = PIXI.Sprite.fromImage('true_colour_resized.jpg');
colour_sprite.anchor.x = 0;
colour_sprite.anchor.y = 0;
const height_sprite = PIXI.Sprite.fromImage('ASTGTMV003_S45E168_dem.png');
height_sprite.anchor.x = 0;
height_sprite.anchor.y = 0;

function draw_objects(){
    app.renderer.resize(window.innerWidth, window.innerHeight);
    resize_ratio = Math.max(window.innerWidth / colour_sprite.width, window.innerHeight / colour_sprite.height)
    app.stage.addChild(colour_sprite);
    colour_sprite.width = colour_sprite.width * resize_ratio;
    colour_sprite.height = colour_sprite.height * resize_ratio;
}


function start_update_colours(){
    app.stage.addChild(height_sprite);
    app.renderer.resize(window.innerWidth, window.innerHeight);
    resize_ratio = Math.max(window.innerWidth / height_sprite.width, window.innerHeight / height_sprite.height)
    height_sprite.width = height_sprite.width * resize_ratio;
    height_sprite.height = height_sprite.height * resize_ratio;
}

window.addEventListener('resize', draw_objects);
draw_objects();
