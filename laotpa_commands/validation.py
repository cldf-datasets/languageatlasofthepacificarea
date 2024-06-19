"""
Validation of the data in this dataset is split into several commands.
"""
import pathlib
import contextlib
import dataclasses

import fiona
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from csvw.dsv import reader, UnicodeWriter


def get_lon_lat(arg):
    if isinstance(arg, tuple):
        assert len(arg) == 2
        return arg
    if isinstance(arg, Polygon):
        centroid = arg.centroid
        return centroid.x, centroid.y


def is_polynesian(arg):
    lon, lat = get_lon_lat(arg)
    return lon < 0 or lon > 163


def is_micronesian(arg):
    lon, lat = get_lon_lat(arg)
    return lon > 130 and lat > 1


@contextlib.contextmanager
def validate(args, ds, f, plotter, item_class):
    data = Data(ds, f, item_class)
    try:
        yield None if args.plot_only and data.path.exists() else data
    finally:
        if data.rows:
            data.write()
        assert data.path.exists()
        plotter(data.read())


class Data:
    def __init__(self, ds, f, item_class):
        self.cls = item_class
        self.path = ds.etc_dir / '{}.csv'.format(pathlib.Path(f).stem)
        self.rows = []

    def append(self, row):
        self.rows.append(self.cls(*row) if not isinstance(row, self.cls) else row)

    def read(self):
        return [self.cls.from_row(tuple(r.values())) for r in reader(self.path, dicts=True)]

    def write(self):
        with UnicodeWriter(self.path) as w:
            w.writerow([f.name for f in dataclasses.fields(self.cls)])
            for row in self.rows:
                w.writerow(dataclasses.astuple(row) if isinstance(row, self.cls) else row)


@contextlib.contextmanager
def plot(title, xlabel, ylabel, legend_loc='upper left', legend_items=None):
    fig, ax = plt.subplots()
    try:
        yield ax
    finally:
        ax.set_xlabel(xlabel, fontsize=15)
        ax.set_ylabel(ylabel, fontsize=15)
        ax.set_title(title)
        if legend_items:
            ax.legend(
                handles=[mpatches.Patch(color=c, label=l) for c, l in legend_items.items()],
                loc=legend_loc)
        ax.grid(True)
        fig.tight_layout()
        plt.show()


def iter_ne_shapes(shapefile):
    yield from fiona.open(
        str(pathlib.Path(__file__).parent / 'naturalearth' / '{}.shp'.format(shapefile)))


def run(args):
    pass
