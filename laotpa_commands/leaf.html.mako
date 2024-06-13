<%inherit file="base.html.mako"/>
<%block name="head">
<title>${title}</title>
<style>
    body, html, .vh {
        height: 100vh;
    }
    title {
        text-align: center;
        width: 100%;
    }
    #table {
        display: block;
        margin-left: 10px;
        margin-right: 10px;
        height: 100%;
        overflow-y: scroll;
    }
    #map {
        height: 100%;
        width: 100%;
    }
    .leaflet-range-control {
    background-color: #fff;
}
.leaflet-range-control.horizontal {
    height: 26px;
    padding-right: 5px;
}
.leaflet-range-control .leaflet-range-icon {
    display: inline-block;
    float: left;
    width: 26px;
    height: 26px;
    background-image: url('data:image/svg+xml;base64,PHN2ZyBmaWxsPSIjMDAwMDAwIiBoZWlnaHQ9IjI0IiB2aWV3Qm94PSIwIDAgMjQgMjQiIHdpZHRoPSIyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4NCiAgICA8cGF0aCBkPSJNMCAwaDI0djI0SDB6IiBmaWxsPSJub25lIi8+DQogICAgPHBhdGggZD0iTTE1IDE3djJoMnYtMmgydi0yaC0ydi0yaC0ydjJoLTJ2Mmgyem01LTE1SDRjLTEuMSAwLTIgLjktMiAydjE2YzAgMS4xLjkgMiAyIDJoMTZjMS4xIDAgMi0uOSAyLTJWNGMwLTEuMS0uOS0yLTItMnpNNSA1aDZ2Mkg1VjV6bTE1IDE1SDRMMjAgNHYxNnoiLz4NCjwvc3ZnPg==');
}
.leaflet-range-control input[type=range] {
    display: block;
    cursor: pointer;
    width: 100%;
    margin: 0px;
}
.leaflet-range-control input[type=range][orient=horizontal] {
    margin-top: 5px;
    width: 150px;
}
</style>
</%block>
<div class="vh pure-g">
    <div class="vh pure-u-4-5">
        <div id='map'></div>
    </div>
    <div class="vh pure-u-1-5">
        <table id="table" class="pure-table">
            <thead>
            <tr>
                <th>Language</th>
            </tr>
            </thead>
            <tbody>
            % for lang in languages:
            <tr>
                <td><a onclick="highlight(`${lang.id}`)">${lang.cldf.name}</a></td>
            </tr>
            % endfor
            </tbody>
        </table>
    </div>
</div>
<script>
    var polygons,
        styles = {
        'regular': {
            'color': '#0000ff',
            'weight': 2,
            'opacity': 0.1},
        'highlight': {
            'color': '#ff0000',
            'weight': 2,
            'opacity': 0.7
        }},
        langlayers = {};

    function onEachFeature(feature, layer) {
        var popup = '<strong>' + feature.properties.title + '</strong><br>';
        popup += 'Glottocode <a href="https://glottolog.org/resource/languoid/id/' + feature.properties['cldf:languageReference'] + '">' + feature.properties['cldf:languageReference'] + '</a><br>';
        popup += '<p>Aggregated from shapes for</p>';
        popup += '<ul>';
        for (const shape of feature.properties.shapes) {
            popup += '<li>' + shape + '</li>';
        }
        popup += '</ul>';
        layer.bindTooltip(feature.properties.title);
        layer.bindPopup(popup);
        layer.setStyle(styles.regular);
        langlayers[feature.properties['cldf:languageReference']] = layer;
    }
    const langs = ${geojson};
	const map = L.map('map').setView([37.8, -96], 4);
	const latLngBounds = L.latLngBounds([[${lat1}, ${lon1}],[${lat2}, ${lon2}]]);

    function highlight(lid) {
        var layer;
        for (id in langlayers) {
            layer = langlayers[id];
            if (id === lid) {
                layer.setStyle(styles.highlight);
                map.panTo(layer.getBounds().getCenter())
            } else {
                layer.setStyle(styles.regular);
            }
        }
    }

    L.tileLayer(
        'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            maxZoom: 18,
            attribution:'&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors'}
    ).addTo(map);
    const imageOverlay = L.imageOverlay('${img}', latLngBounds, {
        opacity: 0.5,
        interactive: true
    }).addTo(map);
    if (langs) {
        polygons = L.geoJSON(langs, {onEachFeature: onEachFeature}).addTo(map);
    }
    L.control.layers(
        [],
        {
            'Atlas leaf ${title}': imageOverlay,
            'Language polygons': polygons},
        {collapsed: false}).addTo(map);
	map.fitBounds(latLngBounds);

    L.Control.Range = L.Control.extend({
    options: {
        position: 'topright',
        min: 0,
        max: 100,
        value: 0,
        step: 1,
        orient: 'vertical',
        iconClass: 'leaflet-range-icon',
        icon: true
    },

    onAdd: function(map) {
        var container = L.DomUtil.create('div', 'leaflet-range-control leaflet-bar ' + this.options.orient);
        if (this.options.icon) {
          L.DomUtil.create('span', this.options.iconClass, container);
        };
        var slider = L.DomUtil.create('input', '', container);
        slider.type = 'range';
        slider.setAttribute('orient', this.options.orient);
        slider.min = this.options.min;
        slider.max = this.options.max;
        slider.step = this.options.step;
        slider.value = this.options.value;

        L.DomEvent.on(slider, 'mousedown mouseup click touchstart', L.DomEvent.stopPropagation);

        /* IE11 seems to process events in the wrong order, so the only way to prevent map movement while dragging the
         * slider is to disable map dragging when the cursor enters the slider (by the time the mousedown event fires
         * it's too late becuase the event seems to go to the map first, which results in any subsequent motion
         * resulting in map movement even after map.dragging.disable() is called.
         */
        L.DomEvent.on(slider, 'mouseenter', function(e) {
            map.dragging.disable()
        });
        L.DomEvent.on(slider, 'mouseleave', function(e) {
            map.dragging.enable();
        });

        L.DomEvent.on(slider, 'change', function(e) {
            this.fire('change', {value: e.target.value});
        }.bind(this));

        L.DomEvent.on(slider, 'input', function(e) {
            this.fire('input', {value: e.target.value});
        }.bind(this));

        this._slider = slider;
        this._container = container;

        return this._container;
    },

    setValue: function(value) {
        this.options.value = value;
        this._slider.value = value;
    },

});

L.Control.Range.include(L.Evented.prototype)

L.control.range = function (options) {
  return new L.Control.Range(options);
};

   var slider = L.control.range({
    position: 'topright',
    min: 0,
    max: 100,
    value: 50,
    step: 1,
    orient: 'horizontal',
    iconClass: 'leaflet-range-icon',
    icon: true
});

slider.on('input change', function(e) {
   imageOverlay.setOpacity(e.value / 100);
});

    map.addControl(slider);
</script>
