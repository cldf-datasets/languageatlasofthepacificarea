import pathlib
import functools
import itertools
import collections

import geopandas
from pycldf import Sources
from clldutils.jsonlib import dump
from clldutils.markup import add_markdown_text
from cldfbench import Dataset as BaseDataset
from shapely.geometry import Point, shape

from cldfgeojson import MEDIA_TYPE, aggregate, feature_collection, merged_geometry, fixed_geometry


def norm(d):
    for k in ['ISLAND_NAM', 'ISLAND_NA_', 'ISL_NAM']:
        if k in d:
            d['ISLAND_NAME'] = d.pop(k)
    if 'CNTRY_NAME' in d:
        d['COUNTRY_NAME'] = d.pop('CNTRY_NAME')
        if d['COUNTRY_NAME'] == 'Tailand':
            d['COUNTRY_NAME'] = 'Thailand'
    if 'SOVEREIGN' in d and 'COUNTRY_NAME' not in d:
        if d['SOVEREIGN'] == 'Australia':
            d['COUNTRY_NAME'] = 'Australia'
    if d.get('LANGUAGE', '').startswith('Uninhabite'):
        del d['LANGUAGE']
    if d.get('LANGUAGE', '').startswith('Unclassified'):
        del d['LANGUAGE']
    for v in d.values():
        assert ';' not in v
    return d


