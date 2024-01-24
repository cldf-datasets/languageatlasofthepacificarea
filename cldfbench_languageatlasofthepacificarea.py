import copy
import pathlib
import functools
import itertools
import collections

import geopandas
from shapely.geometry import shape, Polygon
from cldfbench import Dataset as BaseDataset


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


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "languageatlasofthepacificarea"

    @functools.cached_property
    def languages(self):
        return collections.OrderedDict(
            [(lg['Name'], lg) for lg in self.etc_dir.read_csv('languages.csv', dicts=True)])

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    def cmd_download(self, args):
        self.raw_dir.download_and_unpack(
            'https://ecaidata.org/dataset/209cb079-2270-4016-bc8d-f6c7835779c5/'
            'resource/b5095d0f-7429-445d-a507-916aae5398ba/download/languagemap040429.zip')

    def iter_geojson_features(self):
        features = {}
        properties = []

        for i, feature in enumerate(geopandas.read_file(
                str(self.raw_dir / 'languagemap_040102.shp')).__geo_interface__['features']):
            props = norm({k: v for k, v in feature['properties'].items() if v})
            if 'LANGUAGE' in props:
                properties.append(props)

                if props['LANGUAGE'] in features:
                    features[props['LANGUAGE']]['geometry']['coordinates'].extend(multi_polygon(feature))
                else:
                    features[props['LANGUAGE']] = {
                        'id': str(i),
                        'type': 'Feature',
                        'properties': {'title': props['LANGUAGE']},
                        'geometry': {
                            'type': 'MultiPolygon',
                            'coordinates': multi_polygon(feature)
                        }
                    }

        for lname, props in itertools.groupby(
                sorted(properties, key=lambda f: f['LANGUAGE']),
                lambda f: f['LANGUAGE']):
            f = features[lname]
            props = list(props)
            f['properties']['countries'] = sorted(set(p['COUNTRY_NAME'] for p in props if 'COUNTRY_NAME' in p))
            f['properties']['sovereigns'] = sorted(set(p['SOVEREIGN'] for p in props if 'SOVEREIGN' in p))
            f['properties']['islands'] = sorted(set(p['ISLAND_NAME'] for p in props if 'ISLAND_NAME' in p))

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
            yield lname, f

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
