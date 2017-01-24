Sunburst = Object.create(D3Visualization);
Sunburst.setup = function(mainDiv, width, height, startDate, endDate, firstLevelName, secondLevelName, ammount, linkType) {
    var self = this;
    self.firstLevelName = firstLevelName
    self.secondLevelName = secondLevelName
    self.ammount = ammount
    self.setupD3(mainDiv, width, height, startDate, endDate, linkType);
    self.radius = (self.height/2)-5;
    self.svg = self.svg.append("g")
                .attr("transform", "translate(" + self.width/2 + "," + self.height/2 + ")");
    var translateVar = [self.width/2,self.height/2];


    self.draw = function(summarizedData) {
        //clear space
        self.spinVar.stop();
        self.svg.selectAll("*").remove();
        //remove the tooltip if there was one, and add the tooltip for the current vis
        if (self.tooltip)
            jQuery(self.tooltip[0][0]).remove();
        self.tooltip = self.mainDiv.append("div")
            .attr("id","tooltip");
        //colors
        var hue = d3.scale.category20();
        var luminance = d3.scale.sqrt()
            .domain([0, 1e6])
            .clamp(true)
            .range([90, 20]);

    
        //prepare the data
        var root = {name:"root", children:[]};
        var categories = {}; 
        summarizedData.forEach(function(d){
            var t_ammount = parseFloat(d[self.ammount])
            if (!(d.c_id in categories)){
                categories[d.c_id] = {};
                categories[d.c_id]['name'] = d[self.firstLevelName]
                categories[d.c_id]['children'] = [];
            }
            categories[d.c_id]['children'].push({name:d[self.secondLevelName], id:d['e_id'], size:t_ammount});
        });
        Object.keys(categories)
            .sort()
            .forEach(function(key){
                root['children'].push(categories[key]);
            });
        var partition = d3.layout.partition()
            //.sort(function(a, b) { return d3.ascending(a.name, b.name); })
            .size([2 * Math.PI, self.radius]);
        partition
            .value(function(d) { return d.size; })
            .nodes(root)
            .forEach(function(d) {
                d._children = d.children;
                d.sum = d.value;
                d.key = key(d);
                d.fill = fill(d);
            });
        partition
            .children(function(d, depth) { return depth < 2 ? d._children : null; })
            .value(function(d) { return d.sum; });

        var arc = d3.svg.arc()
            .startAngle(function(d) { return d.x; })
            .endAngle(function(d) { return d.x + d.dx ; })
            .padAngle(.001)
            .padRadius(self.radius / 3)
            .innerRadius(function(d) { return self.radius / 3 * d.depth; })
            .outerRadius(function(d) { return self.radius / 3 * (d.depth + 1) - 1; });

        var center = self.svg.append("circle")
            .attr("r", self.radius / 3)
            .on("click", zoomOut);

        center.append("title")
            .text("Regresar");

        var path = self.svg.selectAll("path")
            .data(partition.nodes(root).slice(1))
            .enter()
            .append("path")
            .attr("d", arc)
            .style("fill", function(d) { return d.fill; })
            .each(function(d) { this._current = updateArc(d); })
            .on("click", zoomIn)
            .on('mouseover', function(d) {
                self.tooltip.transition()
                    .duration(200)
                    .style("opacity", 1);
                self.tooltip.html("<h6>"+d.name+"</h6>"+
                            "Gastado: Q "+parseFloat(d.value).formatMoney(2)+"</br>"
                            )
                        .style("left", (d3.mouse(this)[0]+translateVar[0])+"px")
                        .style("top", (d3.mouse(this)[1]+translateVar[1])+"px");
            })
            .on('mouseout', function(d) {
                self.tooltip.transition()
                    .duration(500)
                    .style("opacity",0);
            });

        self.finishRender();
          
        function zoomIn(p) {
            if (p.depth > 1) p = p.parent;
            if (!p.children) {
                if (self.linkType == "entidad"){
                    window.open('/visualizaciones/entidad/'+p.id+"/"+self.startDate+"/"+self.endDate, '_blank');
                }
                return;
            }
            zoom(p, p);
        }

        function zoomOut(p) {
            if (!p.parent) return;
            zoom(p.parent, p);
        }

        // Zoom to the specified new root.
        function zoom(root, p) {
            if (document.documentElement.__transition__) return;

            // Rescale outside angles to match the new layout.
            var enterArc,
                exitArc,
                outsideAngle = d3.scale.linear().domain([0, 2 * Math.PI]);

            function insideArc(d) {
                return p.key > d.key
                ? {depth: d.depth - 1, x: 0, dx: 0} : p.key < d.key
                ? {depth: d.depth - 1, x: 2 * Math.PI, dx: 0}
                : {depth: 0, x: 0, dx: 2 * Math.PI};
            }

            function outsideArc(d) {
                return {depth: d.depth + 1, x: outsideAngle(d.x), dx: outsideAngle(d.x + d.dx) - outsideAngle(d.x)};
            }

            center.datum(root);

            // When zooming in, arcs enter from the outside and exit to the inside.
            // Entering outside arcs start from the old layout.
            if (root === p) enterArc = outsideArc, exitArc = insideArc, outsideAngle.range([p.x, p.x + p.dx]);

            path = path.data(partition.nodes(root).slice(1), function(d) { return d.key; });

            // When zooming out, arcs enter from the inside and exit to the outside.
            // Exiting outside arcs transition to the new layout.
            if (root !== p) enterArc = insideArc, exitArc = outsideArc, outsideAngle.range([p.x, p.x + p.dx]);

            d3.transition().duration(d3.event.altKey ? 7500 : 750).each(function() {
                path.exit().transition()
                .style("fill-opacity", function(d) { return d.depth === 1 + (root === p) ? 1 : 0; })
                .attrTween("d", function(d) { return arcTween.call(this, exitArc(d)); })
                .remove();

                path.enter().append("path")
                .style("fill-opacity", function(d) { return d.depth === 2 - (root === p) ? 1 : 0; })
                .style("fill", function(d) { return d.fill; })
                .on("click", zoomIn)
                .each(function(d) { this._current = enterArc(d); })
                .on('mouseover', function(d) {
                    self.tooltip.transition()
                        .duration(200)
                        .style("opacity", 1);
                    self.tooltip.html("<h6>"+d.name+"</h6>"+
                                "Gastado: Q "+parseFloat(d.value).formatMoney(2)+"</br>"
                                )
                            .style("left", (d3.mouse(this)[0]+translateVar[0])+"px")
                            .style("top", (d3.mouse(this)[1]+translateVar[1])+"px");
                })
                .on('mouseout', function(d) {
                    self.tooltip.transition()
                        .duration(500)
                        .style("opacity",0);
                });


                path.transition()
                .style("fill-opacity", 1)
                .attrTween("d", function(d) { return arcTween.call(this, updateArc(d)); });
            });
        }
        
        
        function key(d) {
          var k = [], p = d;
          while (p.depth) k.push(p.name), p = p.parent;
          return k.reverse().join(".");
        }

        function fill(d) {
          var p = d;
          while (p.depth > 1) p = p.parent;
          var c = d3.lab(hue(p.name));
          c.l = luminance(d.sum);
          return c;
        }

        function arcTween(b) {
          var i = d3.interpolate(this._current, b);
          this._current = i(0);
          return function(t) {
            return arc(i(t));
          };
        }

        function updateArc(d) {
          return {depth: d.depth, x: d.x, dx: d.dx};
        }
    }
}
