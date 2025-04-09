<a name="ds-genericmetadatajson"> </a>

# Generic CLDF dataset derived from the ECAI digitization of Wurm and Hattori's "Language Atlas of the Pacific Area" from 1981 and 1983

**CLDF Metadata**: [Generic-metadata.json](./Generic-metadata.json)

**Sources**: [sources.bib](./sources.bib)

Wurm & Hattori’s Language Atlas of the Pacific Area describes the geographic speaker areas of the languages and language varieties spoken in the Pacific. Thanks to the efforts of the Electronic Cultural Atlas Initiative, this monumental piece of work has been available in digital form for over 15 years. But lacking proper identification of language varieties this digitized data was largely unusable for today’s research methods. This CLDF dataset turns ECAI’s digitized artefacts of the Language Atlas into an open, reusable geo-referenced dataset of speaker area polygons for a quarter of the world’s languages.

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Wurm, S. & Hattori, S. Language Atlas of the Pacific Area: New Guinea area, Oceania, Australia, vol. 66 of Pacific Linguistics: Series C (Canberra: Research School of Pacific and Asian Studies, Australian National University, Canberra, 1981).
Wurm, S. & Hattori, S. Language Atlas of the Pacific Area: Japan area, Taiwan-Formosa, Philippines, Mainland and insular South-East Asia, vol. 67 of Pacific Linguistics: Series C (Canberra: Research School of Pacific and Asian Studies, Australian National University, Canberra, 1983).
Registered scans and GIS dataset released by the Electronic Cultural Atlas Initiative (ECAI).
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Generic](http://cldf.clld.org/v1.0/terms.rdf#Generic)
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by-nc/4.0/
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/cldf-datasets/languageatlasofthepacificarea
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/cldf-datasets/languageatlasofthepacificarea/tree/59e5bb2">cldf-datasets/languageatlasofthepacificarea v2.0-10-g59e5bb2</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v5.1">Glottolog v5.1</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.12.3</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | languageatlasofthepacificarea
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-contributionscsv"></a>Table [contributions.csv](./contributions.csv)

We list the individual shapes from the source dataset as contributions in order to preserve the original metadata.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ContributionTable](http://cldf.clld.org/v1.0/terms.rdf#ContributionTable)
[dc:extent](http://purl.org/dc/terms/extent) | 3131


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | We use the 1-based index of the first shape with matching metadata in the original shapefile as identifier.<br>Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Contributor](http://cldf.clld.org/v1.0/terms.rdf#contributor) | `string` | 
[Citation](http://cldf.clld.org/v1.0/terms.rdf#citation) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Rights](http://purl.org/dc/terms/rights) | `string` | 
[Media_IDs](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | list of `string` (separated by ` `) | Contributions can be related to various kinds of media. ECAI shape contributions are linked to GeoJSON files that store the geo data; Atlas leaf contributions are linked to the corresponding scans and geo-data derived from these.<br>References [media.csv::ID](#table-mediacsv)
`Type` | `string`<br>Valid choices:<br> `leaf` `shape` | There are two types of contributions: Individual shapes from ECAI's geo-registered dataset and individual leaves of the Atlas.
`Properties` | `json` | Shape metadata from ECAI's GIS dataset and Glottocodes of the Glottolog languoids to which the shape was matched.

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 357


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string`<br>Regex: `[^/]+/.+` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
[Path_In_Zip](http://cldf.clld.org/v1.0/terms.rdf#pathInZip) | `string` | 

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1873


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal`<br>&ge; -90<br>&le; 90 | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal`<br>&ge; -180<br>&le; 180 | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string`<br>Regex: `[a-z0-9]{4}[1-9][0-9]{3}` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string`<br>Regex: `[a-z]{3}` | 
[Speaker_Area](http://cldf.clld.org/v1.0/terms.rdf#speakerArea) | `string` | References [media.csv::ID](#table-mediacsv)
`Glottolog_Languoid_Level` | `string`<br>Valid choices:<br> `language` `family` | 
`Family` | `string` | 
[Contribution_IDs](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | list of `string` (separated by ` `) | List of identifiers of shapes in the original shapefile that were aggregated to create the shape referenced by Speaker_Area and of Atlas leaves mapping a georeferenced area intersecting with this languoid's area.<br>References [contributions.csv::ID](#table-contributionscsv)

