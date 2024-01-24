"""

"""
from clldutils.jsonlib import load
from clldutils.clilib import PathType
from pyglottolog.languoids import Glottocode
from csvw.dsv import UnicodeWriter

from cldfbench_languageatlasofthepacificarea import Dataset


def register(parser):
    parser.add_argument('geojson', type=PathType(type='file'))


def run(args):
    ds = Dataset()
    for feature in load(args.geojson)['features']:
        if feature['geometry']['type'] != 'Point':
            match = Glottocode.pattern.search(feature['properties']['title'])
            if match:
                lname = feature['properties']['title'][:match.start()].strip()
                gc = feature['properties']['title'][match.start():match.end()]
                assert not ds.languages[lname]['Glottocode']
                ds.languages[lname]['Glottocode'] = gc

    with UnicodeWriter(ds.etc_dir / 'languages.csv') as w:
        for i, lg in enumerate(ds.languages.values()):
            if not i:
                w.writerow(lg.keys())
            w.writerow(lg.values())
