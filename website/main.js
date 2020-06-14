document.getElementById("loading").remove()

// Initialize data structures
var graph_neighbours = new Object();
var graph_attributes = new Object();
var graph_sprites = new Object();

var max_x = 0;
var max_y = 0;
for (node of graph_data){
    max_x = (node.center[0] > max_x) ? node.center[0] : max_x;
    max_y = (node.center[1] > max_y) ? node.center[1] : max_y;
    graph_neighbours[node.key] = node.neighbours;
    graph_attributes[node.key] = {
        center: node.center,
        height: node.height,
        key: node.key,
    };
}
var width_per_circle;
var height_per_circle;
var circle_radius;


function find_circle_centerpoint(x, y) {
    return [
        x * width_per_circle + width_per_circle / 2,
        y * height_per_circle + height_per_circle / 2,
    ]
}

// function find_circle_colour(altitude) {
// }
// function draw_line(x1, y1, x2, y2) {
// }

function draw_circles(texture, container){
    for (node of Object.values(graph_attributes)){
        center = find_circle_centerpoint(node.center[0], node.center[1]);
        let sprite = new PIXI.Sprite(texture);
        sprite.x = center[0];
        sprite.y = center[1];
        container.addChild(sprite);
        graph_sprites[node.key] = sprite;
    }
}

// Create pixi app
const app = new PIXI.Application({backgroundColor: 0x1099bb, resolution: window.devicePixelRatio || 1});
document.body.appendChild(app.view);
let container = new PIXI.ParticleContainer(graph_data.length);
app.stage.addChild(container);


window.addEventListener('resize', draw_objects);
function draw_objects() {
    container.removeChildren();
    app.renderer.resize(window.innerWidth, window.innerHeight);
    width_per_circle = window.innerWidth / max_x;
    height_per_circle = window.innerHeight / max_y;
    circle_radius = 0.4 * Math.min(width_per_circle, height_per_circle)
    draw_circles(create_circle_texture(), container)
}
draw_objects();

// Utility function
function create_circle_texture(){
    const p = new PIXI.Graphics();
    p.beginFill(0xFFFFFF);
    p.lineStyle(0);
    p.drawCircle(circle_radius, circle_radius, circle_radius);
    p.endFill();
    const t = PIXI.RenderTexture.create(p.width, p.height);
    app.renderer.render(p, t);
    return t;
}