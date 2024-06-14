import functools
import dataclasses

from shapely.geometry import shape

from .util import Fixer


@dataclasses.dataclass
class Hole:
    language: str
    geometry: dict

    @classmethod
    def from_spec(cls, spec):
        res = cls(language=spec['properties']['LANGUAGE'], geometry=spec['geometry'])
        assert res.shape.is_valid
        return res

    @functools.cached_property
    def shape(self):
        return shape(self.geometry)


class ReinsertHoles(Fixer):
    __item_class__ = Hole

    def __call__(self, feature, geom):
        hole = self.fixes[feature['properties']['LANGUAGE']].pop()
        assert geom['type'] == 'MultiPolygon'
        new_polys = []
        for poly in geom['coordinates']:
            polyshape = shape(dict(type='Polygon', coordinates=poly))
            assert polyshape.is_valid
            if polyshape.contains(hole.shape):
                assert len(poly) == 1, 'expected polygon without holes!'
                poly = list(poly)
                # Add the first ring of the hole geometry as hole:
                poly.append(hole.geometry['coordinates'][0])
            new_polys.append(poly)
        geom['coordinates'] = new_polys
        assert shape(geom).is_valid
        return geom
