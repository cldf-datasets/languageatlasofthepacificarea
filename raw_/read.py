import copy
import itertools
import collections

import shapely
from shapely.geometry import shape, Polygon
import geopandas

from csvw.dsv import UnicodeWriter, reader
from clldutils.jsonlib import dump


def norm(d):
    for k in ['ISLAND_NAM', 'ISLAND_NA_', 'ISL_NAM']:
        if k in d:
            d['ISLAND_NAME'] = d.pop(k)
    if 'CNTRY_NAME' in d:
        d['COUNTRY_NAME'] = d.pop('CNTRY_NAME')
        if d['COUNTRY_NAME'] == 'Tailand':
            d['COUNTRY_NAME'] = 'Thailand'
    if 'SOVEREIGN' in d and 'COUNTRY_NAME' not in d:
        if d['SOVEREIGN'] == 'Australia':
            d['COUNTRY_NAME'] = 'Australia'
    if d.get('LANGUAGE', '').startswith('Uninhabite'):
        del d['LANGUAGE']
    if d.get('LANGUAGE', '').startswith('Unclassified'):
        del d['LANGUAGE']
    for v in d.values():
        assert ';' not in v
    return d


def multi_polygon(f):
    if f['geometry']['type'] == 'Polygon':
        return copy.copy([f['geometry']['coordinates']])
    assert f['geometry']['type'] == 'MultiPolygon'
    return copy.copy(f['geometry']['coordinates'])


if __name__ == '__main__':
    fields = collections.Counter()
    features = []
    polys = collections.defaultdict(list)
    data = geopandas.read_file('languagemap_040102.shp')
    data_proj = data.copy()
    #print(data['geometry'])
    #data_proj['geometry'] = data_proj['geometry'].to_crs(epsg=4326)
    #data_proj.crs = from_epsg(4326)

    for i, feature in enumerate(data.__geo_interface__['features']):
        #print(feature['properties']['LANGUAGE'])
        #_ = shapely.MultiPolygon(feature)
        props = norm({k: v for k, v in feature['properties'].items() if v})
        if 'LANGUAGE' in props:
            features.append(props)

            if props['LANGUAGE'] in polys:
                polys[props['LANGUAGE']]['geometry']['coordinates'].extend(multi_polygon(feature))
            else:
                polys[props['LANGUAGE']] = {
                    'id': 'x',
                    'type': 'Feature',
                    'properties': {'title': props['LANGUAGE']},
                    'geometry': {
                        'type': 'MultiPolygon',
                        'coordinates': multi_polygon(feature)
                    }
                }

        else:
            continue
        fields.update(props.keys())
        #print({k: v for k, v in feature['properties'].items() if v})
        pass
    #for k, v in fields.most_common():
    #    print(k, v)
    #print(i + 1)
    with UnicodeWriter('../etc/languages.csv') as w:
        w.writerow(['Name', 'Countries', 'Sovereigns', 'Islands', 'Glottocode'])
        for lname, props in itertools.groupby(sorted(features, key=lambda f: f['LANGUAGE']), lambda f: f['LANGUAGE']):
            #props = [{k: v for k, v in p.items() if k in ['LANGUAGE', 'COUNTRY_NAME']} for p in props]
            #if len(props) > 1:
            #    tprops = [str(sorted(p.items())) for p in props]
            #    if len(set(tprops)) != len(props):
            #        for prop in props:
            #            print(prop)
            #            pass
            props = list(props)
            w.writerow([
                lname, 
                '; '.join(sorted(set(p['COUNTRY_NAME'] for p in props if 'COUNTRY_NAME' in p))),
                '; '.join(sorted(set(p['SOVEREIGN'] for p in props if 'SOVEREIGN' in p))),
                '; '.join(sorted(set(p['ISLAND_NAME'] for p in props if 'ISLAND_NAME' in p))),
                '',
            ])

geojson = {
    'type': 'FeatureCollection',
    'features': [],
}
for lname, f in polys.items():
    mp = None
    for i, poly in enumerate(f['geometry']['coordinates']):
        rings = []
        for ring in poly:
            # Some linear rings are self-intersecting. We fix these by taking the 0-distance
            # buffer around the ring instead.
            p = Polygon(ring)
            if not p.is_valid:
                p = p.buffer(0)
                assert p.is_valid
            rings.append(p.__geo_interface__['coordinates'][0])
        p = shape(dict(type='Polygon', coordinates=rings))
        assert p.is_valid
        if mp is None:
            mp = shape(dict(type='MultiPolygon', coordinates=[rings]))
        else:
            mp = mp.union(p)
        assert mp.is_valid
    f['geometry'] = mp.__geo_interface__
    geojson['features'].append(f)


for r in reader('/home/robert/projects/glottolog/glottolog-cldf/cldf/languages.csv', dicts=True):
    if r['Family_ID'] == 'aust1307':
        if (not r['Language_ID']) and r['Longitude']:
            geojson['features'].append({
                'type': 'Feature',
                'properties': {'title': '{} ({})'.format(r['Name'], r['ID'])},
                'geometry': {
    "type": "Point",
    "coordinates": [float(r['Longitude']), float(r['Latitude'])]
  }
            })



dump(geojson, 'languages.geojson', indent=2)

"""
LANGUAGE 4483
CNTRY_NAME 2172
SOVEREIGN 1802
ISLAND_NAM 1086
ISLAND_NA_ 455
ISL_NAM 1
4483

Names:

?
Angan Stock-Level Family
JAGOI Dialects/Assem
Uninhabited Area
Uninhabited Areas
Uninhabites Areas
"""

