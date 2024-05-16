import shutil
import typing
import pathlib
import functools
import itertools
import mimetypes
import collections
import urllib.request

import geopandas
from pycldf import Sources
from clldutils.jsonlib import dump, load
from clldutils.markup import add_markdown_text
from cldfbench import Dataset as BaseDataset
from shapely.geometry import Point, shape
import pycountry
from lxml.etree import HTMLParser, fromstring

from cldfgeojson import MEDIA_TYPE, aggregate, feature_collection, merged_geometry, fixed_geometry

DC_RIGHTS = "© ECAI Digital Language Atlas of the Pacific Area"
# License for scanned leaves New Guinea (https://ecaidata.org/dataset/language_atlas_of_the_pacific_scanned_atlas_leaves_-_new_guinea):
# Leaves 1-12
# CC-BY
# License for scanned leaves Taiwan (https://ecaidata.org/dataset/pacific-language-atlas-leaves-taiwan):
# Leave 30
# http://creativecommons.org/licenses/by-nc/2.0/

# https://ecaidata.org/dataset/language_atlas_of_the_pacific_scanned_atlas_leaves_-_new_guinea

COLS = ['LANGUAGE', 'COUNTRY_NAME', 'ISLAND_NAME', 'SOVEREIGN']


def existing_dir(d):
    if not d.exists():
        d.mkdir()
    assert d.is_dir()
    return d


def norm_metadata(d) -> typing.Union[typing.Dict[str, str], None]:
    """
    Normalize field names and field content for country and island names.

    Return `None` if the record does not contain metadata about a language polygon.
    """
    for k in ['ISLAND_NAM', 'ISLAND_NA_', 'ISL_NAM']:
        if k in d:
            v = d.pop(k)
            d['ISLAND_NAME'] = {
                'apua New Guinea': 'Papua New Guinea',
                'Papua New Gu': 'Papua New Guinea',
            }.get(v, v)
    if 'CNTRY_NAME' in d:
        d['COUNTRY_NAME'] = d.pop('CNTRY_NAME')
        ncountries = []
        for name in d['COUNTRY_NAME'].split('/'):
            name = {
                'Tailand': 'Thailand',
                'Burma': 'Myanmar',
                'Christmas I.': 'Christmas Island',
                'East Tiimor': 'Timor-Leste',
                'East Timor': 'Timor-Leste',
                'Kampuchea': 'Cambodia',
                'Laos': "Lao People's Democratic Republic",
            }.get(name, name)
            assert pycountry.countries.lookup(name)
            ncountries.append(name)
        d['COUNTRY_NAME'] = '/'.join(ncountries)
    if 'SOVEREIGN' in d and 'COUNTRY_NAME' not in d:
        if d['SOVEREIGN'] == 'Australia':
            d['COUNTRY_NAME'] = 'Australia'
    if d.get('LANGUAGE', '').startswith('Uninhabite'):
        return None
    if d.get('LANGUAGE', '').startswith('Unclassified'):
        return None
    for v in d.values():
        assert ';' not in v
    for col in COLS:
        d.setdefault(col, '')
    assert set(COLS).issubset(set(d.keys()))
    return d


MOVED = 0


