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
    assert ds.languages

    for feature in load(args.geojson)['features']:
        if feature['geometry']['type'] != 'Point':
            prop = 'title'
            match = Glottocode.pattern.search(feature['properties']['title'])
            if not match:
                if isinstance(feature['properties']['islands'], str):
                    match = Glottocode.pattern.search(feature['properties']['islands'])
                    if match:
                        prop = 'islands'
            if match:
                if prop == 'title':
                    lname = feature['properties']['title'][:match.start()].strip()
                else:
                    lname = feature['properties']['title'].strip()

                gc = feature['properties'][prop][match.start():match.end()]
                print('{} -> {}'.format(lname, gc))
                if ds.languages[lname]['Glottocode']:
                    assert ds.languages[lname]['Glottocode'] == gc
                ds.languages[lname]['Glottocode'] = gc

    with UnicodeWriter(ds.etc_dir / 'languages.csv') as w:
        for i, lg in enumerate(ds.languages.values()):
            if not i:
                w.writerow(lg.keys())
            w.writerow(lg.values())
