var markers = [];
var iterator = 0;
var geocoder;
var map; 
var d = new Date();
var curr_day = d.getDate();
var curr_month = d.getMonth() + 1; //Months are zero based
var curr_year = d.getFullYear();  
var curr_hr=d.getHours()  
var curr_minute=d.getMinutes()

var all_circles=[]

var destination_latlong;

var good_blocks_latlong = [];


var sf_latlong = new google.maps.LatLng(37.7771187, -122.4196396);
var sf_latlong_2 = new google.maps.LatLng(37.7801187, -122.4236396);


function initialize() {
    geocoder = new google.maps.Geocoder();
    var mapOptions = {
        center: new google.maps.LatLng(37.740, -122.440),
        zoom: 12
    };

    console.log("setting up the map");

    map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
}
      
    
function getGoodblocks() { 
    $.getJSON('/getGoodblocks', {lat: destination_latlong[0], lon: destination_latlong[1], num_days: $('#select_days').val(),
               num_hours: $('#select_hours').val(), zone:$('#select_zone').val(), current_time : $('#datetimepicker').val()}, 
            function(list_of_good_add) {

            // console.log("Output is = " + list_of_good_add);

            // clear_all_circles
            for (var i = 0; i < all_circles.length; i++) {
                all_circles[i].setMap(null);
            }

            for (var i=0; i < list_of_good_add.length; i++) {  

                lat_c=list_of_good_add[i][1]
                lon_c=list_of_good_add[i][2]

                console.log("Output is = " + lat_c + lon_c);

                console.log("risk = " + list_of_good_add[i][5]);


                if ( list_of_good_add[i][3] == 1 ){

                    all_circles.push(
                        new google.maps.Circle({
                            center: new google.maps.LatLng(lat_c,lon_c),
                            radius: list_of_good_add[i][6], 
                            map: map,
                            strokeColor: list_of_good_add[i][4],
                            strokeOpacity: 1,
                            strokeWeight: 2,
                            fillColor: list_of_good_add[i][4],
                            fillOpacity: list_of_good_add[i][7], 
                            title:"Hello round!"
                        })
                    )
                }else{
                    all_circles.push(
                        new google.maps.Circle({
                            center: new google.maps.LatLng(lat_c,lon_c),
                            radius: 7, 
                            map: map,
                            strokeColor: '#606060', // #993333,
                            strokeOpacity: .8,
                            strokeWeight: 2,
                            fillColor: '#606060',
                            fillOpacity: 0.6,
                            title:"Hello round!"
                        })
                    )                    
                }
            }
        });
};


function convert_dest_addr_to_latlong() {  
    // destination

    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }

    var sAddress = $('#inputTextAddress').val(); 
    if (! sAddress.match(/(.*)San Francisco(.*)/i) ) { sAddress+=", San Francisco" }
    geocoder.geocode({ 'address': sAddress }, function (results, status){
      if (status == google.maps.GeocoderStatus.OK) {
        for (var i=0; i<results.length; i++) {
            //  console.log(results[i]['formatted_address']);
            if ( results[i]['formatted_address'].match(/(.*)San Francisco(.*)/i) ) {
                map.setCenter(results[i].geometry.location); map.setZoom(17)
                
                markers.push( new google.maps.Marker({  map: map,  position: results[i].geometry.location }))

                destination_latlong=[results[i]['geometry']['location']['d'],results[i]['geometry']['location']['e']]
                getGoodblocks()
                return
            }
        }              
      }
      else {
        alert("Geocode was not successful for the following reason: " + status);
        console.log("Geocoding failed: " + status);
      }
    })
} 



$(function() {
    console.log( "ready as well!" ); 
    $('#inputButtonGeocode').click(function() {
        console.log($('#inputTextAddress').val());
        console.log($('#datetimepicker').val()); 
        console.log($('#select_days').val());
        convert_dest_addr_to_latlong()         
    });

    $("#ex_1").click(function() {  
        $('#inputTextAddress').val('2450 turk')
        $('#datetimepicker').val('2014/01/27 20:50')
        $('#select_days').val('2 days')
        $('#select_hours').val('22hr:30min')

    }); 

    $("#ex_2").click(function() {  
        $('#inputTextAddress').val('2500 vallejo st')
        $('#datetimepicker').val('2014/01/27 20:50')
        $('#select_days').val('0 day')
        $('#select_hours').val('22hr:30min')
    }); 

    $("#ex_3").click(function() {  
        $('#inputTextAddress').val('2799 geary blvd')
        $('#datetimepicker').val('2014/01/27 20:50')
        $('#select_days').val('1 day')
        $('#select_hours').val('10hr:30min')
    }); 


}); 
    // 1000 franklin st

    //  
  
    bounds: new google.maps.LatLngBounds(
      new google.maps.LatLng(33.671068, -116.25128),
      new google.maps.LatLng(33.685282, -116.233942))
      
      
      
      
        

google.maps.event.addDomListener(window, 'load', initialize());


 