# Configuration directory

This directory contains "configuration" data, i.e. data which helps with and
guides the conversion of the raw data to CLDF.


## Mapping languages to Glottolog

Run
```shell
cldfbench laotpa.geojson
```
to create a GeoJSON file including unmapped polygons and Glottolog language markers.

Open this file in https://geojson.io/

Assign Glottocodes to polygons by appending the appropriate Glottocode to the polygons `title` property.

Save the data in GeoJSON format.

Add the new Glottocodes to `etc/languages.csv` by running
```shell
cldfbench laotpa.mergeglottocodes ~/Downloads/map.geojson
```
