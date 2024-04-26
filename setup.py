from setuptools import setup


setup(
    name='cldfbench_languageatlasofthepacificarea',
    py_modules=['cldfbench_languageatlasofthepacificarea'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'languageatlasofthepacificarea=cldfbench_languageatlasofthepacificarea:Dataset',
        ],
        'cldfbench.commands': [
            'laotpa=laotpa_commands',
        ]
    },
    install_requires=[
        'cldfbench',
        'pyglottolog',
        'geopandas',
        'shapely',
        'cldfgeojson',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
