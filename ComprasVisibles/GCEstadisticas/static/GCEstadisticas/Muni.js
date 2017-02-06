Muni = Object.create(D3Visualization);
Muni.setup = function(mainDiv, width, height, startDate, endDate) {
    var self = this;
    var startDate = new Date(startDate);
    var endDate = new Date(endDate);
    self.setupD3(mainDiv, width, height, startDate, endDate);
    self.projection = d3.geo.mercator()
        .scale(7701.467646382165)
        .center([-94.23084508112287,17.888754053851084]) //projection center
        .translate([width/2,height/2]) //translate to center the map in view
    self.path = d3.geo.path()
	    .projection(self.projection);
    var munisGroup;
    //Create zoom/pan listener and utilities
    var translateVar = [0,0];
    var scaleVar = 1;
    var zoom = d3.behavior.zoom()
        .scaleExtent([1, Infinity])
        .on("zoom", function() {
            translateVar[0] = d3.event.translate[0];
            translateVar[1] = d3.event.translate[1];
            scaleVar = d3.event.scale;
            munisGroup.attr("transform", "translate(" + zoom.translate() + ")scale(" + zoom.scale() + ")")
                .selectAll("path").style("stroke-width", 1 / zoom.scale() + "px" );
        });
    self.svg.call(zoom);

    self.drawAll = function(mapData, expenseData) {
        //prepare map
        self.spinVar.stop();
        self.svg.selectAll("*").remove();
        var outlines = topojson.feature(mapData, mapData.objects.collection);
         munisGroup = self.svg.append('g').attr('id', 'muni');
        //prepare data
        var expenseById = {}
        var maxValue = 0;
        var minValue = 10000;
        expenseData.forEach(function(d) {
            //if the entity being analized is on the array of the entities that have to been added, then add it to the array
            if (jQuery.inArray(d['id'].toString(), selectedEntities)!=-1) {
                //if the entry on the array for the DEPARMENT-CITY does not exists, then create it so it si possible to assign values
                if ((expenseById[d['department']+'-'+d['city']] == null) | (expenseById[d['department']+'-'+d['city']] == undefined))
                    expenseById[d['department']+'-'+d['city']] = 0;
                //add it to the summarization for the city
                expenseById[d['department']+'-'+d['city']] += parseFloat(d['t_ammount']);
                if (expenseById[d['department']+'-'+d['city']] > maxValue) {
                    maxValue = expenseById[d['department']+'-'+d['city']];
                }
                if (expenseById[d['department']+'-'+d['city']] < minValue) {
                    minValue = expenseById[d['department']+'-'+d['city']];
                }
            }
        });
        //to enhance visualization, if minValue is greater than 1% of maxValue then use 1% of max, as minValue
        if (minValue > maxValue*0.01)
            minValue = maxValue*0.01;
        var ammountScale = d3.scale.linear().domain([minValue,maxValue]).range([0,100]);
        //setup tooltip
        if (self.tooltip)
            jQuery(self.tooltip[0][0]).remove();
        self.tooltip = self.mainDiv.append("div")
            .attr("id","tooltip");
        //draw map
        munisGroup.selectAll('path')
            .data(outlines.features)
            .enter()
            .append('path')
            .attr('d', self.path)
            .style('fill', function(d) {
                if((expenseById[d.properties.DEPARTAMEN+'-'+d.properties.MUNICIPIO] == null) | (expenseById[d.properties.DEPARTAMEN+'-'+d.properties.MUNICIPIO] == undefined)) {
                    return "white";
                }
                return gradientColor('#EDF9EA','#155E00',ammountScale(expenseById[d.properties.DEPARTAMEN+'-'+d.properties.MUNICIPIO]));
            })
            .style('stroke','black')
            .style('stroke-width','0.3px')
            .on('mouseover', function(d) {
                self.tooltip.transition()
                    .duration(200)
                    .style("opacity", 1);
                self.tooltip.html(  "<h3>"+d.properties.MUNICIPIO+"</h3>"+
                                    "Nombre del municipio (mapa SEGEPLAN): "+d.properties.MUNI_ORIG+"</br>"+
                                    "Departamento: "+d.properties.DEPARTAMEN+"</br>"+
                                    "Q "+parseFloat(expenseById[d.properties.DEPARTAMEN+'-'+d.properties.MUNICIPIO]).formatMoney(2))
                    .style("left", ((d3.mouse(this)[0]*scaleVar+translateVar[0])) +"px")
                    .style("top", ((d3.mouse(this)[1]*scaleVar+translateVar[1])) +"px");
            })
            .on('mouseout', function(d) {
                self.tooltip.transition()
                    .duration(500)
                    .style("opacity",0);
            });
        self.finishRender();
    }

    self.draw = function(error, mapData, expenseData) {
        if(error) throw error;
        self.mapData = mapData;
        self.expenseData = expenseData;
        self.drawAll(mapData, expenseData);
    }

    self.redraw = function(expenseData) {
        self.expenseData = expenseData;
        self.drawAll(self.mapData, expenseData);
    }

    self.updatePaint = function() {
        self.drawAll(self.mapData, self.expenseData);
    }

}
