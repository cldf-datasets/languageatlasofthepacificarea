"""
Compute distances between polygons mapped to the same language.

This metric provides information about the plausibility of Glottolog matches.
E.g. for an ambiguous dialect name like "Bime", in Indonesia, if all polygons were matched to the
same Glottocode, one language would have an "outlier" polygon, resulting in a high standard
deviation for the distances between polygons for this language.
"""
import typing
import pathlib
import itertools
import statistics
import dataclasses

from shapely.geometry import shape, Polygon
from shapely import distance
from cldfbench_languageatlasofthepacificarea import Dataset
from clldutils.jsonlib import load, dump
from cldfgeojson import feature_collection, Feature
from tqdm import tqdm

from .validation import iter_ne_shapes, validate, is_micronesian, is_polynesian, annotate


def spread(f: Feature) -> typing.Tuple[float, typing.List[Polygon]]:
    assert f['geometry']['type'] == 'MultiPolygon'
    polys = [shape(dict(type='Polygon', coordinates=poly)) for poly in f['geometry']['coordinates']]
    if len(polys) > 2:
        dist = statistics.stdev(p1.distance(p2) for p1, p2 in itertools.combinations(polys, 2))
    elif len(polys) == 2:
        dist = polys[0].distance(polys[1])
    else:
        dist = 0
    return dist, polys


@dataclasses.dataclass
class PolygonSpread:
    glottocode: str
    npolys: int
    spread: float
    coastal: bool
    language: str

    @classmethod
    def from_row(cls, row):
        return cls(row[0], int(row[1]), float(row[2]), row[3] == 'True', row[4])


def register(parser):
    parser.add_argument('--plot-only', action='store_true', default=False)


def run(args):
    ds = Dataset()
    ne10 = [shape(shp['geometry']) for shp in iter_ne_shapes('ne_10m_ocean')]
    spread_out = []

    with validate(
        args,
        ds,
        __file__,
        PolygonSpread,
        _plot,
        (
            'Spread of polygons per language',
            'Number of polygons',
            'Standard deviation of distances between polygons'),
        plot_kw=dict(
            legend_loc='upper right',
            legend_items={'r': 'Non-coastal language', 'b': 'Coastal language'}),
    ) as data:
        if data is None:
            return
        for f in tqdm(load(ds.cldf_dir / 'languages.geojson')['features']):
            if f['geometry']['type'] == 'MultiPolygon':
                mdist, polys = spread(f)
                if not mdist:
                    continue
                if mdist > 14:
                    assert f['properties']['title'] in [
                        'Tuvalu',  # Crosses the antimeridian.
                        'Mangaia-Old Rapa',
                    ]
                else:
                    coastal = all(is_polynesian(p) for p in polys)
                    if not coastal:
                        coastal = all(is_micronesian(p) for p in polys)
                    if not coastal:
                        coastal = all(
                            min(0 if p.intersects(l) else distance(p, l)
                                for l in ne10) < 0.005 for p in polys)  # ~< 500m
                    data.append((
                        f['properties']['cldf:languageReference'],
                        len(polys),
                        mdist,
                        coastal,
                        f['properties']['title']
                    ))
                    if mdist > 2:
                        spread_out.append(f)

                        # Mandar: OK, coastal language in Sulawesi
                        # Tavoyan: OK, coastal language in Myanmar
                        # Vietnamese: big language with short distances between polygons compared to the size of the polygons
                        # Tausug: OK, coastal language in north borneo, philippines

    dump(feature_collection(spread_out), pathlib.Path('spread_out.geojson'))


def _plot(rows, ax):
    ax.scatter(
        [r.npolys for r in rows],
        [r.spread for r in rows],
        c=['b' if r.coastal else 'r' for r in rows])
    for r in rows:
        if r.spread > 3 and not r.coastal:
            annotate(ax, r.language,(r.npolys, r.spread))
