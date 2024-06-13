<%inherit file="base.html.mako"/>
<%block name="head">
<title>Language Atlas of the Pacific Area</title>
<style>
    body, html {
        height: 100vh;
    }
    #map {
        height: 100%;
        width: 100%;
    }
</style>
</%block>
<div id='map'></div>
<script>
    const layers = {};
    const map = L.map('map').setView([0, 180], 1);
    const leaves = ${leaves};

    function onEachFeature(feature, layer) {
        layers[feature.properties.title] = L.layerGroup([layer]).addTo(map);
        layer.bindTooltip(feature.properties.title);
        layer.on('click', function() {window.location.assign(feature.properties.url)});
    }
    var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        osmAttrib = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        osm = L.tileLayer(osmUrl, { maxZoom: 18, attribution: osmAttrib });
    osm.addTo(map);
    L.geoJSON(leaves, {onEachFeature: onEachFeature}).addTo(map);
    L.control.layers([], layers, {collapsed: false}).addTo(map);
</script>