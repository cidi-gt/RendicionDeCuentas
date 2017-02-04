PunchCard = Object.create(D3Visualization);
PunchCard.setup = function(mainDiv, squareEdge, strStartDate, strEndDate, linkType) {
    var self = this;
    var startDate = new Date(Date.parse(strStartDate+"T00:00:00-0600"));
    var endDate = new Date(Date.parse(strEndDate+"T23:59:59-0600"));
    //2 space between squares, 54 number of columns, 5 trailing widht at the end
    self.colNumber = 54;
    var width = (((squareEdge+2)*self.colNumber)+5);
    //double the size needed for 8 rows
    var height = (((squareEdge+2)*8)*2);
    self.setupD3(mainDiv, width, height, startDate, endDate, linkType);
    self.squareEdge = squareEdge;
    
    self.parentChangeDates = self.changeDates;

    self.changeDates = function(startDate, endDate) {
        //calculate dates    
        var startDate = new Date(Date.parse(startDate+"T00:00:00-0600"));
        var endDate = new Date(Date.parse(endDate+"T00:00:00-0600"));
        self.parentChangeDates(startDate,endDate);
    }
    
    self.draw = function(summarizedData) {
        var days = ["Domingo","Lunes","Martes","Miercoles","Jueves","Viernes","Sabado"]
        var months = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
        var startDayOfWeek = self.startDate.getDay();
        var currentDate = self.startDate;
        var datesArray = Array();
        var namesArray = Array();
        //add days to an array of dates, and another of names to display the data
        while (currentDate <= self.endDate) {
            datesArray.push(currentDate.formatDate());
            namesArray.push(days[currentDate.getDay()]+' '+currentDate.getDate()+' de '+months[currentDate.getMonth()]+' de '+currentDate.getFullYear());
            currentDate = currentDate.addDays(1);
        }
        //get the minimum and maximum values, (d3 function didn't get the right values)
        var maxValue = 0;
        var minValue = 100000;
        var extractedValues = {};
        summarizedData.forEach(function(d){
            extractedValues[d['end_date']] = parseFloat(d['t_ammount']);
            if (extractedValues[d['end_date']] > maxValue)
                maxValue = extractedValues[d['end_date']];
            if (extractedValues[d['end_date']] < minValue)
                minValue = extractedValues[d['end_date']];
        });
        
        //to enhance visualization, if minValue is greater than 1% of maxValue then use 1% of max, as minValue
        if (minValue > maxValue*0.01)
            minValue = maxValue*0.01;
        var ammountScale = d3.scale.linear().domain([minValue,maxValue]).range([0,100]);

        //clear the svg if there was something on it
        self.spinVar.stop();
        self.svg.selectAll("*").remove();
        
        //remove the tooltip if there was one, and add the tooltip for the current vis
        if (self.tooltip)
            jQuery(self.tooltip[0][0]).remove();
        self.tooltip = self.mainDiv.append("div")
            .attr("id","tooltip");

        var squareEdge = self.squareEdge;

        //initialize coordinates variables
        var y = (startDayOfWeek*(squareEdge+2))-((squareEdge+2));
        var x = 0;
        //check if difference is less than you can put in the worst case scenario for
        //54 columns(worst case is first day of week is the last row of the first column)
        var moreThanYear = false;
        if (((self.endDate - self.startDate)/86400000) > (self.colNumber*7-6)) {
            moreThanYear = true;
            //resize the svg to the needed height to display + the space of a full year (to display tooltip)
            self.svg.attr("height", ((self.endDate.getYear() - self.startDate.getYear()+1)*((squareEdge+2)*6+50))+((squareEdge+2)*6+50));
        }
        else {
            //make sure the size of the svg is for one row + the space of a full year (to display tooltip)
            self.svg.attr("height", ((squareEdge+2)*6+50)*2);
        }
        var squareSelection = self.svg.selectAll("rect")
                                .data(datesArray)
                                .enter()
                                .append("rect")
                                .attr("y", function(d){
                                    if (moreThanYear){
                                        currDate = new Date(Date.parse(d+"T00:00:00-0600"));
                                        //get the number of the working year.
                                        //multiply it for the height that each year uses
                                        y = currDate.getYear() - self.startDate.getYear();
                                        y = y * ((squareEdge+2)*6+50);
                                        //get the dayOfWeek and week of teh date to get x,y
                                        currDayOfWeek = currDate.getDay();
                                        currWeek = currDate.getWeek()-1; //real programmers start counting on 0 (and it displays better this way)
                                        extractedValues[d+'_x'] = (squareEdge+2)*currWeek;
                                        return currDayOfWeek*(squareEdge+2) + y;
                                    }
                                    else {
                                        //move squareEdge+littleSpace to draw the square 
                                        y = y+squareEdge+2;
                                        if (y > (6*(squareEdge+2))) {
                                            //next col
                                            y = 0;
                                            if (y==0)
                                                x = x + squareEdge+2;
                                        }
                                        extractedValues[d+'_x'] = x;
                                        return y;
                                    }
                                })
                                .attr("x",function(d) {
                                    return extractedValues[d+'_x'];
                                })
                                .attr("width",squareEdge)
                                .attr("height",squareEdge)
                                .style("stroke","#000")
                                .style("stroke-width","0.1")
                                .style("fill",function(d){
                                    /*currDate = d.formatDate()*/
                                    if((extractedValues[d] == null) | (extractedValues[d] == undefined)) {
                                        return "white";
                                    }
                                    return  gradientColor('#EDF9EA','#155E00',ammountScale(extractedValues[d]));
                                })
                                .on('mouseover', function(d,i) {
                                    self.tooltip.transition()
                                        .duration(200)
                                        .style("opacity", 1);
                                    self.tooltip.html("<h3>"+namesArray[i]+"</h3>"+
                                                "Gastado: Q "+parseFloat(extractedValues[d]).formatMoney(2)+"</br>"
                                                )
                                            .style("left", (d3.mouse(this)[0])+"px")
                                            .style("top", (d3.mouse(this)[1])+"px");
                                })
                                .on('mouseout', function(d) {
                                    self.tooltip.transition()
                                        .duration(500)
                                        .style("opacity",0);
                                })
                                .on('click', function(d) {
                                    window.open(self.linkType+d, '_blank');
                                });
        self.finishRender();
    }
    
}

