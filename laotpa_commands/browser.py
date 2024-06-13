"""
Build a set of HTML pages to browse Atlas leaves as interactive leaflet maps.
"""
import json
import pathlib
import webbrowser

from pycldf.media import File
from clldutils.misc import data_url
from mako.lookup import TemplateLookup

from cldfbench_languageatlasofthepacificarea import Dataset


def run(args):
    lookup = TemplateLookup(directories=[str(pathlib.Path(__file__).parent)])

    out = pathlib.Path('language_atlas_of_the_pacific_area')
    if not out.exists():
        out.mkdir()

    def render(tmpl, fname, **vars):
        out.joinpath(fname).write_text(lookup.get_template(tmpl).render(**vars), encoding='utf8')

    cldf = Dataset().cldf_reader()

    leaves = {
        l.id: l for l in cldf.objects('ContributionTable') if l.data['Type'] == 'leaf'}
    lgeojson = {
        f['properties']['cldf:languageReference']: f for f in
        File.from_dataset(
            cldf, cldf.get_object('MediaTable', 'languages')).read_json()['features']}
    fgeojson = {
        f['properties']['cldf:languageReference']: f for f in
        File.from_dataset(
            cldf, cldf.get_object('MediaTable', 'families')).read_json()['features']}

    #
    # FIXME: support stocks!
    #

    indexgeojson = {}
    languages = [
        l for l in cldf.objects('LanguageTable')
        if l.data['Glottolog_Languoid_Level'] == 'language']
    contribs = [
        {c.id: (c.cldf.name, c.data['Type']) for c in l.all_related('contributionReference')}
        for l in languages]
    for lang, contrib in zip(languages, contribs):
        lgeojson[lang.id]['properties']['shapes'] = sorted(
            {c[0] for c in contrib.values() if c[1] == 'shape'})

    families = [
        l for l in cldf.objects('LanguageTable')
        if l.data['Glottolog_Languoid_Level'] == 'family' or not l.data['Family']]
    fcontribs = [
        {c.id: (c.cldf.name, c.data['Type']) for c in l.all_related('contributionReference')}
        for l in families]
    for lang, contrib in zip(families, fcontribs):
        fgeojson[lang.id]['properties']['shapes'] = sorted(
            {c[0] for c in contrib.values() if c[1] == 'shape'})

    for lid, leaf in leaves.items():
        img, bounds, mapped = None, None, None
        for f in leaf.all_related('mediaReference'):
            if f.id.endswith('_web'):
                img = File.from_dataset(cldf, f)
            elif f.id.endswith('_bounds'):
                bounds = File.from_dataset(cldf, f)
            elif f.id.endswith('_mapped_area'):
                mapped = File.from_dataset(cldf, f)
        if not (img and bounds):
            continue

        indexgeojson[lid] = mapped.read_json()
        indexgeojson[lid]['properties'].update(title=leaf.cldf.name, url='{}.html'.format(lid))

        bounds = bounds.read_json()['bbox']
        langs, features = [], []
        if 'Stocks' in leaf.cldf.name:
            for lang, contrib in zip(families, fcontribs):
                if lid in contrib:
                    features.append(fgeojson[lang.id])
                    langs.append(lang)
        else:
            for lang, contrib in zip(languages, contribs):
                if lid in contrib:
                    features.append(lgeojson[lang.id])
                    langs.append(lang)
        render(
            'leaf.html.mako',
            '{}.html'.format(lid),
            title=leaf.cldf.name,
            img=data_url(img.read(), 'image/jpeg'),
            geojson=json.dumps(dict(type='FeatureCollection', features=features)),
            languages=sorted(langs, key=lambda l: l.cldf.name),
            lat1=bounds[1],
            lon1=bounds[0],
            lat2=bounds[3],
            lon2=bounds[2],
        )

    render(
        'index.html.mako',
        'index.html',
        leaves=json.dumps(dict(type='FeatureCollection', features=list(indexgeojson.values()))))

    webbrowser.open(str(out / 'index.html'))
