# river-flow-3
Another attempt at writing the river flow algorithm focused on visualizations

## Visualization Steps

1. Pixels with colour for height
2. Swap to graph
3. Visualise merging equal height nodes by moving them to the centre point then changing them into one point
4. Flooding
5. BFS
6. Sort
7. Creation of linked list
8. Flow simulation

### Detailed list of steps

* Show NSW
* Zoom to map and show heightmap
* Select small area and zoom
* Show only heightmap as grid of squares
* Move squares appart and show linking lines
* Show equal height nodes
* 1 by 1 merge equal height nodes

### Instructions

1. Create virtual environment `virtualenv -p python3.7 venv`
2. Install required packages `pip install -r requirements.txt`
3. `cd pygame`
4. `python renderer.py`
5. Press right arrow key to advance
6. Press ESC at any time to exit

### Screenshot

![Graph of links between places with different heights][doc/screenshot.png]
