"""
Validation of the data in this dataset is split into several commands.
"""
import pathlib
import contextlib

import fiona
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


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
