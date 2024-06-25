from setuptools import setup, find_packages


setup(
    name='cldfbench_languageatlasofthepacificarea',
    py_modules=['cldfbench_languageatlasofthepacificarea'],
    packages=find_packages(where='.'),
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
        'fiona',
        'shapely',
        'cldfgeojson',
        'mako',
        'matplotlib',
        'tqdm',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
