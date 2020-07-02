document.getElementById("loading").remove()

// Initialize data structures
var graph_neighbours = new Object();
var graph_attributes = new Object();
var graph_sprites = new Object();
var graph_lines = new Object();

var max_x = 0;
var max_y = 0;
var max_height = 0;
var min_height = 100000;
var num_links = 0;

for (node of graph_data) {
    max_x = (node.center[0] > max_x) ? node.center[0] : max_x;
    max_y = (node.center[1] > max_y) ? node.center[1] : max_y;
    max_height = (node.height > max_height) ? node.height : max_height;
    min_height = (node.height < min_height) ? node.height : min_height;
    graph_neighbours[node.key] = node.neighbours;
    num_links += node.neighbours.length;
    graph_attributes[node.key] = {
        center: node.center,
        height: node.height,
        key: node.key,
    };
}
max_x += 1;
max_y += 1;

var grid_size;
var circle_radius;

// Create pixi app
const app = new PIXI.Application({
    backgroundColor: 0x000000,
    resolution: window.devicePixelRatio || 1
});
document.body.appendChild(app.view);

let line_container = new PIXI.ParticleContainer(num_links);
app.stage.addChild(line_container);
let container = new PIXI.ParticleContainer(graph_data.length);
app.stage.addChild(container);

window.addEventListener('resize', draw_objects);

function find_circle_centerpoint(x, y) {
    return [
        x * grid_size + grid_size / 2,
        y * grid_size + grid_size / 2,
    ]
}

function draw_circles(texture, container) {
    for (node of Object.values(graph_attributes)) {
        center = find_circle_centerpoint(node.center[0], node.center[1]);
        let sprite = new PIXI.Sprite(texture);
        sprite.x = center[0] - circle_radius;
        sprite.y = center[1] - circle_radius;
        sprite.tint = height_to_colour(node.height);
        container.addChild(sprite);
        graph_sprites[node.key] = sprite;
    }
}

function get_angle(x1, x2, y1, y2) {
    return Math.atan2(y2 - y1, x2 - x1) - Math.PI / 2;
}

function draw_lines(container) {
    texture = create_pixel_texture()
    for (node of Object.values(graph_attributes)) {
        center = find_circle_centerpoint(node.center[0], node.center[1]);
        for (neighbour of Object.values(graph_neighbours[node.key])) {
            neighbour_node = graph_attributes[neighbour]
            center2 = find_circle_centerpoint(neighbour_node.center[0], neighbour_node.center[1]);
            sprite = draw_line(center[0], center[1], center2[0], center2[1], 2, texture)
            graph_lines[node.key + ">" + neighbour_node.key] = sprite;
        }
    }
}

function draw_line(x1, y1, x2, y2, thickness, texture) {
    let line_sprite = new PIXI.Sprite.from(texture);
    angle = get_angle(x1, x2, y1, y2);
    line_sprite.x = x1 - Math.cos(angle) * thickness / 2;
    line_sprite.y = y1 - Math.sin(angle) * thickness / 2;
    line_sprite.scale.x = thickness;
    line_sprite.scale.y = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5;
    line_sprite.rotation = angle;
    line_container.addChild(line_sprite);
    return line_sprite;
}

function draw_objects() {
    container.removeChildren();
    line_container.removeChildren();
    app.renderer.resize(window.innerWidth, window.innerHeight);
    grid_size = Math.min(window.innerWidth / max_x, window.innerHeight / max_y);
    circle_radius = 0.4 * grid_size
    draw_circles(create_circle_texture(), container)
    draw_lines(line_container)
}

// Flow simulation code:
var graph_flows = new Object();
function start_update_colours() {
    sorted_keys = Object.keys(graph_attributes).sort(k => graph_attributes[k].height);
    for (key of sorted_keys) {
        graph_flows[key] = 1;
    }
    loop_update_colours()
}

function loop_update_colours() {
    update_colours();
    if (Math.max(...Object.values(graph_flows)) > 0) {
        setTimeout(loop_update_colours, 0);
    }
}

function update_colours() {
    for (key of sorted_keys) {
        // There has gotta be a way to do this with fewer passes!
        // Also stop recalculating height difference!
        total_outflow_height = 0;
        largest_height_difference = 0;
        for (neighbour of graph_neighbours[key]) {
            if (graph_attributes[key].height > graph_attributes[neighbour].height) {
                height_difference = graph_attributes[key].height - graph_attributes[neighbour].height;
                total_outflow_height += height_difference;
                if (height_difference > largest_height_difference) {
                    largest_height_difference = height_difference;
                }
            }
        }
        // Only send flow to nodes that have a significant amount of flow
        // Significant means at least 10% of the flow going to the main outflow
        active_total_height_difference = 0;
        for (neighbour of graph_neighbours[key]) {
            height_difference = graph_attributes[key].height - graph_attributes[neighbour].height;
            if (height_difference > largest_height_difference/10){
                active_total_height_difference += graph_attributes[key].height - graph_attributes[neighbour].height;
            }
        }
        for (neighbour of graph_neighbours[key]) {
            height_difference = graph_attributes[key].height - graph_attributes[neighbour].height;
            if (height_difference > largest_height_difference/10){
                graph_flows[neighbour] += graph_flows[key] * height_difference / active_total_height_difference
            }
        }
        graph_flows[key] = 0;
    }
    max_flow = Math.log(Math.max(...Object.values(graph_flows)))
    for (key of sorted_keys) {
        let sprite = graph_sprites[key];
        container.removeChild(sprite);
        sprite.tint = float_to_colour(Math.max(0, Math.log(graph_flows[key])) / max_flow);
        container.addChild(sprite);
    }
}

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

function create_pixel_texture() {
    const p = new PIXI.Graphics();
    p.beginFill(0xFFFFFF);
    p.lineStyle(0);
    p.drawRect(0, 0, 1, 1);
    p.endFill();
    const t = PIXI.RenderTexture.create(p.width, p.height);
    app.renderer.render(p, t);
    return t;
}

function height_to_colour(height) {
    if (max_height - min_height == 0) {
        return 0x000000
    }
    rgb = gist_earth[Math.floor((height - min_height) / (max_height - min_height) * 255)]
    return (rgb[0] << 16) + (rgb[1] << 8) + rgb[2];
}

function float_to_colour(value) {
    rgb = gist_earth[Math.floor(value * 255)]
    return (rgb[0] << 16) + (rgb[1] << 8) + rgb[2];
}

draw_objects();
