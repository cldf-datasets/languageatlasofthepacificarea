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
    parser.add_argument(
        '--family',
        default='aust1307',
    )


def run(args):
    ds = Dataset()
    geojson = {
        'type': 'FeatureCollection',
        'features': [],
    }
    glottocodes = set()
    i = 0
    for _, lname, feature in ds.iter_geojson_features():
        if not ds.languages[lname]['Glottocode']:
            i += 1
            geojson['features'].append(feature)
        else:
            for gc in ds.languages[lname]['Glottocode'].split():
                glottocodes.add(gc)

    eligible = set()
    for r in reader(args.glottologlanguages.parent / 'values.csv', dicts=True):
        if r['Code_ID'] in ['level-language', 'level-dialect']:
            eligible.add(r['Language_ID'])

    def in_area(r):
        # ol: 20, 90; -24 160
        try:
            lon, lat = float(r['Longitude']), float(r['Latitude'])
        except:
            return False
        return -20 < lat < 20 and 110 < lon < 150

    for r in reader(args.glottologlanguages, dicts=True):
        # if r['Family_ID'] == args.family:  # 'pama1250':  # 'aust1307':
        if in_area(r):
            if r['ID'] not in glottocodes:
                if r['ID'] in eligible:
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
