"""
Compute distances between polygons mapped to the same language.

This metric provides information about the plausibility of Glottolog matches.
E.g. for an ambiguous dialect name like "Bime", in Indonesia, if all polygons were matched to the
same Glottocode, one language would have an "outlier" polygon, resulting in a high standard
deviation for the distances between polygons for this language.
"""
import pathlib
import itertools
import statistics

import fiona
from shapely.geometry import shape
from shapely import distance
from cldfbench_languageatlasofthepacificarea import Dataset
from clldutils.jsonlib import load, dump
from cldfgeojson import feature_collection
import matplotlib.pyplot as plt
from tqdm import tqdm
import matplotlib.patches as mpatches


def polynesian(polys):
    c = polys[0].centroid
    return c.x > 163 or c.x < 0


def run(args):
    ds = Dataset()

    ne10 = []
    for shapefile in ['ne_10m_ocean']:
        for shp in fiona.open(
                str(pathlib.Path(__file__).parent / 'naturalearth' / '{}.shp'.format(shapefile))):
            ne10.append(shape(shp['geometry']))

    x, y, c, labels = [], [], [], []
    spread_out = []
    for f in tqdm(load(ds.cldf_dir / 'languages.geojson')['features']):
        if f['geometry']['type'] == 'MultiPolygon':
            polys = [
                shape(dict(type='Polygon', coordinates=poly))
                for poly in f['geometry']['coordinates']]
            if len(polys) > 2:
                mdist = statistics.stdev(p1.distance(p2) for p1, p2 in itertools.combinations(polys, 2))
            else:
                mdist = max(p1.distance(p2) for p1, p2 in itertools.combinations(polys, 2))
            if mdist < 14:
                coastal = polynesian(polys) or all(min(0 if p.intersects(l) else distance(p, l) for l in ne10) < 0.005 for p in polys)  # ~< 500m
                x.append(len(polys))
                y.append(mdist)
                c.append('b' if coastal else 'r')
                if mdist > 2:
                    if not coastal:
                        labels.append((f['properties']['title'], len(polys), mdist))
                    else:
                        #print(len(polys), mdist, f['properties'])
                        pass
                    spread_out.append(f)

                    # Mandar: OK, coastal language in Sulawesi
                    # Tavoyan: OK, coastal language in Myanmar
                    # Vietnamese: big language with short distances between polygons compared to the size of the polygons
                    # Tausug: OK, coastal language in north borneo, philippines
            else:
                assert f['properties']['title'] in [
                    'Tuvalu',  # Crosses the antimeridian.
                    'Ramoaaina',  # ...
                    'Mangaia-Old Rapa',
                ]
                #print(f['properties'])

    dump(feature_collection(spread_out), pathlib.Path('spread_out.geojson'))
    plot(x, y, c, labels)


def plot(x, y, c, labels):
    fig, ax = plt.subplots()
    ax.scatter(
        x,
        y,
        c=c
    )
    ax.set_xlabel(r'Number of polygons', fontsize=15)
    ax.set_ylabel('Standard deviation of distances between polygons', fontsize=15)
    ax.set_title('Spread of polygons per language')
    for label, x_, y_ in labels:
        ax.annotate(label, (x_, y_))
    red_patch = mpatches.Patch(color='r', label=r'Non-coastal language')
    blue_patch = mpatches.Patch(color='b', label=r'Coastal language')
    ax.legend(handles=[blue_patch, red_patch], loc='upper right')
    ax.grid(True)
    fig.tight_layout()
    plt.show()
