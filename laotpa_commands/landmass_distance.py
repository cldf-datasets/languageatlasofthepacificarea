"""
Compute statistics about curated polygons not intersecting with land masses. This metric
provides information about how accurately the shapes in the dataset align with geography.

Land masses are defined by features in the NaturalEarth large scale shapefiles for land and reefs.
"""
import dataclasses

from shapely import distance
from shapely.geometry import shape, Point
from clldutils.jsonlib import load
import tqdm

from cldfbench_languageatlasofthepacificarea import Dataset
from .validation import plot, iter_ne_shapes, validate, is_polynesian, is_micronesian


@dataclasses.dataclass
class NonIntersectingPolygon:
    language: str
    centroid_lon: float
    centroid_lat: float
    area: float
    distance: float

    @property
    def is_polynesian(self):
        return is_polynesian((self.centroid_lon, self.centroid_lat))

    @property
    def is_micronesian(self):
        return is_micronesian((self.centroid_lon, self.centroid_lat))

    @classmethod
    def from_row(cls, row):
        return cls(row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4]))


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

    # We store the move target points, because polygons containing one of these are considered
    # "intersecting".
    move_targets = []
    for row in ds.etc_dir.read_csv('fixes_location.csv', dicts=True):
        if row['target_lat']:
            move_targets.append(Point(float(row['target_lon']), float(row['target_lat'])))

    # Load NaturalEarth features:
    ne10 = []
    for shapefile in ['ne_10m_land', 'ne_10m_reefs']:  # FIXME: add png_admbnda_adm1_20180419
        for shp in iter_ne_shapes(shapefile):
            ne10.extend(list(iter_polygons(shp)))

    with validate(args, ds, __file__, _plot, item_class=NonIntersectingPolygon) as non_intersecting:
        if non_intersecting is None:  # we only plot pre-computed results.
            return

        # Loop over corrected, aggregated ECAI shapefile features.
        for f in tqdm.tqdm(load(ds.cldf_dir / 'ecai.geojson')['features']):
            for poly in iter_polygons(f):
                if any(poly.contains(mt) for mt in move_targets):
                    # Don't check if the polygon contains any target point of a move!
                    continue

                for ne in ne10:
                    if ne.intersects(poly):
                        break
                else:
                    if f['properties']['LANGUAGE'] in [  # List of languages that have been cleared:
                        'Bicoli',
                        'MAISIN(Uiaku)',
                        'Logea',  # verified with PNG admin boundaries shapefile
                    ]:
                        continue
                    cent = poly.centroid
                    non_intersecting.append((
                        f['properties']['LANGUAGE'],
                        cent.x,
                        cent.y,
                        poly.area,
                        min(distance(poly, p2) for p2 in ne10)))


def _plot(nips):
    with plot(
        'Polygons not intersecting with land',
        'Area',
        'Distance',
        legend_items={
            'b': r'"Polynesian" ($lon\,>\,163$ or $lon < 0$)',
            'c': r'"Micronesian" ($lon\,>\,130$ and $lat > 1$)',
            'r': r'Other',
        },
    ) as ax:
        ax.scatter(
            [nip.area for nip in nips],
            [nip.distance for nip in nips],
            c=['b' if nip.is_polynesian else ('c' if nip.is_micronesian else 'r') for nip in nips])
