"""
input: (name, glottocode) pairs - may also be read from stdin!
"""
import sys
import itertools
import collections

from shapely.geometry import shape, MultiPolygon, box, Point
from shapely import buffer
from matplotlib import colormaps
from matplotlib.colors import rgb2hex
from pycldf import Dataset
from pycldf.media import MediaTable
from csvw.dsv import reader
from cldfgeojson import MEDIA_TYPE
from clldutils.jsonlib import dump
from pycldf.cli_util import add_catalog_spec

from cldfbench_languageatlasofthepacificarea import Dataset

NAME_COL = 'Name'
GLOTTOCODE_COL = 'Glottocode'

#
# FIXME: shorten names (remove "(Papua New Guinea)", etc.)
# Configurable:
# - add other Glottolog langs in area.
# - add other langs in separate layer.
#

def Languages(s):
    if s == '-':
        lines = [l.strip() for l in sys.stdin.readlines()]
        return [dict(Name=r[0], Glottocode=r[1]) for r in reader(lines)]
    return list(reader(s, dicts=True))


def register(parser):
    add_catalog_spec(parser, 'glottolog')
    parser.add_argument('--name-column', default=NAME_COL, type=str)
    parser.add_argument('--glottocode-column', default=GLOTTOCODE_COL, type=str)
    parser.add_argument('input', type=Languages)


def run(args):
    langs = []
    try:
        for d in args.input:
            d[NAME_COL] = d.pop(args.name_column)
            d[GLOTTOCODE_COL] = d.pop(args.glottocode_column)
            langs.append(d)
    except KeyError:
        raise
    ds = Dataset()
    _run(args, ds.cldf_reader(), langs)


def get_classification(lg):
    cl = [gc for _, gc, _ in lg.lineage]
    if cl and cl[0].startswith('aust1'):
        return ('Austronesian', cl[6], cl)
    return ('Other', cl[0] if cl else lg.id, cl)


def _run(args, ds, langs):
    classification = {}
    media = MediaTable(ds)
    geojson = {f.id: f.read_json() for f in media if f.mimetype == MEDIA_TYPE}
    geojson_languages = {f['properties']['cldf:languageReference']: f for f in geojson['languages']['features']}
    geojson_ecai = {f['id']: f for f in geojson['ecai']['features']}

    gl = args.glottolog.api
    glangs = {l.id: l for l in gl.languoids()}

    whlangs = {l['Glottocode']: l for l in ds['LanguageTable']}

    whshapes = collections.defaultdict(list)
    for l in ds['ContributionTable']:
        if l['Properties'] and 'Glottocodes' in l['Properties']:
            for gc in l['Properties']['Glottocodes']:
                whshapes[gc].append(l)
    #
    # FIXME: merge whshapes?!
    #

    def get_feature(gc):
        # Lookup LanguageTable, and then ContributionTable to collect shapes, then Glottolog for point coordinates.
        cl = get_classification(glangs[gc])
        classification[gc] = (cl[0], cl[1])

        if gc in whlangs:
            feature = geojson_languages[gc]
        elif gc in whshapes:
            assert len(whshapes[gc]) == 1
            feature = geojson_ecai[whshapes[gc][0]['ID']]
        else:
            lg = glangs[gc]
            feature = {
                'type': 'Feature',
                # FIXME: make buffer distance configurable!
                'geometry': buffer(Point(lg.longitude, lg.latitude), 0.02).__geo_interface__,
                'properties': {
                    'cldf:languageReference': row['Glottocode']
                },
            }
        feature['properties'].update(
            title=glangs[gc].name.split('(')[0].strip(),  # FIXME: configurable!
            family=cl[0],
            group=cl[1],
            classification='{} - {}'.format(cl[0], glangs[cl[1]].name),
        )
        return feature, cl[2]

    features, gcs = [], set()
    for row in langs:
        feature, lineage = get_feature(row['Glottocode'])
        gcs.add(row['Glottocode'])
        gcs |= set(lineage)
        feature['properties'].update(title=row[NAME_COL])
        features.append(feature)

    bb = MultiPolygon(list(itertools.chain(*[
        shape(f['geometry']).geoms if isinstance(shape(f['geometry']), MultiPolygon) else [shape(f['geometry'])]
        for f in features])))
    boundingbox = buffer(box(*bb.bounds), 0.2)

    exclude = {'indo1319', 'pidg1258'}
    other = []
    for l in glangs.values():
        if l.latitude \
                and l.id not in gcs \
                and l.level == gl.languoid_levels.language \
                and ((not l.lineage) or (l.lineage[0][1] not in exclude)):
            p = Point(l.longitude, l.latitude)
            if boundingbox.contains(p):
                features.append(get_feature(l.id)[0])
                #other.append(get_feature(l.id)[0])

    colors = {}
    for fam, vals in itertools.groupby(sorted(set(classification.values())), lambda i: i[0]):
        vals = [v[1] for v in vals]

        for i, v in enumerate(vals, start=1):
            colors[(fam, v)] = rgb2hex(colormaps['Oranges' if fam == 'Austronesian' else 'Greys'](i / (len(vals) + 1)))

    for f in features:
        color = colors[(f['properties']['family'], f['properties']['group'])]
        f['properties'].update({
            'stroke': '#000',
            'fill': color,
            'fill-opacity': 0.9,
        })
    dump(dict(type='FeatureCollection', features=features), 'paper.geojson', indent=2)




    for f in other:
        color = colors[(f['properties']['family'], f['properties']['group'])]
        f['properties'].update({
            #'marker-color': color,
            #'marker-size': 'small',
            'stroke': '#000',
            'fill': color,
            'fill-opacity': 0.9,
        })
    dump(dict(type='FeatureCollection', features=other), 'glottolog.geojson', indent=2)

    dump(dict(type='FeatureCollection', features=other + features), 'full.geojson')
