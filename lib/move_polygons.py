import typing
import dataclasses

from shapely.geometry import Point, shape

from .util import Fixer


@dataclasses.dataclass
class Move:
    """
    A move is defined by a language to identify matching features, a point to find matching polygons
    and a translation vector specifying the actual move.
    """
    language: str
    point: Point
    vector: typing.Union[typing.Tuple[float], None]

    @classmethod
    def from_spec(cls, spec: typing.Dict[str, str]):
        lon, lat = float(spec['source_lon']), float(spec['source_lat'])
        move = cls(
            language=spec['LANGUAGE'],
            point=Point(lon, lat),
            vector=(float(spec['target_lon']) - lon, float(spec['target_lat']) - lat)
                if spec['target_lon'] else None,
        )
        # Make sure translations are reasonably close.
        if move.vector and move.language not in {'RAPA', 'EASTER ISLAND'}:
            assert abs(move.vector[0]) < 1.3 and abs(move.vector[1]) < 1.3, (
                'Translation vector too big for {0.language}: {0.vector}'.format(move))
        return move

    def __call__(self, polygon_coordinates):
        """
        "Move" a polygon, by adding the translation vector to each coordinate of each ring.
        """
        if self.vector:
            return [
                [(lon + self.vector[0], lat + self.vector[1]) for lon, lat in ring]
                for ring in polygon_coordinates]
        return polygon_coordinates


class Mover(Fixer):
    """
    Functionality to "move" features according to specifications.
    """
    __item_class__ = Move

    def __call__(self, feature) -> dict:
        """
        Implements the functionality to move polygons by a vector for a feature.
        """
        language = feature['properties']['LANGUAGE']
        if language not in self.fixes:
            return feature

        geom = feature['geometry']
        out_polys = []
        in_polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
        for poly in in_polys:  # We operate on individual polygons, not full MultiPolygons.
            pshape = shape(dict(type='Polygon', coordinates=poly))

            move, mindex = None, -1
            for i, m in enumerate(self.fixes[language]):
                if pshape.contains(m.point):
                    # The starting point of the translation vector falls within the polygon!
                    move, mindex = m, i
                    break  # Assuming non-overlapping polygons we are done with the feature.
            if move and move.vector is None:
                # If no vector is defined, we remove the polygon from the shape.
                pass
            else:
                out_polys.append(move(poly) if move else poly)
            if mindex > -1:  # A matching move was found.
                del self.fixes[language][mindex]  # We keep track of which moves have been made.
        geom['type'] = 'Polygon' if len(out_polys) == 1 else 'MultiPolygon'
        geom['coordinates'] = out_polys[0] if len(out_polys) == 1 else out_polys
        return feature
