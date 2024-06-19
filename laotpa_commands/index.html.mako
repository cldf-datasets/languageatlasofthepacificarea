<%inherit file="base.html.mako"/>
<%block name="head">
<title>Language Atlas of the Pacific Area</title>
</%block>
<%block name="table">
<thead>
<tr>
    <th>No</th>
    <th>Title</th>
</tr>
</thead>
<tbody>
% for leaf in leaves:
<tr>
    <td><a href="#" title="click to highlight the area in the map" onclick="highlight('${leaf.id}')">${leaf.id}</a></td>
    <td><a title="click to open the Atlas leaf" href="${leaf.id}.html">${leaf.cldf.name}</a></td>
</tr>
% endfor
</tbody>
</%block>
<script>
    const layers = {};
    const featuregroups = {};
    const map = L.map('map').setView([0, 180], 2);
    const leaves = ${leavesgeojson};

    function highlight(lid) {
        for (id in layers) {
            if (id == lid) {
                map.fitBounds(featuregroups[lid].getBounds());
                layers[id].eachLayer(function (layer) {
                    layer.setStyle({color: 'red', fillColor :'red', 'opacity': 0.2});
                    layer.bringToFront();
                });
            } else {
                layers[id].eachLayer(function (layer) {layer.setStyle({color: 'blue', fillColor :'blue', 'opacity': 0.1})});
            }
        }
    }

    function onEachFeature(feature, layer) {
        featuregroups[feature.properties.id] = L.featureGroup([layer]).addTo(map);
        layers[feature.properties.id] = L.layerGroup([layer]).addTo(map);
        layer.bindTooltip(feature.properties.id + ': ' + feature.properties.title);
        layer.setStyle({color: 'blue', fillColor :'blue', 'opacity': 0.1});
        layer.on('click', function() {window.location.assign(feature.properties.url)});
    }
    var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        osmAttrib = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        osm = L.tileLayer(osmUrl, { maxZoom: 18, attribution: osmAttrib });
    osm.addTo(map);
    L.geoJSON(leaves, {onEachFeature: onEachFeature}).addTo(map);
</script>