var D3Visualization = {
    width: 960,
    height: 650,
    startDate: new Date(),
    endDate: new Date(),
    svg: null,
    refreshBtn: '#btnActualizar',
    renderingVisualizations: 0, //variable to control visualizations rendering in one page, to enable refresh button
    setupD3: function(mainDiv,width,height,startDate,endDate, linkType) {
        D3Visualization.renderingVisualizations += 1;
        jQuery(D3Visualization.refreshBtn).prop('disabled',true);
        this.mainDiv = d3.select(mainDiv);
        if (width > 0)
            this.width = width;
        if (height > 0)
            this.height = height;
        this.startDate = startDate;
        this.endDate = endDate;
        this.spinVar = new Spinner(spOpts).spin(this.mainDiv[0][0]);
        this.svg = this.mainDiv.append("svg")
                    .attr("width",this.width)
                    .attr("height",this.height);
        //linkType is used when the click event is fired, it knows which link has to open (if it has)
        this.linkType = linkType || "";
    },
    changeDates: function(startDate, endDate) {
        jQuery(D3Visualization.refreshBtn).prop('disabled', true);
        D3Visualization.renderingVisualizations += 1;
        //as it is changing dates, it will be cleared first
        this.spinVar.spin(this.mainDiv[0][0]);
        this.svg.selectAll("*").remove();
        //change dates
        this.startDate = startDate;
        this.endDate = endDate;
    },
    finishRender: function() {
        D3Visualization.renderingVisualizations -=1;
        if (D3Visualization.renderingVisualizations <= 0) {
            jQuery(D3Visualization.refreshBtn).prop('disabled',false);
            D3Visualization.renderingVisualizations = 0;
        }
    }
    
}

