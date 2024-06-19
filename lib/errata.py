import typing
import dataclasses

from shapely.geometry import Point, shape

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

    @classmethod
    def from_spec(cls, spec: typing.Dict[str, str]):
        lon, lat = float(spec['lon']), float(spec['lat'])
        return cls(
            language=spec['LANGUAGE'],
            point=Point(lon, lat),
            fix=dict(s.split('=') for s in spec['fix'].split(';'))
        )


class Errata(Fixer):
    __item_class__ = Erratum

    def __call__(self, props, geom):
        language = props['LANGUAGE']
        if language in self.fixes:
            obj, eindex = shape(geom), -1
            for i, erratum in enumerate(self.fixes[language]):
                if obj.contains(erratum.point):
                    props.update(erratum.fix)
                    eindex = i
                    break
            if eindex > -1:
                del self.fixes[language][eindex]
        return props

    @property
    def all_done(self):
        return not any(bool(len(e)) for e in self.fixes.values())
