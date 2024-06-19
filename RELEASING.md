# Releasing

```shell
cldfbench download cldfbench_languageatlasofthepacificarea.py
cldfbench makecldf cldfbench_languageatlasofthepacificarea.py --glottolog-version v5.0
```

```shell
pytest
```

```shell
cldfbench zenodo cldfbench_languageatlasofthepacificarea.py
```

```shell
cldfbench cldfreadme cldfbench_languageatlasofthepacificarea.py 
```

```shell
cldferd --format compact.svg cldf > etc/erd.svg
```

```shell
cldfbench readme cldfbench_languageatlasofthepacificarea.py 
```

Recreate the browseable Atlas:
```shell
cldfbench laotpa.browser
```
