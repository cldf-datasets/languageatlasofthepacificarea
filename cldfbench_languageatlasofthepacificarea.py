"""
cldfbench dataset definition for languageatlasofthepacificarea
"""
import shutil
import pathlib
import warnings
import functools
import mimetypes
import collections

import fiona
from pycldf import Sources
from clldutils.jsonlib import dump, load
from clldutils.markup import add_markdown_text
from clldutils.path import TemporaryDirectory
from cldfbench import Dataset as BaseDataset
from shapely.geometry import Point, shape
from cldfgeojson import geotiff
from cldfgeojson import (
    MEDIA_TYPE, aggregate, feature_collection, merged_geometry, fixed_geometry, InvalidRingWarning)

from lib.move_polygons import Mover
from lib.errata import Errata
from lib.repair_geometry import ReinsertHoles
from lib.util import existing_dir
from lib import metadata

DC_RIGHTS = "© ECAI Digital Language Atlas of the Pacific Area"


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "languageatlasofthepacificarea"

    @functools.cached_property
    def languages(self):
        return collections.OrderedDict(
            [((lg['Name'], lg['Countries']), lg)
             for lg in self.etc_dir.read_csv('languages.csv', dicts=True)])

    def cmd_readme(self, args) -> str:
        return add_markdown_text(
            BaseDataset.cmd_readme(self, args),
            self.dir.joinpath('NOTES.md').read_text(encoding='utf8'),
            'Description')

    def iter_geojson_features(self):
        """
        This method implements the procedures described in the paper's "Correcting polygons"
        section.
        """
        errata = Errata(self.etc_dir.read_csv('fixes_metadata.csv', dicts=True))
        geofixes = ReinsertHoles(self.etc_dir.read_json('fixes_geometry.geojson')['features'])
        features = collections.defaultdict(list)
        for i, feature in enumerate(fiona.open(str(self.raw_dir / 'languagemap_040102.shp'))):
            feature = feature.__geo_interface__
            props = metadata.normalize({k: v for k, v in feature['properties'].items() if v})
            if props:  # Ignore uninhabited areas, unclassified languages etc.
                with (warnings.catch_warnings(record=True) as w):
                    warnings.simplefilter("always")
                    geom = fixed_geometry(
                        feature, fix_longitude=True, fix_antimeridian=True)['geometry']
                    if w and w[-1].category == InvalidRingWarning:
                        geom = geofixes(feature, geom)
                assert geom['coordinates'], '{} no coords'.format(props)
                # Sometimes polygons erroneously share the same metadata. This must be fixed before
                # we can merge based on metadata and then lookup language mappings.
                props = errata(props, geom)
                features[tuple(props[col] for col in metadata.COLS)].append((i + 1, geom))

        assert errata.all_done and geofixes.all_done

        mover = Mover(self.etc_dir.read_csv('fixes_location.csv', dicts=True))

        for lid, shapes in sorted(features.items(), key=lambda i: i[1][0][0]):
            fid = shapes[0][0]
            f = {
                'id': str(fid),
                'type': 'Feature',
                'properties': dict(zip(metadata.COLS, lid)),
                'geometry': merged_geometry([s[1] for s in shapes]),
            }
            yield fid, lid, mover(f)

        assert mover.all_done, 'Not all moves made'

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)

        args.writer.cldf.add_sources(*Sources.from_file(self.etc_dir / "sources.bib"))

        # Add scanned Atlas leaves:
        georeferenced = dict(self.iter_leaves(args))

        coded_langs = {
            tuple(v[col] for col in metadata.COLS): v
            for v in self.etc_dir.read_csv('languages.csv', dicts=True) if v.get('Glottocode')}

        polys = []
        ecai_features = collections.OrderedDict()
        for lid, lidt, feature in sorted(self.iter_geojson_features(), key=lambda i: i[0]):
            ecai_features[lid] = feature
            args.writer.objects['ContributionTable'].append(dict(
                ID=lid,
                Name=lidt[0],
                Source=['ecai', 'wurm_and_hattori'],
                Media_IDs=['ecai'],
                Type='shape',
                Rights=DC_RIGHTS,
                Properties={col: val for col, val in zip(metadata.COLS, lidt)
                            if val and col != 'LANGUAGE'},
            ))
            if lidt in coded_langs:
                for gc in coded_langs[lidt]['Glottocode'].split():
                    polys.append((str(lid), feature, gc))

        lids = None
        for ptype in ['language', 'family']:
            label = 'languages' if ptype == 'language' else 'families'
            p = self.cldf_dir / '{}.geojson'.format(label)
            features, languages = aggregate(
                polys, args.glottolog.api, level=ptype, buffer=0.005, opacity=0.5)
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

    def iter_leaves(self, args):
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
            ]:
                p = sdir / name
                if p.exists():
                    mid = '{}_{}'.format(ldir.name, type_)
                    shutil.copy(p, ldir / name)
                    args.writer.objects['MediaTable'].append(dict(
                        ID=mid,
                        Name='{}/{}'.format(ldir.name, p.name),
                        Description=desc.format(ldir.name),
                        Media_Type=mimetype or mimetypes.guess_type(name)[0],
                        Download_URL=str(ldir.joinpath(name).relative_to(self.cldf_dir)),
                    ))
                    mids.append(mid)
            if sdir.joinpath('leaf.geojson').exists():
                feature = load(sdir / 'leaf.geojson')['features'][-1]
                assert 'bbox' not in feature

                yield (sdir.name, shape(feature['geometry']))

                p = ldir / 'mapped_area.geojson'
                dump(feature, p, indent=2)
                args.writer.objects['MediaTable'].append(dict(
                    ID='{}_mapped_area'.format(ldir.name),
                    Name='{}/{}'.format(ldir.name, p.name),
                    Description='Geo-referenced area of the scan.',
                    Media_Type='application/geo+json',
                    Download_URL=str(
                        ldir.joinpath('mapped_area.geojson').relative_to(self.cldf_dir)),
                ))
                mids.append('{}_mapped_area'.format(ldir.name))
            epsg4326tif = sdir / 'original_modified.tif'
            if not epsg4326tif.exists():
                epsg4326tif = sdir / 'epsg4326.tif'
            if epsg4326tif.exists():
                p = ldir / 'epsg4326.tif'
                shutil.copy(epsg4326tif, p)
                args.writer.objects['MediaTable'].append(dict(
                    ID='{}_geotiff'.format(ldir.name),
                    Name='{}/{}'.format(ldir.name, p.name),
                    Description='Geo-referenced scan of {} as GeoTIFF for EPSG:4326 - WGS 84',
                    Media_Type='image/tiff',
                    Download_URL=str(p.relative_to(self.cldf_dir)),
                ))
                mids.append('{}_geotiff'.format(ldir.name))
                with TemporaryDirectory() as tmp:
                    # 2. create temporary web mercator tif
                    webtif = geotiff.webmercator(epsg4326tif, tmp / 'web.tif')
                    # 3. convert web mercator tif to jpg
                    web = geotiff.jpeg(webtif, ldir / 'web.jpg')
                    args.writer.objects['MediaTable'].append(dict(
                        ID='{}_web'.format(ldir.name),
                        Name='{}/{}'.format(ldir.name, web.name),
                        Description='GeoTIFF re-projected to web mercator and translated to JPEG',
                        Media_Type='image/jpeg',
                        Download_URL=str(web.relative_to(self.cldf_dir)),
                    ))
                    mids.append('{}_web'.format(ldir.name))
                    # 4. store the bounds
                    p = ldir / 'bounds.geojson'
                    dump(geotiff.bounds(webtif), p, indent=2)
                    args.writer.objects['MediaTable'].append(dict(
                        ID='{}_bounds'.format(ldir.name),
                        Name='{}/{}'.format(ldir.name, p.name),
                        Description='Bounding box of the scan',
                        Media_Type='application/geo+json',
                        Download_URL=str(p.relative_to(self.cldf_dir)),
                    ))
                    mids.append('{}_bounds'.format(ldir.name))

            args.writer.objects['ContributionTable'].append(dict(
                ID=sdir.name,
                Name=row['Contents'],
                Source=['ecai', 'wurm_and_hattori'],
                Media_IDs=mids,
                Type='leaf',
                Rights=DC_RIGHTS,
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
                'name': 'Rights',
                'propertyUrl': 'http://purl.org/dc/terms/rights',
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
            {
                'name': 'Properties',
                'dc:description': "Shape metadata from ECAI's GIS dataset.",
                'datatype': 'json',
            }
        )
        t.common_props['dc:description'] = \
            ('We list the individual shapes from the source dataset as contributions in order to '
             'preserve the original metadata.')
        cldf['ContributionTable', 'id'].common_props['dc:description'] = \
            ('We use the 1-based index of the first shape with corresponding '
             'LANGUAGE property in the original shapefile as identifier.')
        cldf.add_component(
            'MediaTable',
        )
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
