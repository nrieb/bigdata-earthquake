// @author nrieb

var map;
var SAMPLE_SIZE = 100000

//See https://stackoverflow.com/questions/439463/how-to-get-get-and-post-variables-with-jquery
function getQueryParams(qs) {
    qs = qs.split("+").join(" ");
    var params = {},
        tokens,
        re = /[?&]?([^=]+)=([^&]*)/g;

    while (tokens = re.exec(qs)) {
        params[decodeURIComponent(tokens[1])]
            = decodeURIComponent(tokens[2]);
    }

    return params;
}

// See https://stackoverflow.com/questions/11935175/sampling-a-random-subset-from-an-array
function getRandomSubarray(arr, size) {
    var shuffled = arr.slice(0), i = arr.length, min = i - size, temp, index;
    if (min < 0)
	min = 0
    while (i-- > min) {
        index = Math.floor((i + 1) * Math.random());
        temp = shuffled[index];
        shuffled[index] = shuffled[i];
        shuffled[i] = temp;
    }
    return shuffled.slice(min);
}

function success(data, textStatus, jqXHR) {
    var heatMapData = [];
    console.log("got a success");
    for (tripid in data)
	for (i in data[tripid])
		heatMapData.push(new google.maps.LatLng(data[tripid][i][1],
							data[tripid][i][2]))
    sample = getRandomSubarray(heatMapData, SAMPLE_SIZE)
    var heatmap = new google.maps.visualization.HeatmapLayer({
	data: sample,
	radius: 7
    });
    heatmap.setMap(map)
}

function initialize() {
    Math.seedrandom('a better seed?')
    var $_GET = getQueryParams(document.location.search);
    var url = "http://cs.unm.edu/~lnunno/uber-viz/json/fileLoader.php?name="
    var timeOfDay = "day"
    if ("time" in $_GET) {
	if ($_GET["time"] == "day") {
	    timeOfDay = "day"
	}
        else
	{
	    timeOfDay = "night"
	}
    }
    console.log(url + timeOfDay + ".json")
    $.ajax({
        url: url + timeOfDay + ".json",
        dataType:"json",
        async: true,
	success: success,
    });

    var sanFrancisco = new google.maps.LatLng(37.774546, -122.433523);
    
    map = new google.maps.Map(document.getElementById('map_canvas'), {
	center: sanFrancisco,
	zoom: 13,
	zoomControl: true,
	mapTypeId: google.maps.MapTypeId.ROADMAP,
    });
}
