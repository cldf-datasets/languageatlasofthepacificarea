import copy
import typing
import dataclasses

from shapely.geometry import Point, shape, MultiPolygon

from .util import Fixer


@dataclasses.dataclass
class Erratum:
    """
    An erratum is defined by a language to identify matching features, a point to find a matching
    shape and a specification of corrections.
    """
    language: str
    point: Point
    fix: dict
    split: bool = False

    @classmethod
    def from_spec(cls, spec: typing.Dict[str, str]):
        lon, lat = float(spec['lon']), float(spec['lat'])
        return cls(
            language=spec['LANGUAGE'],
            point=Point(lon, lat),
            fix=dict(s.split('=') for s in spec['fix'].split(';')),
            split=bool(spec.get('split', False)),
        )


class Errata(Fixer):
    __item_class__ = Erratum

    def __call__(self, props, geom):
        language = props['LANGUAGE']
        res = [(props, geom)]
        if language in self.fixes:
            obj, eindex = shape(geom), -1
            for i, erratum in enumerate(self.fixes[language]):
                if obj.contains(erratum.point):
                    if erratum.split:
                        assert isinstance(obj, MultiPolygon)
                        res = []
                        for geom in obj.geoms:
                            p = copy.copy(props)
                            if geom.contains(erratum.point):
                                p.update(erratum.fix)
                            res.append((p, geom.__geo_interface__))
                    else:
                        res[0][0].update(erratum.fix)
                    eindex = i
                    break
            if eindex > -1:
                del self.fixes[language][eindex]
        return res

    @property
    def all_done(self):
        return not any(bool(len(e)) for e in self.fixes.values())
