# Configuration directory

This directory contains "configuration" data, i.e. data which helps with and
guides the conversion of the raw data to CLDF - or fixes errata. 
It also contains results of validating the resulting CLDF dataset.


## Configuration

- [languages.csv](languages.csv): Table mapping ECAI shapefile metadata to Glottolog languoids.
- [sources.bib](sources.bib): BibTeX file with bibliographical records for the source data.
- [atlas](atlas/): Contains directories for each Atlas leaf, with the following files with the
  results of geo-referencing the ECAI scans:
  - `original.jpg.points`: Text files storing the GCPs (ground control points) recorded with QGIS' georeferencer.
  - `original_modified.tif` or `epsg4326.tif`: Geo-referenced scan in GeoTIFF format, created via QGIS.
  - `leaf.geojson`: GeoJSON file containing one Polygon feature, describing the extent of the geo-referenced
    area on the leaf, excluding inset maps and legend.


## Errata

- [fixes_location.csv](fixes_location.csv): Table specifying translations vectors for misplaced polygons.
- [fixes_metadata.csv](fixes_metadata.csv): Table specifying corrections for metadata of polygons.

In both cases, matching polygons - i.e. the ones to be fixed - are determined via LANGUAGE property
and one contained coordinate.


## Validation data

See [VALIDATION.md](../VALIDATION.md).
