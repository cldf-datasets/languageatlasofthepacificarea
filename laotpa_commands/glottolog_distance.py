"""
A measure how accurately the shapes of the dataset match the geographic information from Glottolog.
"""
from shapely.geometry import shape
from clldutils.clilib import PathType
from clldutils.path import TemporaryDirectory
from clldutils.jsonlib import load, dump
from pycldf.ext.discovery import get_dataset
from csvw.dsv import UnicodeWriter

from cldfbench_languageatlasofthepacificarea import Dataset
from .validation import plot


def register(parser):
    parser.add_argument('glottolog_cldf', type=PathType(type='dir'))


def run(args):
    ds = Dataset()

    with TemporaryDirectory() as tmp:
        gl = get_dataset(args.glottolog_cldf, tmp)
        gl_coords = {
            l.id: l.as_geojson_feature for l in gl.objects('LanguageTable') if l.cldf.longitude}
        #
        # FIXME: get number of countries as proxy for "big" language.
        #

    #
    # FIXME: get number of polygons as proxy for "spread out" language
    # again a scatterplot!
    #
    outliers, labels = [], []
    dists = []
    for f in load(ds.cldf_dir / 'languages.geojson')['features']:
        if f['properties']['cldf:languageReference'] in gl_coords:
            shp = shape(f['geometry'])
            npolys = len(f['geometry']['coordinates']) if f['geometry']['type'] == 'MultiPolygon' else 1

            gl_coord = shape(gl_coords[f['properties']['cldf:languageReference']]['geometry'])
            if shp.contains(gl_coord):
                dists.append((f['properties']['cldf:languageReference'], True, 0))
            elif shp.convex_hull.contains(gl_coord):
                dists.append((f['properties']['cldf:languageReference'], False, 0))
            else:
                dist = shp.distance(gl_coord)
                if dist > 180:
                    dist = abs(dist - 360)
                dists.append((f['properties']['cldf:languageReference'], False, dist))
                outliers.append((npolys, dist))
                if dist > 2:
                    labels.append((f['properties']['title'], npolys, dist))
                #if 0 < dist < 0.5:
                #    # i.e. non-zero distances less than ~55km (half of the distance between degrees of
                #    # longitude around the equator)
                #    dists.append(dist)
                #if dist >= 0.5:
                #    # Are manually investigated!
                #    outliers[f['properties']['cldf:languageReference']] = (math.ceil(dist), [gl_coord, f])
            #if dist > 1:
            #    print('{}\t{}\t{}'.format(f['properties']['cldf:languageReference'], f['properties']['title'], dist))
        #else:
        #    print('-- {}\t{}'.format(f['properties']['cldf:languageReference'], f['properties']['title']))
    with UnicodeWriter(ds.etc_dir / 'glottolog_distances.csv') as writer:
        writer.writerow(['Glottocode', 'Contained', 'Distances'])
        writer.writerows(dists)
    #subprocess.check_call(['csvstat', str(ds.etc_dir / 'glottolog_distances.csv')])
    _plot([i[0] for i in outliers], [i[1] for i in outliers], labels)


def _plot(x, y, labels):#, c, labels):
    with plot(
        'Distance from Glottolog coordinate',
        'Number of polygons',
        'Distance',
    ) as ax:
        ax.scatter(x, y)
        for label, x_, y_ in labels:
            ax.annotate(label, (x_, y_))
