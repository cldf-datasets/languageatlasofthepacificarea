"""

"""
from cldfbench_languageatlasofthepacificarea import Dataset


def run(args):
    ds = Dataset()

    i = 0
    for lname, feature in ds.iter_geojson_features():
        #print(lname)
        if not ds.languages[lname]['Glottocode']:
            i += 1
    print(i)

    #
    # FIXME: also add Glottolog marker!
    #