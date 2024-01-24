"""

"""
from csvw.dsv import reader
from clldutils.jsonlib import dump
from clldutils.clilib import PathType

from cldfbench_languageatlasofthepacificarea import Dataset


def register(parser):
    parser.add_argument(
        'glottologlanguages',
        type=PathType(type='file'),
        help='path to glottolog-cldf/cldf/languages.csv')


def run(args):
    ds = Dataset()
    geojson = {
        'type': 'FeatureCollection',
        'features': [],
    }
    glottocodes = set()
    i = 0
    for lname, feature in ds.iter_geojson_features():
        if not ds.languages[lname]['Glottocode']:
            i += 1
            geojson['features'].append(feature)
        else:
            glottocodes.add(ds.languages[lname]['Glottocode'])

    for r in reader(args.glottologlanguages, dicts=True):
        if r['Family_ID'] == 'aust1307':
            if (not r['Language_ID']) and r['Longitude'] and not r['ID'] in glottocodes:
                geojson['features'].append({
                    'type': 'Feature',
                    'properties': {'title': '{} {}'.format(r['Name'], r['ID'])},
                    'geometry': {
                        "type": "Point",
                        "coordinates": [float(r['Longitude']), float(r['Latitude'])]
                    }
                })

    dump(geojson, 'languages.geojson', indent=2)
    print('{} features written to languages.geojson'.format(i))
