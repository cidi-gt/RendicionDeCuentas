/*
    This object expects:
        mainDiv: name of the div where the svg is going to be inserted
        widht: svg width
        height: svg height
        startDate: first day of the visualization
        endDate: last day of the visualization
        varRadius: name of the json property that is going to be used to manage the radius
        coloringVar: array of properties that are going to be used to color the bubbles
        coloringTipLabels: array of labels that will be put on the tooltip for the variables in the coloringVar
        linkType: will create a link, depending on the value
        besides, the json needes a property named "name" to put on the tooltip
        the value used as radius needs to be float. It will be presented as Q.N{+}.NN
        
        
*/
Bubble = Object.create(D3Visualization);
Bubble.setup = function(mainDiv, width, height, startDate, endDate, varRadius, coloringVar, coloringTipLabels, linkType) {
    var self = this;
    self.varRadius = varRadius;
    self.coloringVar = coloringVar;
    self.coloringTipLabels = coloringTipLabels;
    self.setupD3(mainDiv, width, height, startDate, endDate, linkType);
    var translateVar = [0,0];
    var scaleVar = 1;
    var zoom = d3.behavior.zoom()
        .scaleExtent([0.1, Infinity])
        .on("zoom", function(){
            translateVar[0] = d3.event.translate[0];
            translateVar[1] = d3.event.translate[1];
            scaleVar = d3.event.scale;
            self.svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
        });
    self.svg.call(zoom);


    self.draw = function(summarizedData) {
        var maxRadius = 0
        var minRadius = 1000000;
        var maxColors = [];
        var minColors = [];
        self.coloringVar.forEach(function(){
            maxColors.push(0);
            minColors.push(1000000);
        });
        var nodes = [];

        self.spinVar.stop();
        self.svg.selectAll("*").remove();

        var bubble = d3.layout.pack()
                .sort(null)
                .size([self.width, self.height])
                .padding(1.5);

        summarizedData.forEach(function(d){
            currRadius = isNaN(parseFloat(d[varRadius]))?0:parseFloat(d[varRadius]);
            currColorings = []
            self.coloringVar.forEach(function(element){
                currColorings.push(parseInt(d[element]));
            });
            if (currRadius > 0) {
                node = {}
                node['packageName'] = "main";
                node['className'] = d['name'];
                node['value'] = currRadius;
                node['name'] = d['name'];
                node['id'] = d['id'];
                node['t_radius'] = currRadius;
                self.coloringVar.forEach(function(element, index){
                    node[element] = currColorings[index];
                });
                nodes.push(node);
                if (currRadius > maxRadius)
                    maxRadius = currRadius;
                if (currRadius < minRadius)
                    minRadius = currRadius;
                currColorings.forEach(function(element, index){
                    if (element < minColors[index])
                        minColors[index] = element;
                    if (element > maxColors[index])
                        maxColors[index] = element;
                });
            }
        });

        nodes.sort(function(x, y){
           return d3.descending(x.value, y.value);
        });
        
        var svgNode = self.svg.selectAll(".node")
                .data(bubble.nodes({children: [{children: nodes}]})
                .filter(function(d) { return !d.children; }))
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });


        //to enhance visualization, if minRadius is greater than 1% of maxRadius then use 1% of max, as minradius
        if (minRadius > maxRadius*0.01)
            minRadius = maxRadius*0.01;
        radiusScale = d3.scale.linear().domain([minRadius,maxRadius]).range([1,100]);
        coloringScale = []
        self.coloringVar.forEach(function(element, index){
            coloringScale.push(d3.scale.linear().domain([minColors[index],maxColors[index]]).range([0,100]));
        });

        //setup tooltip
        if (self.tooltip)
            jQuery(self.tooltip[0][0]).remove();
        self.tooltip = self.mainDiv.append("div")
            .attr("id","tooltip");

        svgNode.append("circle")
                .attr("r", function(d){ d.r = radiusScale(d.t_radius);  return radiusScale(d.t_radius); })
                .style("stroke","#000")
                .style("stroke-width","0.3")
                .on('mouseover', function(d) {
                    d3.select(this).style("stroke-width","0.9");
                    self.tooltip.transition()
                        .duration(200)
                        .style("opacity", 1);
                    coloringTip = "";
                    self.coloringVar.forEach(function(element, index){
                        coloringTip += self.coloringTipLabels[index]+d[element]+"</br>";
                    });
                    self.tooltip.html("<h6>"+d.name+"</h6>"+
                                "Gastado: Q "+parseFloat(d.t_radius).formatMoney(2)+"</br>"+
                                coloringTip
                                )
                        .style("left", ((d3.mouse(this)[0]*scaleVar+translateVar[0]+(scaleVar*d.x))) +"px")
                        .style("top", ((d3.mouse(this)[1]*scaleVar+translateVar[1]+(scaleVar*d.y))) +"px");
                        
                })
                .on('mouseout', function(d) {
                    d3.select(this).style("stroke-width","0.5");
                    self.tooltip.transition()
                        .duration(500)
                        .style("opacity",0);
                })
                .on('click', function(d){
                    if (self.linkType == "entidad"){
                        window.open('/visualizaciones/entidad/'+d.id+"/"+self.startDate+"/"+self.endDate, '_blank');
                    }
                    if (self.linkType == "proveedor") {
                        window.open('/visualizaciones/proveedor/'+d.id+"/"+self.startDate+"/"+self.endDate, '_blank');
                    }
                });

        self.refreshColor(0);
        self.finishRender();
    }

    
    self.refreshColor = function(visVar) {
        var squareSelection = gbe.svg.selectAll("circle")
                                .style("fill",function(d){
                                    var observedVar = 0;
                                    observedVar = d[self.coloringVar[visVar]];
                                    if((observedVar == null) | (observedVar == undefined)) {
                                        return "white";
                                    }
                                    switch(visVar){
                                        case 0:
                                            return gradientColor('#C1F4D5','#00441b',coloringScale[0](observedVar));
                                            break;
                                        case 1:
                                            return gradientColor('#C6DEFF','#08306b',coloringScale[0](observedVar));
                                            break;
                                        case 2:
                                            return gradientColor('#FCE4AB','#EC971F',coloringScale[0](observedVar));
                                            break;
                                    }
        });
        return false;
    }
}
