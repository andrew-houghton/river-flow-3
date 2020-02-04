var color = d3.scale.linear()
   .domain([0, 15, 20])
   .range(["#f11", "#1f1", "#a1f"])
   .interpolate(d3.interpolateHcl);

function spiral(d, i){
    var j,
        cx = 300,
        cy = 300;
    for (j = 0; j < 20; j+= 0.05){
        d3.select(this)
            .append('circle')
            .attr('cx', cx + Math.sin(j) * j * 10)
            .attr('cy', cy + Math.cos(j) * j * 10)
            .attr('r', 3)
        .style('fill',color(j));
    }
}

d3.select("svg").append('circle').attr('cx', 50)
  .attr('cy', 50)
  .attr('r', 5)
  .style('fill', color(0));

d3.select("svg").each(spiral);