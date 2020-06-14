document.getElementById("loading").remove()

// Initialize data structures


// Create pixi app
const app = new PIXI.Application({
    width: 800, height: 600, backgroundColor: 0x1099bb, resolution: window.devicePixelRatio || 1,
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
