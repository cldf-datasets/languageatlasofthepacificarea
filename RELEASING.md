# Releasing

Install required packages:
```shell
pip install -e .
```

Note that [GDAL](https://gdal.org/) is required to run the CLDF creation. Known working versions of
GDAL are 3.4.1 and 3.9.0.

Recreate the CLDF dataset:
```shell
cldfbench download cldfbench_languageatlasofthepacificarea.py
cldfbench makecldf cldfbench_languageatlasofthepacificarea.py --glottolog-version v5.0
```

Run the consistency checks on the dataset:
```shell
pytest
```

Create the metadata for Zenodo:
```shell
cldfbench zenodo cldfbench_languageatlasofthepacificarea.py
```

```shell
cldfbench cldfreadme cldfbench_languageatlasofthepacificarea.py 
```

```shell
cldfviz.erd --format compact.svg cldf > etc/erd.svg
```

```shell
cldfbench readme cldfbench_languageatlasofthepacificarea.py 
```

Recreate the browseable Atlas:
```shell
cldfbench laotpa.browser
```
