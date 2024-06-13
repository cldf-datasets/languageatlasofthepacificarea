"""
Compute statistics about curated polygons not intersecting with land masses. This metric
provides information about how accurately the shapes in the dataset align with geography.

Land masses are defined by features in the NaturalEarth large scale shapefiles for land and reefs.
"""
import pathlib
import collections
import dataclasses

import fiona
from shapely import distance
from shapely.geometry import shape, Point
from clldutils.jsonlib import load
from csvw.dsv import reader, UnicodeWriter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import tqdm

from cldfbench_languageatlasofthepacificarea import Dataset


@dataclasses.dataclass
class NonIntersectingPolygon:
    language: str
    centroid_lon: float
    centroid_lat: float
    area: float
    distance: float

    @property
    def is_polynesian(self):
        return self.centroid_lon < 0 or self.centroid_lon > 163

    @classmethod
    def from_row(cls, row):
        return cls(row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4]))

    @classmethod
    def from_polygon(cls, polygon, language, distance):
        cent = polygon.centroid
        return cls(language, cent.x, cent.y, polygon.area, distance)


def register(parser):
    parser.add_argument('--plot-only', action='store_true', default=False)


def iter_polygons(f):
    if 'Polygon' in f['geometry']['type']:
        coords = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon'\
            else [f['geometry']['coordinates']]
        for poly in coords:
            yield shape(dict(type='Polygon', coordinates=poly))
    else:  # The reefs shapefile also contains LineStrings.
        yield shape(f['geometry'])


def run(args):
    ds = Dataset()
    res = ds.etc_dir / 'non-intersecting-polygons.csv'
    if args.plot_only and res.exists():
        plot([NonIntersectingPolygon.from_row(r) for r in reader(res)])
        return

    # We store the move target points, because polygons containing one of these are considered
    # "intersecting".
    move_targets = []
    for row in ds.etc_dir.read_csv('move.csv', dicts=True):
        if row['target_lat']:
            move_targets.append(Point(float(row['target_lon']), float(row['target_lat'])))

    # Load NaturalEarth features:
    ne10 = []
    for shapefile in ['ne_10m_land', 'ne_10m_reefs']:
        for shp in fiona.open(
                str(pathlib.Path(__file__).parent / 'naturalearth' / '{}.shp'.format(shapefile))):
            ne10.extend(list(iter_polygons(shp)))

    non_intersecting = []
    polys_per_language, nip_per_language = collections.Counter(), collections.Counter()
    for f in tqdm.tqdm(load(ds.cldf_dir / 'ecai.geojson')['features']):
        # Our corrected, aggregated features.
        for poly in iter_polygons(f):
            polys_per_language.update([f['properties']['LANGUAGE']])
            # Don't alert if poly contains any target point of a move!
            if any(poly.contains(mt) for mt in move_targets):
                continue
            for ne in ne10:
                if ne.intersects(poly):
                    break
            else:
                nip_per_language.update([f['properties']['LANGUAGE']])
                non_intersecting.append(NonIntersectingPolygon.from_polygon(
                    poly,
                    f['properties']['LANGUAGE'],
                    min(distance(poly, p2) for p2 in ne10)
                ))


    assert all(
        polys_per_language[nip.language] > nip_per_language[nip.language]
        for nip in non_intersecting)
    with UnicodeWriter(res) as w:
        for nip in non_intersecting:
            w.writerow(dataclasses.astuple(nip))

    plot(non_intersecting)


def plot(nips):
    fig, ax = plt.subplots()
    ax.scatter(
        [nip.area for nip in nips],
        [nip.distance for nip in nips],
        c=['b' if nip.is_polynesian else 'r' for nip in nips])
    ax.set_xlabel(r'Area', fontsize=15)
    ax.set_ylabel(r'Distance', fontsize=15)
    ax.set_title('Polygons not intersecting with land')
    red_patch = mpatches.Patch(color='r', label=r'Other ($0\,<\,lon\,<\,163$)')
    blue_patch = mpatches.Patch(color='b', label=r'"Polynesian" ($lon\,>\,163$ or $lon < 0$)')
    ax.legend(handles=[blue_patch, red_patch], loc='upper left')
    ax.grid(True)
    fig.tight_layout()
    plt.show()
