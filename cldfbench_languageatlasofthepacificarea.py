import copy
import pathlib
import functools
import itertools
import collections

import geopandas
from shapely.geometry import shape, Polygon, Point
from shapely import union_all
from clldutils.jsonlib import dump
from clldutils.color import qualitative_colors
from cldfbench import Dataset as BaseDataset

#
# shapely unary_union to merge geometries per glottocode
# https://shapely.readthedocs.io/en/stable/reference/shapely.unary_union.html
#
# add command to check, whether the merged areas for a languoid contain all point coordinates from
# Glottolog for said languoid.
#

def merged_geometry(features):
    # Note: We slightly increase each polygon using `buffer` to make sure they overlap a bit and
    # internal boundaries are thus removed.
    return union_all([shape(f['geometry']).buffer(0.001) for f in features])


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


def multi_polygon(f):
    if f['geometry']['type'] == 'Polygon':
        return copy.copy([f['geometry']['coordinates']])
    assert f['geometry']['type'] == 'MultiPolygon'
    return copy.copy(f['geometry']['coordinates'])


class FeatureCollection(list):
    def __init__(self, path, **properties):
        self.path = path
        self.properties = properties
        list.__init__(self)

    def __enter__(self):
        return self

    def append_feature(self, shape, **properties):
        self.append(dict(type="Feature", properties=properties, geometry=shape.__geo_interface__))

    def __exit__(self, exc_type, exc_val, exc_tb):
        geojson = dict(type="FeatureCollection", features=self, properties=self.properties)
        dump(geojson, self.path, indent=2)

    def as_row(self, **kw):
        res = dict(
            ID=self.path.stem,
            Name=self.properties['title'],
            Description=self.properties['description'],
            Media_Type='application/geo+json',
            Download_URL=self.path.name,
        )
        res.update(kw)
        return res


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "languageatlasofthepacificarea"

    @functools.cached_property
    def languages(self):
        return collections.OrderedDict(
            [((lg['Name'], lg['Countries']), lg) for lg in self.etc_dir.read_csv('languages.csv', dicts=True)])

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    #
    # FIXME: cmd_readme: add notes to readme!
    #

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
                    features[lid]['geometry']['coordinates'].extend(multi_polygon(feature))
                else:
                    lname2index[lid] = i + 1
                    features[lid] = {
                        'id': str(i),
                        'type': 'Feature',
                        'properties': {},
                        'geometry': {'type': 'MultiPolygon', 'coordinates': multi_polygon(feature)}
                    }

        for (lname, cname), props in itertools.groupby(
                sorted(properties, key=lambda f: (f['LANGUAGE'], f['COUNTRY_NAME'])),
                lambda f: (f['LANGUAGE'], f['COUNTRY_NAME'])):
            f = features[(lname, cname)]
            props = list(props)
            for attr in ['COUNTRY_NAME', 'SOVEREIGN', 'ISLAND_NAME']:
                f['properties'][attr] = sorted(set(p[attr] for p in props if attr in p))

            mp = None
            for i, poly in enumerate(f['geometry']['coordinates']):
                rings = []
                for ring in poly:
                    # Some linear rings are self-intersecting. We fix these by taking the 0-distance
                    # buffer around the ring instead.
                    p = Polygon(ring)
                    if not p.is_valid:
                        p = p.buffer(0)
                        assert p.is_valid
                    rings.append(p.__geo_interface__['coordinates'][0])
                p = shape(dict(type='Polygon', coordinates=rings))
                assert p.is_valid
                if mp is None:
                    mp = shape(dict(type='MultiPolygon', coordinates=[rings]))
                else:
                    mp = mp.union(p)
                assert mp.is_valid
            f['geometry'] = mp.__geo_interface__
            yield lname2index[(lname, cname)], lname, cname, f

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)

        #
        # FIXME: add sources!
        #

        polys_by_code = collections.defaultdict(list)
        coded_langs = {k: v for k, v in self.languages.items() if v.get('Glottocode')}
        coded_names = collections.defaultdict(list)
        for k, v in self.languages.items():
            if v.get('Glottocode'):
                coded_names[k[0]].append(v)

        glangs = {lg.id: lg for lg in args.glottolog.api.languoids()}
        lang2fam = {}
        lang = {gc for gc, glang in glangs.items() if glang.level.name == 'language'}

        # Assemble all Glottocodes related to any area.
        for lid, lname, cname, feature in sorted(self.iter_geojson_features(), key=lambda i: i[0]):
            args.writer.objects['ContributionTable'].append(dict(
                ID=lid,
                Name=lname,
                Country=cname or None,
                Sovereigns=feature['properties']['SOVEREIGN'],
                Islands=feature['properties']['ISLAND_NAME'],
            ))
            if (not cname) and lname in coded_names and len(coded_names[lname]) == 1:
                # No country specified, but we only have one entry for the name anyway.
                cname = coded_names[lname][0]['Countries']
            if (lname, cname) in coded_langs:
                for gc in coded_langs[(lname, cname)]['Glottocode'].split():
                    glang = glangs[gc]
                    polys_by_code[glang.id].append((lid, feature))
                    lang2fam[glang.id] = glang.id if not glang.lineage else glang.lineage[0][1]
                    if glang.lineage:
                        lang2fam[glang.id] = glang.lineage[0][1]
                        for _, fgc, _ in glang.lineage:
                            lang2fam[fgc] = glang.lineage[0][1]
                            polys_by_code[fgc].append((lid, feature))
                    else:
                        lang2fam[glang.id] = glang.id

        colors = dict(zip(
            [k for k, v in collections.Counter(lang2fam.values()).most_common()],
            qualitative_colors(len(lang2fam.values()))))

        with FeatureCollection(
            self.cldf_dir / 'languages.geojson',
            title='Speaker areas for languages',
            description='Speaker areas from Wurm and Hattori 1981 aggregated for Glottolog '
                        'language-level languoids, color-coded by family.',
        ) as geojson:
            for gc, polys in polys_by_code.items():
                glang = glangs[gc]
                if gc in lang:
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=gc,
                        Name=glang.name,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Source_Languoid_IDs=[str(p[0]) for p in polys],
                        Speaker_Area=geojson.path.stem,
                        Glottolog_Languoid_Level='language',
                        Family=glangs[lang2fam[gc]].name if lang2fam[gc] != gc else None,
                    ))
                    geojson.append_feature(
                        merged_geometry([p[1] for p in polys]),
                        title=glang.name,
                        fill=colors[lang2fam[gc]],
                        family=glangs[lang2fam[gc]].name if lang2fam[gc] != gc else None,
                        **{'cldf:languageReference': gc, 'fill-opacity': 0.8})
        args.writer.objects['MediaTable'].append(geojson.as_row())

        with FeatureCollection(
            self.cldf_dir / 'families.geojson',
            title='Speaker areas for language families',
            description='Speaker areas from Wurm and Hattori 1981 aggregated for Glottolog '
                        'top-level family languoids.',
        ) as geojson:
            for gc in sorted(set(lang2fam.values())):
                glang = glangs[gc]
                if gc not in lang:  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=gc,
                        Name=glang.name,
                        Source_Languoid_IDs=[str(p[0]) for p in polys],
                        Speaker_Area=geojson.path.stem,
                        Glottolog_Languoid_Level='family',
                    ))
                geojson.append_feature(
                    merged_geometry([p[1] for p in polys_by_code[gc]]),
                    title=glang.name,
                    fill=colors[gc],
                    **{'cldf:languageReference': gc, "fill-opacity": 0.8})
        args.writer.objects['MediaTable'].append(geojson.as_row())

        #
        # FIXME: Write another GeoJSON file with aggregated speaker areas for language-level
        # languoids and one for dialect areas, including parentLanguageGlottocode column!
        #

        return
        try:
            p = Point(glangs[gc].longitude, glangs[gc].latitude)
            t += 1
            geo = merged_geometry(polys)
            if not geo.contains(p):
                if 0.5 < geo.distance(p) < 350:
                    m += 1
                    lang_areas['features'].append(dict(
                        type="Feature",
                        properties={"title": '{} {}'.format(glangs[gc].name, glangs[gc].id)},
                        geometry=geo.__geo_interface__))
                    lang_areas['features'].append(dict(
                        type="Feature",
                        properties={"title": '{} {}'.format(glangs[gc].name, glangs[gc].id)},
                        geometry=p.__geo_interface__))
        except:
            print(glangs[gc].id, glangs[gc].latitude)

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
