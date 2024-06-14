import typing

import pycountry

# The normalized field names of the shape metadata:
COLS = ['LANGUAGE', 'COUNTRY_NAME', 'ISLAND_NAME', 'SOVEREIGN']


def normalize(d: typing.Dict[str, str]) -> typing.Union[typing.Dict[str, str], None]:
    """
    Normalize field names and field content for country and island names.

    Return `None` if the record does not contain metadata about a language polygon.
    """
    for k in ['ISLAND_NAM', 'ISLAND_NA_', 'ISL_NAM']:  # Spelling "variants".
        if k in d:
            v = d.pop(k)
            d['ISLAND_NAME'] = {  # Typos:
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