def move(feature, references):
    geom = feature['geometry']
    out_polys = []
    in_polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    for poly in in_polys:
        pshape = shape(dict(type='Polygon', coordinates=poly))
        lon, lat = None, None
        for point, _lon, _lat in references:
            print(point)
            if pshape.contains(point):
                print('got it!')
                lon, lat = _lon, _lat
                break
        if lon is not None:
            out_poly = [[(_lon + lon, _lat + lat) for _lon, _lat in ring] for ring in poly]
        else:
            out_poly = poly
        out_polys.append(out_poly)
    geom['type'] = 'Polygon' if len(out_polys) == 1 else 'MultiPolygon'
    geom['coordinates'] = out_polys[0] if len(out_polys) == 1 else out_polys
    return feature


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "languageatlasofthepacificarea"

    @functools.cached_property
    def languages(self):
        return collections.OrderedDict(
            [((lg['Name'], lg['Countries']), lg) for lg in self.etc_dir.read_csv('languages.csv', dicts=True)])

    @functools.cached_property
    def vectors(self):
        res = {}
        for pid, rows in itertools.groupby(
            sorted(self.etc_dir.read_csv('move.csv', dicts=True), key=lambda r: r['pid']),
            lambda r: r['pid'],
        ):
            res[int(pid)] = []
            for lg in rows:
                lon, lat = float(lg['source_lon']), float(lg['source_lat'])
                res[int(pid)].append((
                    Point(lon if lon > 0 else lon + 360, lat),
                    float(lg['target_lon']) - float(lg['source_lon']),
                    float(lg['target_lat']) - float(lg['source_lat'])))
        return res

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    def cmd_readme(self, args) -> str:
        return add_markdown_text(
            BaseDataset.cmd_readme(self, args),
            self.dir.joinpath('NOTES.md').read_text(encoding='utf8'),
            'Description')

    def cmd_download(self, args):
        self.raw_dir.download_and_unpack(
            'https://ecaidata.org/dataset/209cb079-2270-4016-bc8d-f6c7835779c5/'
            'resource/b5095d0f-7429-445d-a507-916aae5398ba/download/languagemap040429.zip')

    def iter_geojson_features(self):
        features = {}
        properties = []
        lname2index = {}
        for i, feature in enumerate(geopandas.read_file(
                str(self.raw_dir / 'languagemap_040102.shp')).__geo_interface__['features']):
            props = norm({k: v for k, v in feature['properties'].items() if v})
            if 'LANGUAGE' in props:  # Ignore uninhabited areas, unclassified languages etc.
                props.setdefault('COUNTRY_NAME', '')
                lid = (props['LANGUAGE'], props['COUNTRY_NAME'])
                properties.append(props)

                if lid in features:
                    features[lid]['geometry'] = merged_geometry(
                        [features[lid], fixed_geometry(feature)], buffer=0)
                else:
                    lname2index[lid] = i + 1
                    features[lid] = {
                        'id': str(i),
                        'type': 'Feature',
                        'properties': {},
                        'geometry': fixed_geometry(feature)['geometry'],
                    }

        for (lname, cname), props in itertools.groupby(
                sorted(properties, key=lambda f: (f['LANGUAGE'], f['COUNTRY_NAME'])),
                lambda f: (f['LANGUAGE'], f['COUNTRY_NAME'])):
            f = features[(lname, cname)]
            props = list(props)
            for attr in ['COUNTRY_NAME', 'SOVEREIGN', 'ISLAND_NAME']:
                f['properties'][attr] = sorted(set(p[attr] for p in props if attr in p))

            fid = lname2index[(lname, cname)]
            if fid in self.vectors:
                move(f, self.vectors[fid])

            yield fid, lname, cname, f

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)

        args.writer.cldf.add_sources(*Sources.from_file(self.etc_dir / "sources.bib"))

        coded_langs = {k: v for k, v in self.languages.items() if v.get('Glottocode')}
        coded_names = collections.defaultdict(list)
        for k, v in self.languages.items():
            if v.get('Glottocode'):
                coded_names[k[0]].append(v)

        polys = []
        for lid, lname, cname, feature in sorted(self.iter_geojson_features(), key=lambda i: i[0]):
            args.writer.objects['ContributionTable'].append(dict(
                ID=lid,
                Name=lname,
                Country=cname or None,
                Sovereigns=feature['properties']['SOVEREIGN'],
                Islands=feature['properties']['ISLAND_NAME'],
                Source=['ecai', 'wurm_and_hattori']
            ))
            if (not cname) and lname in coded_names and len(coded_names[lname]) == 1:
                # No country specified, but we only have one entry for the name anyway.
                cname = coded_names[lname][0]['Countries']
            if (lname, cname) in coded_langs:
                for gc in coded_langs[(lname, cname)]['Glottocode'].split():
                    polys.append((str(lid), feature, gc))

        lids = None
        for ptype in ['language', 'family']:
            label = 'languages' if ptype == 'language' else 'families'
            p = self.cldf_dir / '{}.geojson'.format(label)
            features, languages = aggregate(polys, args.glottolog.api, level=ptype, buffer=0.005)
            dump(feature_collection(
                features,
                title='Speaker areas for {}'.format(label),
                description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype)),
                p,
                indent=2)
            for glang, pids, family in languages:
                if lids is None or (glang.id not in lids):  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=glang.id,
                        Name=glang.name,
                        Glottocode=glang.id,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Source_Languoid_IDs=pids,
                        Speaker_Area=p.stem,
                        Glottolog_Languoid_Level=ptype,
                        Family=family,
                    ))
            args.writer.objects['MediaTable'].append(dict(
                ID=p.stem,
                Name='Speaker areas for {}'.format(label),
                Description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype),
                Media_Type=MEDIA_TYPE,
                Download_URL=p.name,
            ))
            lids = {gl.id for gl, _, _ in languages}

    def schema(self, cldf):
        t = cldf.add_component(
            'ContributionTable',
            {
                'name': 'Country',
            },
            {
                'name':'Sovereigns',
                'separator': '; ',
            },
            {
                'name':'Islands',
                'separator': '; ',
            },
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'
            },
        )
        t.common_props['dc:description'] = \
            ('We list the individual shapes from the source dataset as contributions in order to '
             'preserve the original metadata.')
        cldf['ContributionTable', 'id'].common_props['dc:description'] = \
            ('We use the 1-based index of the first shape with corresponding '
             'LANGUAGE property in the original shapefile as identifier.')
        cldf.add_component('MediaTable')
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Speaker_Area',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#speakerArea'
            },
            {
                'name': 'Glottolog_Languoid_Level'},
            {
                'name': 'Family',
            },
            {
                'name': 'Source_Languoid_IDs',
                'separator': ' ',
                'dc:description': 'List of identifiers of shapes in the original shapefile that '
                                  'were aggregated to create the shape referenced by Speaker_Area.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'
            },
        )
