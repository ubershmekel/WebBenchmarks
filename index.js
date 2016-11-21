$(function(){
    function isNumeric(num) {
        return !isNaN(num)
    }
    
    function main() {
        // Default sort 7th column descending order
        $("#myTable").tablesorter({sortList: [[7, 1]]});
        
        $("td").each(function(index, el) {
            var $el = $(el);
            var text = $el.text();
            if(isNumeric(text)) {
                var val = +text;
                var red = 255 - val;
                var green = 255;
                var blue = 255 - val;
                $el.css('background-color', 'rgb(' + red + ',' + green + ',' + blue + ')');
            }
        })
    }
    
    main();
});
