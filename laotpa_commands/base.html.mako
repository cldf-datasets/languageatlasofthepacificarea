<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css" integrity="sha384-X38yfunGUhNzHpBaEBsWLO+A0HDYOQi8ufWDkZ0k9e0eXz/tH3II7uKZ9msv++Ls" crossorigin="anonymous">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
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
    </style>
    <%block name="head"/>
</head>

<body>
<div class="vh pure-g">
    <div class="vh pure-u-${w}-5">
        <div id='map'></div>
    </div>
    <div class="vh pure-u-${5 - w}-5">
        <table id="table" class="pure-table">
            <%block name="table"/>
        </table>
    </div>
</div>
${self.body()}
</body>
</html>