# Configuration directory

This directory contains "configuration" data, i.e. data which helps with and
guides the conversion of the raw data to CLDF.


## Mapping languages to Glottolog

Make sure you have the dependcies installed:
```shell
pip install -e .
```

Run
```shell
cldfbench laotpa.geojson PATH/TO/glottolog-cldf/cldf/languages.csv
```
to create a GeoJSON file including unmapped polygons and Glottolog language markers.

Open this file in https://geojson.io/

Assign Glottocodes to polygons by appending the appropriate Glottocode to the polygons `title` property.

Save the data in GeoJSON format.

Add the new Glottocodes to `etc/languages.csv` by running
```shell
cldfbench laotpa.mergeglottocodes ~/Downloads/map.geojson
```

Commit and push:
```shell
git commit -m"more glottocodes" etc/languages.csv
```
