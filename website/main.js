document.getElementById("loading").remove()

// Initialize data structures
var graph_neighbours = new Object();
var graph_attributes = new Object();
var max_x = 0;
var max_y = 0;
for (node of graph_data){
    max_x = (node.center[0] > max_x) ? node.center[0] : max_x;
    max_y = (node.center[1] > max_y) ? node.center[1] : max_y;
    graph_neighbours[node.key] = node.neighbours;
    graph_attributes[node.key] = {center:node.center, height:node.height};
}

function find_circle_centerpoint(x, y){

}

function find_circle_colour(altitude){

}

function draw_line(x1, y1, x2, y2){

}

// Create pixi app
const app = new PIXI.Application({
    backgroundColor: 0x1099bb, resolution: window.devicePixelRatio || 1,
});
document.body.appendChild(app.view);

// Create bunnies
const container = new PIXI.Container();
app.stage.addChild(container);
const texture = PIXI.Texture.from('bunny.png');
for (let i = 0; i < 25; i++) {
    const bunny = new PIXI.Sprite(texture);
    bunny.anchor.set(0.5);
    bunny.x = (i % 5) * 40;
    bunny.y = Math.floor(i / 5) * 40;
    container.addChild(bunny);
}

// Rotate bunnies on update
app.ticker.add((delta) => {
    container.rotation += 0.001 * delta;
});

// Resize canvas on reload
window.addEventListener('resize', resize);
function resize() {
    app.renderer.resize(window.innerWidth, window.innerHeight);
    container.x = app.screen.width / 2;
    container.y = app.screen.height / 2;
    container.pivot.x = container.width / 2;
    container.pivot.y = container.height / 2;
}
resize();
