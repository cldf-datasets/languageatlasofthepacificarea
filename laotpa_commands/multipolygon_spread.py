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

from shapely.geometry import shape
from shapely import distance
from cldfbench_languageatlasofthepacificarea import Dataset
from clldutils.jsonlib import load, dump
from cldfgeojson import feature_collection
from tqdm import tqdm

from .validation import plot, iter_ne_shapes


def polynesian(polys):
    c = polys[0].centroid
    return c.x > 163 or c.x < 0


def run(args):
    ds = Dataset()
    ne10 = [shape(shp['geometry']) for shp in iter_ne_shapes('ne_10m_ocean')]

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
    _plot(x, y, c, labels)


def _plot(x, y, c, labels):
    with plot(
        'Spread of polygons per language',
        'Number of polygons',
        'Standard deviation of distances between polygons',
        legend_loc='upper right',
        legend_items={'r': 'Non-coastal language', 'b': 'Coastal language'},
    ) as ax:
        ax.scatter(x, y, c=c)
        for label, x_, y_ in labels:
            ax.annotate(label, (x_, y_))