def move(feature, references):
    geom = feature['geometry']
    out_polys = []
    in_polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    for poly in in_polys:
        pshape = shape(dict(type='Polygon', coordinates=poly))
        lon, lat, delete = None, None, False
        for point, _lon, _lat in references:
            if pshape.contains(point):
                global MOVED
                MOVED += 1
                #print(MOVED)
                lon, lat = _lon, _lat
                if _lon is None and _lat is None:
                    delete = True
                break
        if lon is not None:
            out_poly = [[(_lon + lon, _lat + lat) for _lon, _lat in ring] for ring in poly]
        else:
            out_poly = poly
        if not delete:
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
                    float(lg['target_lon']) - lon if lg['target_lon'] else None,
                    float(lg['target_lat']) - lat if lg['target_lat'] else None))
        return res

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    def cmd_readme(self, args) -> str:
        return add_markdown_text(
            BaseDataset.cmd_readme(self, args),
            self.dir.joinpath('NOTES.md').read_text(encoding='utf8'),
            'Description')

    def cmd_download(self, args):
        import requests
        for item in load(self.raw_dir / 'atlas_leaves.json'):
            html = fromstring(urllib.request.urlopen(item['url']).read(), HTMLParser())
            for link in html.xpath('//a'):
                if 'href' in link.attrib:
                    href = link.attrib['href']
                    if href.split('/')[-1].startswith('L0'):
                        o = self.raw_dir / 'atlas' / href.split('/')[-1]
                        href = href.replace('http:', 'https:').replace('edu/a', 'edu//a')
                        if href.endswith('jgw'):
                            continue
                        if not o.exists():
                            try:
                                print(href)
                                o.write_bytes(requests.get(href, verify=False).content)
                            except:
                                raise
                                pass
        return

        res = []
        u = "https://ecai.org//austronesiaweb/PacificAtlasContents-Alpha.htm"
        html = fromstring(urllib.request.urlopen(u).read(), HTMLParser())
        for tr in html.xpath('//table[@width="589"]/tr'):
            tds = list(tr.xpath('td'))
            if len(tds) == 3 and tds[-1].xpath('a'):
                res.append(dict(
                    name=tds[0].text,
                    id=tds[1].text,
                    url='https://ecai.org/austronesiaweb/{}'.format(tds[-1].xpath('a')[0].attrib['href'])
                ))
        dump(res, self.raw_dir / 'atlas_leaves.json', indent=2)
        return

        dl = self.raw_dir / 'atlas' / 'new_guinea'
        dl.mkdir()
        for item in self.raw_dir.joinpath('atlas').read_json('new_guinea.json')['@graph']:
            if item['@type'] == 'schema:DataDownload':
                urllib.request.urlretrieve(item['schema:url'], dl / item['schema:url'].split('/')[-1])
        return
        url = "https://ecaidata.org/dataset/language_atlas_of_the_pacific_scanned_atlas_leaves_-_new_guinea"
        html = fromstring(urllib.request.urlopen(url).read(), HTMLParser())
        json = html.xpath('//script[@type="application/ld+json"]')[0]
        self.raw_dir.joinpath('atlas', 'new_guinea.json').write_text(json.text, encoding='utf8')
        return

        import os
        from csvw.dsv import UnicodeWriter

        cols = ['LANGUAGE', 'COUNTRY_NAME', 'ISLAND_NAME', 'SOVEREIGN']
        with UnicodeWriter('shapes_norm.csv') as w:
            w.writerow(cols)
            for i, feature in enumerate(geopandas.read_file(
                    str(self.raw_dir / 'languagemap_040102.shp')).__geo_interface__['features']):
                props = norm_metadata({k: v for k, v in feature['properties'].items() if v})
                if props:
                    w.writerow([props.get(col, '') for col in cols])
        return

        u = "https://ecai.berkeley.edu//austronesiaweb/maps/pacificatlas/Pacific_leaves/{}.jpg"
        for row in self.raw_dir.read_csv('atlas_leaves.csv', dicts=True):
            os.system('curl -k {} -o {}'.format(u.format(row['File']), str(self.raw_dir / '{}.jpg'.format(row['File']))))
        return
        #from csvw.dsv import UnicodeWriter
        #md = []
        #for i, feature in enumerate(geopandas.read_file(
        #        str(self.raw_dir / 'languagemap_040102.shp')).__geo_interface__['features']):
        #    md.append(feature['properties'])
        #cols = set()
        #for p in md:
        #    cols = cols.union(p.keys())
        #cols = sorted(cols)

        #print(len(md))
        #with UnicodeWriter('shapes.csv') as w:
        #    w.writerow(cols)
        #    for p in md:
        #        w.writerow([p.get(c, '') for c in cols])

        #return
        self.raw_dir.download_and_unpack(
            'https://ecaidata.org/dataset/209cb079-2270-4016-bc8d-f6c7835779c5/'
            'resource/b5095d0f-7429-445d-a507-916aae5398ba/download/languagemap040429.zip')

    def iter_geojson_features(self):
        errata = collections.defaultdict(list)
        for row in self.etc_dir.read_csv('errata.csv', dicts=True):
            errata[row['LANGUAGE']].append((
                Point(float(row['lon']), float(row['lat'])),
                dict(s.split('=') for s in row['fix'].split(';'))))
        features = {}
        properties = []
        lname2index = {}
        _all = []
        for i, feature in enumerate(geopandas.read_file(
                str(self.raw_dir / 'languagemap_040102.shp')).__geo_interface__['features']):
            _all.append(feature)
            props = norm_metadata({k: v for k, v in feature['properties'].items() if v})
            if props:  # Ignore uninhabited areas, unclassified languages etc.
                geom = fixed_geometry(feature)
                # Sometimes polygons erroneously share the same metadata. This must be fixed before
                # we can merge based on metadata and then lookup language mappings.
                if props['LANGUAGE'] in errata:
                    obj = shape(geom['geometry'])
                    for point, fix in errata[props['LANGUAGE']]:
                        if obj.contains(point):
                            props.update(fix)
                            break

                lid = tuple(props[col] for col in COLS)
                properties.append((lid, props))

                if lid in features:
                    features[lid]['geometry'] = merged_geometry([features[lid], geom], buffer=0)
                else:
                    lname2index[lid] = i + 1
                    features[lid] = {
                        'id': str(i),
                        'type': 'Feature',
                        'properties': {},
                        'geometry': geom['geometry'],
                    }
        dump(feature_collection(_all), self.raw_dir / 'all.geojson')

        for lid, props in itertools.groupby(sorted(properties, key=lambda f: f[0]), lambda f: f[0]):
            f = features[lid]
            props = list(props)
            for attr in ['COUNTRY_NAME', 'SOVEREIGN', 'ISLAND_NAME']:
                f['properties'][attr] = sorted(set(p[attr] for p in props if attr in p))

            fid = lname2index[lid]
            if fid in self.vectors:
                move(f, self.vectors[fid])

            yield fid, lid, f

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)

        args.writer.cldf.add_sources(*Sources.from_file(self.etc_dir / "sources.bib"))

        #
        # Add scanned Atlas leaves:
        #
        georeferenced = {}
        atlas_dir = existing_dir(self.cldf_dir / 'atlas')
        for row in self.raw_dir.read_csv('atlas_leaves.csv', dicts=True):
            sdir = self.raw_dir / 'atlas' / row['File']
            if not sdir.exists():
                assert 'Japan' in row['Contents']
                continue
            ldir = existing_dir(atlas_dir / row['File'])
            mids = []
            for type_, name, desc, mimetype in [
                ('s', 'original.jpg', 'Scanned Atlas leaf {} from ECAI', None),
                ('l', 'legend.jpg', 'Scanned Atlas leaf {} reverse side from ECAI', None),
                ('b', 'back.jpg', 'Scanned Atlas leaf {} legend from ECAI', None),
                ('points',
                 'original.jpg.points',
                 'Ground control points used to geo-reference the scan of {} with QGIS',
                 'text/plain'),
                ('geotiff',
                 'epsg4326.tif',
                 'Geo-referenced scan of {} as GeoTIFF for EPSG:4326 - WGS 84',
                 None),
                ('web',
                 'web.jpg',
                 'GeoTIFF re-projected to web mercator and translated to JPEG of {}',
                 None),
                ('geojson',
                 'leaf.geojson',
                 'Bounding box and geo-referenced area of the scan {}',
                 'application/geo+json'),
            ]:
                p = sdir / name
                if p.exists():
                    mid = '{}_{}'.format(ldir.name, type_)
                    if type_ == 'geojson':
                        georeferenced[sdir.name] = shape(next(itertools.dropwhile(
                            lambda f: f['properties']['id'] != 'georeferenced',
                            load(p)['features']))['geometry'])
                    shutil.copy(p, ldir / name)
                    args.writer.objects['MediaTable'].append(dict(
                        ID=mid,
                        Name='{}/{}'.format(ldir.name, p.name),
                        Description=desc.format(ldir.name),
                        Media_Type=mimetype or mimetypes.guess_type(name)[0],
                        Download_URL=str(ldir.joinpath(name).relative_to(self.cldf_dir)),
                    ))
                    mids.append(mid)

            args.writer.objects['ContributionTable'].append(dict(
                ID=sdir.name,
                Name=row['Contents'],
                Source=['ecai', 'wurm_and_hattori'],
                Media_IDs=mids,
                Type='leaf',
            ))

        coded_langs = {
            tuple(v[col] for col in COLS): v
            for v in self.etc_dir.read_csv('languages_with_comment.csv', dicts=True)
            if v.get('Glottocode')}
        coded_names = collections.defaultdict(list)
        for k, v in self.languages.items():
            if v.get('Glottocode'):
                coded_names[k[0]].append(v)

        polys = []
        ecai_features = collections.OrderedDict()
        for lid, lidt, feature in sorted(self.iter_geojson_features(), key=lambda i: i[0]):
            ecai_features[lid] = feature
            lname, cname, iname, sov = lidt
            name, det = lname, ', '.join(s for s in [cname, iname, sov] if s)
            if det:
                lname = '{} ({})'.format(lname, det)
            args.writer.objects['ContributionTable'].append(dict(
                ID=lid,
                Name=name,
                Source=['ecai', 'wurm_and_hattori'],
                Media_IDs=['ecai'],
                Type='shape',
            ))
            if lidt in coded_langs:
                for gc in coded_langs[lidt]['Glottocode'].split():
                    polys.append((str(lid), feature, gc))

        lids = None
        for ptype in ['language', 'family']:
            label = 'languages' if ptype == 'language' else 'families'
            p = self.cldf_dir / '{}.geojson'.format(label)
            features, languages = aggregate(polys, args.glottolog.api, level=ptype, buffer=0.005, opacity=0.5)
            dump(feature_collection(
                features,
                title='Speaker areas for {}'.format(label),
                description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype)),
                p,
                indent=2)
            for (glang, pids, family), f in zip(languages, features):
                area = shape(f['geometry'])
                for cid, ref in georeferenced.items():
                    if ref.intersects(area):
                        pids.append(cid)
                if lids is None or (glang.id not in lids):  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=glang.id,
                        Name=glang.name,
                        Glottocode=glang.id,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Contribution_IDs=pids,
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

        for lid, feature in ecai_features.items():
            feature['id'] = str(lid)

        dump(
            feature_collection(
                list(ecai_features.values()),
                **{'dc:rights': DC_RIGHTS,
                   'dc:title':
                       'GIS spatial dataset of the ECAI Digital Language Atlas of the Pacific Area'}
            ),
            self.cldf_dir / 'ecai.geojson',
            indent=2)
        args.writer.objects['MediaTable'].append(dict(
            ID='ecai',
            Name='Speaker areas for {}'.format(label),
            Description=
                'Shapes from ECAI with normalized metadata and aggregated by matching metadata',
            Media_Type=MEDIA_TYPE,
            Download_URL='ecai.geojson',
        ))

    def schema(self, cldf):
        t = cldf.add_component(
            'ContributionTable',
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'
            },
            {
                'name': 'Media_IDs',
                'separator': ' ',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference'
            },
            {
                'name': 'Type',
                'datatype': {'base': 'string', 'format': 'leaf|shape'}
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
                'name': 'Contribution_IDs',
                'separator': ' ',
                'dc:description':
                    'List of identifiers of shapes in the original shapefile that were aggregated '
                    'to create the shape referenced by Speaker_Area and of Atlas leaves mapping a '
                    "georeferenced area intersecting with this languoid's area.",
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'
            },
        )
