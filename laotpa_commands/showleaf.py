"""
Show an Atlas leaf overlaid on a web map.
"""
import json
import string
import pathlib
import itertools
import webbrowser

from pycldf.media import File
from pycldf.orm import Language
from clldutils.misc import data_url

from cldfbench_languageatlasofthepacificarea import Dataset


def register(parser):
    parser.add_argument('leaf')


def run(args):
    cldf = Dataset().cldf_reader()

    leaf = cldf.get_object('ContributionTable', args.leaf)
    print(leaf.cldf.name)

    img, geojson = None, None
    for f in leaf.all_related('mediaReference'):
        if f.id.endswith('_web'):
            img = File.from_dataset(cldf, f)
        if f.id.endswith('_geojson'):
            geojson = File.from_dataset(cldf, f)
    assert img and geojson

    bounds = next(itertools.dropwhile(
        lambda f: f['properties']['id'] != 'bounds', geojson.read_json()['features']))['bbox']
    print(bounds)

    langs = []
    for lang in cldf.objects('LanguageTable'):
        if lang.data['Glottolog_Languoid_Level'] == 'language':
            if args.leaf in {c.id for c in lang.all_related('contributionReference')}:
                langs.append(lang.speaker_area_as_geojson_feature)

    # get languages for a table
    html = string.Template(
        pathlib.Path(__file__).parent.joinpath('template.html').read_text(encoding='utf8'))
    pathlib.Path('index.html').write_text(html.substitute(
        title=leaf.cldf.name,
        img=data_url(img.read(), 'image/jpeg'),
        langs=json.dumps(dict(type='FeatureCollection', features=langs)),
        lat1=bounds[1],
        lon1=bounds[0],
        lat2=bounds[3],
        lon2=bounds[2],
    ), encoding='utf8')

    webbrowser.open('index.html')
