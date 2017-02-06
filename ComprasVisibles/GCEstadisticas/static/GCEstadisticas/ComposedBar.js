ComposedBar = Object.create(D3Visualization);
ComposedBar.setup = function(mainDiv, width, height, startDate, endDate, barType, linkType) {
    var self = this;
    self.hBar = (barType == "h")?true:false;
    self.setupD3(mainDiv, width, height, startDate, endDate, linkType);
    var translateVar = [0,0];
    var scaleVar = 1;
    var zoom = d3.behavior.zoom()
        .scaleExtent([1, Infinity])
        .on("zoom", function(){
            translateVar[0] = d3.event.translate[0];
            translateVar[1] = d3.event.translate[1];
            scaleVar = d3.event.scale;
            self.svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
        });
    self.svg.call(zoom);
    var colorScale = d3.scale.linear().domain([4,14]).range([1,100]);
    var entityTypes = {
        4:'Administración Central',
        5:'Entidades Descentralizadas, Autónomas y de Seguridad Social',
        6:'Gobiernos Locales (Municipalidades, Mancomunidades, etc.)',
        7:'Empresas Públicas (Nacionales y Municipales)',
        8:'Fideicomisos con fondos públicos',
        9:'ONG\'s, patronatos, comités, asociaciones y fundaciones',
        10:'Consejos de desarrollo',
        11:'Cooperativas',
        12:'Entidades privadas',
        13:'Otro tipo',
        14:'Organizaciones Internacionales'
    }
    var entityColors = {
        4:'#1F77B4',
        5:'#15324C',
        6:'#2CA02C',
        7:'#D62728',
        8:'#9467BD',
        9:'#FF7F0E',
        10:'#7F7F7F',
        11:'#BCBD22',
        12:'#17BECF',
        13:'#637939',
        14:'#D6616B'
    }
    
    self.drawList = function() {
        jQuery("#typeList").remove();
        jQuery('<div id="typeList"></div>').insertBefore('#visualization');
        Object.keys(entityTypes)
            .sort()
            .forEach(function(key) {
                jQuery('#typeList').append('<input type="checkbox" id="cb'+key+'" style="display:none;"/><label style="margin-right:20px;" for="cb'+key+'">'+entityTypes[key]+'</label>');
                jQuery("head").append($('<style>#cb'+key+' + label:before { content:" "; background-color:'+entityColors[key]+'; display:inline-block; visibility:visible; height:16px; width:16px;}</style>'));
            });
    }

    self.entityColor = function(entity) {
        if (entity in entityTypes)
            return entityColors[entity];
        else
            return "#65D25B";
    }

    self.draw = function(summarizedData) {
        self.drawList();
        self.svg.selectAll("*").remove();
        modalities = {};
        var maxModality = 0;
        var minValue = 100000;
        var totalExpense = 0;
        summarizedData.forEach(function(d){
            var t_ammount = parseFloat(d.t_ammount)
            if (d.modality in modalities){
                modalities[d.modality]['t_ammount'] += t_ammount;
                modalities[d.modality]['values'].push(d);
            }
            else{
                modalities[d.modality] = {};
                modalities[d.modality]['t_ammount'] = t_ammount;
                modalities[d.modality]['values'] = [];
                modalities[d.modality]['values'].push(d);
            }
            if (modalities[d.modality]['t_ammount'] > maxModality){
                maxModality = modalities[d.modality]['t_ammount'];
            }
            if (t_ammount < minValue){
                minValue = t_ammount;
            }
            totalExpense += t_ammount;

        });
        var maxRange = (self.hBar)?self.width-150:self.height-150;
        //to enhance visualization, if minValue is greater than 1% of maxModality then use 1% of max, as minValue
        if (minValue > maxModality*0.01)
            minValue = maxModality*0.01;
        var ammountScale = d3.scale.linear().domain([minValue,maxModality]).range([0.1,maxRange]);

        //clear the svg if there was something on it
        self.spinVar.stop();
        self.svg.selectAll("*").remove();
        
        //remove the tooltip if there was one, and add the tooltip for the current vis
        if (self.tooltip)
            jQuery(self.tooltip[0][0]).remove();
        self.tooltip = self.mainDiv.append("div")
            .attr("id","tooltip");
        var barSelection = {};
        var texts = {};
        var x,y;
        var nextX; //aux var for position cursor to draw when drawing horizontal vars
        var barBaseSize = (self.hBar)?(((self.height-20)/Object.keys(modalities).length)-20)-5:(((self.width-20)/Object.keys(modalities).length)-20)-5;
        x = (self.hBar)?10:20;
        nextX = (self.hBar)?x:0;
        y = (self.hBar)?25:self.height-50;
        Object.keys(modalities)
            .sort()
            .forEach(function(key) {
                sortedValues = modalities[key]['values']
                sortedValues.sort(function(x,y) {
                    return (x.t_ammount - y.t_ammount);
                });
                x = (self.hBar)?10:x;
                y = (self.hBar)?y:self.height-50;
                barSelection[key] = self.svg.append("g").attr("id",key);
                barSelection[key].selectAll("rect")
                                .data(sortedValues)
                                .enter()
                                .append("rect")
                                .attr("y", function(d) {
                                    y = (self.hBar)?y:(y - ammountScale(d.t_ammount));
                                    return y;
                                })
                                .attr("x", function(d) {
                                    x = (self.hBar)?nextX:x;
                                    nextX = (self.hBar)?(nextX + ammountScale(d.t_ammount)):0;
                                    return x;
                                })
                                .attr("width", function(d) {
                                    x = (self.hBar)?(d.x_position):x;
                                    return (self.hBar)?ammountScale(d.t_ammount):barBaseSize;
                                })
                                .attr("height", function(d){
                                    return (self.hBar)?barBaseSize:ammountScale(d.t_ammount);
                                })
                                .style("stroke","#fff")
                                .style("stroke-width","0.08")
                                .style("fill",function(d){
                                    return self.entityColor(d.entity_type_id);
                                })
                                .on('mouseover', function(d) {
                                    self.tooltip.transition()
                                        .duration(200)
                                        .style("opacity", 1);
                                    self.tooltip.html("<h3>"+d.name+"</h3>"+
                                                "Gastado: Q "+parseFloat(d.t_ammount).formatMoney(2)+"</br>"+
                                                "Total de todas las entidades para la modalidad: Q "+parseFloat(modalities[key]['t_ammount']).formatMoney(2)+"</br>"
                                                )
                                        .style("left", ((d3.mouse(this)[0]*scaleVar+translateVar[0])) +"px")
                                        .style("top", ((d3.mouse(this)[1]*scaleVar+translateVar[1])) +"px");
                                })
                                .on('mouseout', function(d) {
                                    self.tooltip.transition()
                                        .duration(500)
                                        .style("opacity",0);
                                })
                                .on('click', function(d) {
                                    if (self.linkType == "entidad"){
                                        window.open('/visualizaciones/entidad/'+d.id+"/"+self.startDate+"/"+self.endDate, '_blank');
                                    }
                                    if (self.linkType == "proveedor"){
                                        window.open('/visualizaciones/proveedor/'+d.id+"/"+self.startDate+"/"+self.endDate, '_blank');
                                    }
                                });
                x = (self.hBar)?10:(x+barBaseSize+20);
                nextX = (self.hBar)?x:0;
                y = (self.hBar)?(y+barBaseSize+25):y;
        });
        x = (self.hBar)?10:20;
        y = (self.hBar)?24:self.height-50;
        var labels = Object.keys(modalities).sort();
        var labelTxt = self.svg.append("g").attr("id","labels").selectAll("text")
                        .data(labels)
                        .enter()
                        .append("text")
                        .attr("x",function(d,i){
                            return (self.hBar)?10:(x + (barBaseSize+20)*i);
                        })
                        .attr("y",function(d,i){
                            return (self.hBar)?(y + (barBaseSize+25)*i):y;
                        })
                        .attr("transform", function(d,i) {
                            return (self.hBar)?"":("rotate(-90,"+(x + (barBaseSize+20)*i)+","+y+")");
                        })
                        .text(function(d){
                            return d+" Q"+parseFloat(modalities[d]['t_ammount']).formatMoney(2)+"("+parseFloat(modalities[d]['t_ammount']*100/totalExpense).formatMoney(2)+"%)";
                        });
        self.finishRender();
    }
}

