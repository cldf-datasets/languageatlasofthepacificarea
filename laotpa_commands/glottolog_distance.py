"""
A measure how accurately the shapes of the dataset match the geographic information from Glottolog.

$ csvsql etc/glottolog_distance.csv --query "select glottocode, language, distance from glottolog_distance where distance > 2 order by distance"
"""
import dataclasses

from shapely.geometry import shape
from clldutils.clilib import PathType
from clldutils.path import TemporaryDirectory
from clldutils.jsonlib import load
from pycldf.ext.discovery import get_dataset

from cldfbench_languageatlasofthepacificarea import Dataset
from .validation import plot, validate


outliers = {
    'lisu1250': 'According to Glottolog, Lisu is spoken in four countries, with the Glottolog '
                'coordinate on the border between China and Myanmar, and the Atlas listing areas '
                'in Thailand.',  # Lisu,7.038565556308784
    'iran1262': 'Iranum is spoken in the Philippines and Malaysia with Glottolog only listing the '
                'Malaysian areas, the Atlas listing all areas.',  # Iranun,6.670919436617212
    'kach1280': 'Southern Jinghpaw is spoken in China and Myanmar with only a small patch of the '
                'area falling within the area mapped in the Atlas.',  # Southern Jinghpaw,4.8788
    'awac1238': 'The Glottolog language is listed as being spoken in China, while the Atlas lists '
                'small patches in Myanmar.',  # Lavia-Awalai-Damangnuo Awa,4.1978514125759805
    'nugu1241': 'The Glottolog coordinate has been reported as too far East and will be '
                'updated.',  # Nugunu (Australia),4.0668630015069915
    'fiji1243': 'Relevant areas in the Atlas are mapped to the subgroup Eastern Fijian, because '
                'they also include areas where other languages of this subgroup are spoken, '
                'leaving just the smaller islands mapped to Fijian.',  # Fijian,3.179890773699526
    'mala1479': 'Glottolog places this language in Kuala Lumpur, but the language is spoken also '
                'in Indonesia, Singapore and Thailand, with the Atlas listing areas on Sumatra '
                'and Borneo.',  # Central Malay,3.176484848400537
    'bouy1240': 'Spoken in China and Vietnam with the Glottolog coordinate well inside China and '
                'the areas listed in the Atlas within Vietnam.',  # Bouyei,3.0234061342447256
    'blan1242': 'Polygon is in a very southern location in Thailand in contrast to the northern '
                'location of Glottolog. The location in Thailand represents a recent refugee '
                'population and is in this sense not wrong but the Glottolog location is '
                'historically and demographically more accurate.',  # Blang,2.870919388912541
    'mart1256': 'The Atlas only lists one dialect of the Glottolog language at roughly the '
                'location given in Glottolog for this dialect. But the Glottolog coordinate for '
                'the language represents the centre-point for the language.',  # Martu Wangka,2.4
    'monn1252': 'The Atlas just lists a couple of very small pockets labeled as MON in Thailand, '
                'while Mon is also spoken in Myanmar.',  # Mon,2.363278360297026
    'main1275': 'Some areas in the Atlas mapped to this Glottolog language were originally '
                'assigned to a supposed language which was subsequently merged into Mainstream '
                'Kenyah in ISO 639-3 as well as in Glottolog.',  # Usun Apau Kenyah,2.02161
}


@dataclasses.dataclass
class GlottologDistance:
    glottocode: str
    npolys: int
    proper_containment: bool
    distance: float
    language: str

    @classmethod
    def from_row(cls, row):
        return cls(row[0], int(row[1]), row[2] == 'True', float(row[3]), row[4])


def register(parser):
    parser.add_argument('--plot-only', action='store_true', default=False)
    parser.add_argument('glottolog_cldf', type=PathType(type='dir'))


def run(args):
    ds = Dataset()

    with TemporaryDirectory() as tmp:
        gl = get_dataset(args.glottolog_cldf, tmp)
        gl_coords = {
            l.id: l.as_geojson_feature for l in gl.objects('LanguageTable') if l.cldf.longitude}

    with (validate(args, ds, __file__, _plot, item_class=GlottologDistance) as data):
        if data is None:
            return
        for f in load(ds.cldf_dir / 'languages.geojson')['features']:
            gc = f['properties']['cldf:languageReference']
            if gc in gl_coords:
                shp = shape(f['geometry'])
                npolys = len(f['geometry']['coordinates']) \
                    if f['geometry']['type'] == 'MultiPolygon' else 1

                gl_coord = shape(gl_coords[gc]['geometry'])
                if shp.contains(gl_coord):
                    data.append((gc, npolys, True, 0, f['properties']['title']))
                elif shp.convex_hull.contains(gl_coord):
                    data.append((gc, npolys, False, 0, f['properties']['title']))
                else:
                    dist = shp.distance(gl_coord)
                    if dist > 180:
                        dist = abs(dist - 360)
                    if dist > 2:
                        assert gc in outliers
                    data.append((gc, npolys, False, dist, f['properties']['title']))


def _plot(rows):
    with plot(
        'Distance from Glottolog coordinate',
        'Number of polygons',
        'Distance',
    ) as ax:
        ax.scatter(
            [r.npolys for r in rows if r.distance > 0],
            [r.distance for r in rows if r.distance > 0],
        )
        for r in rows:
            if r.distance > 2:
                ax.annotate(r.language, (r.npolys, r.distance))
