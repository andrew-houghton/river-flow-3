document.getElementById("loading").remove()

// Initialize data structures
var graph_neighbours = new Object();
var graph_attributes = new Object();
var graph_sprites = new Object();

var max_x = 0;
var max_y = 0;
var max_height = 0;
var min_height = 100000;

for (node of graph_data) {
    max_x = (node.center[0] > max_x) ? node.center[0] : max_x;
    max_y = (node.center[1] > max_y) ? node.center[1] : max_y;
    max_height = (node.height > max_height) ? node.height : max_height;
    min_height = (node.height < min_height) ? node.height : min_height;
    graph_neighbours[node.key] = node.neighbours;
    graph_attributes[node.key] = {
        center: node.center,
        height: node.height,
        key: node.key,
    };
}
var grid_size;
var circle_radius;


function find_circle_centerpoint(x, y) {
    return [
        x * grid_size + grid_size / 2 - circle_radius,
        y * grid_size + grid_size / 2 - circle_radius,
    ]
}

function draw_circles(texture, container) {
    for (node of Object.values(graph_attributes)) {
        center = find_circle_centerpoint(node.center[0], node.center[1]);
        let sprite = new PIXI.Sprite(texture);
        sprite.x = center[0];
        sprite.y = center[1];
        sprite.tint = height_to_colour(node.height);
        container.addChild(sprite);
        graph_sprites[node.key] = sprite;
    }
}

// Create pixi app
const app = new PIXI.Application({
    backgroundColor: 0x000000,
    resolution: window.devicePixelRatio || 1
});
document.body.appendChild(app.view);
let container = new PIXI.ParticleContainer(graph_data.length);
app.stage.addChild(container);


window.addEventListener('resize', draw_objects);

function draw_objects() {
    container.removeChildren();
    app.renderer.resize(window.innerWidth, window.innerHeight);
    grid_size = Math.min(window.innerWidth / max_x, window.innerHeight / max_y);
    circle_radius = 0.4 * grid_size
    draw_circles(create_circle_texture(), container)
}
draw_objects();
update_colours();

function update_colours() {
    texture = create_circle_texture()
    for (let key in graph_sprites) {
        let sprite = graph_sprites[key];
        container.removeChild(sprite);
        sprite.tint = height_to_colour(graph_attributes[key].height);
        container.addChild(sprite);
    }
}

// Utility function
function create_circle_texture() {
    const p = new PIXI.Graphics();
    p.beginFill(0xFFFFFF);
    p.lineStyle(0);
    p.drawCircle(circle_radius, circle_radius, circle_radius);
    p.endFill();
    const t = PIXI.RenderTexture.create(p.width, p.height);
    app.renderer.render(p, t);
    return t;
}

function height_to_colour(height) {
    if (max_height - min_height == 0){
        return 0x000000
    }
    rgb = gist_earth[Math.floor((height - min_height) / (max_height - min_height) * 255)]
    return (rgb[0] << 16) + (rgb[1] << 8) + rgb[2];
}