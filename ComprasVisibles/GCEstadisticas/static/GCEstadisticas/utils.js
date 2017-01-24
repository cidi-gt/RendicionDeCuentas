    Number.prototype.formatMoney = function(c, d, t){
    var n = this, 
        c = isNaN(c = Math.abs(c)) ? 2 : c, 
        d = d == undefined ? "." : d, 
        t = t == undefined ? "," : t, 
        s = n < 0 ? "-" : "", 
        i = String(parseInt(n = Math.abs(Number(n) || 0).toFixed(c))), 
        j = (j = i.length) > 3 ? j % 3 : 0;
       return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
     };
     
    function gradientColor(startColor, endColor, evValue) {
        var startColorDef = {
            'r': parseInt(startColor.slice(1,3), 16),
            'g': parseInt(startColor.slice(3,5), 16),
            'b': parseInt(startColor.slice(5,7), 16)
        }
        var endColorDef = {
            'r': parseInt(endColor.slice(1,3), 16),
            'g': parseInt(endColor.slice(3,5), 16),
            'b': parseInt(endColor.slice(5,7), 16)        
        }
        diffR = endColorDef['r'] - startColorDef['r'];
        diffG = endColorDef['g'] - startColorDef['g'];
        diffB = endColorDef['b'] - startColorDef['b'];

        while (evValue > 100){
            evValue = evValue/10;
        }
        
        newR = Math.round(startColorDef['r'] + ((diffR * evValue)/100));
        newG = Math.round(startColorDef['g'] + ((diffG * evValue)/100));
        newB = Math.round(startColorDef['b'] + ((diffB * evValue)/100));
        
        return "rgb("+newR+","+newG+","+newB+")";
        
    }
    
    Date.prototype.formatDate = function() {

        var mm = (this.getMonth()+1).toString(); 
        var dd = (this.getDate()).toString();
        if (mm.length<2)
            mm = '0'+mm;
        if (dd.length<2)
            dd = '0'+dd;

        return [this.getFullYear(), mm, dd].join('-');
    };

    Date.prototype.addDays = function(numOfDays) {
        var currDate = new Date(this.valueOf());
        currDate.setDate(currDate.getDate() + numOfDays);
        return currDate;
    }
    
    /*http://javascript.about.com/library/blweekyear.htm*/
    Date.prototype.getWeek = function() {
        var onejan = new Date(this.getFullYear(),0,1);
        var millisecsInDay = 86400000;
        return Math.ceil((((this - onejan) /millisecsInDay) + onejan.getDay()+1)/7);
    };


