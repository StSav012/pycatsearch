# pycatsearch

Yet another implementation of [JPL](https://spec.jpl.nasa.gov/) and [CDMS](https://astro.uni-koeln.de/) spectroscopy catalogs offline search.

It consists of two parts:

### `catalog`

###### Sample usage:
```python
from catalog import Catalog
c = Catalog('catalog.json.gz')
c.print(min_frequency=140141, max_frequency=140142)
```

###### Properties:
- `catalog` is a list of the catalog entries loaded by `__init__`.
- `frequency_limits` is a tuple of the minimal and the maximal frequencies of the lines
  the loaded catalogs contain.
- `is_empty` indicates whether nothing has been loaded by `__init__`.
- `sources` contains a list of files that have been loaded successfully by `__init__`.

###### Functions:
- `__init__(self, *catalog_file_names: str)` accepts names of JSON or GZipped JSON files.
  It loads them into memory joined.
- `filter(self, *,
               min_frequency: float = -math.inf,
               max_frequency: float = math.inf,
               min_intensity: float = -math.inf,
               max_intensity: float = math.inf,
               temperature: float = -math.inf,
               any_name: str = '',
               any_formula: str = '',
               any_name_or_formula: str = '',
               species_tag: int = 0,
               inchi: str = '',
               trivial_name: str = '',
               structural_formula: str = '',
               name: str = '',
               stoichiometric_formula: str = '',
               isotopolog: str = '',
               state: str = '',
               degrees_of_freedom: Union[None, int] = None) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]`
  returns only the catalog entries that meet the criteria specified. The arguments are the following:
    - `float min_frequency`: the lower frequency \[MHz\] to take.
    - `float max_frequency`: the upper frequency \[MHz\] to take.
    - `float min_intensity`: the minimal intensity \[log10(nm²×MHz)\] to take.
    - `float max_intensity`: the maximal intensity \[log10(nm²×MHz)\] to take, use to avoid meta-stable substances.
    - `float temperature`: the temperature to calculate the line intensity at,
      use the catalog intensity if not set.
    - `str any_name`: a string to match the ``trivialname`` or the ``name`` field.
    - `str any_formula`: a string to match the ``structuralformula``, ``moleculesymbol``,
      ``stoichiometricformula``, or ``isotopolog`` field.
    - `str any_name_or_formula`: a string to match any field used by :param:any_name and :param:any_formula.
    - `str species_tag`: a number to match the ``speciestag`` field.
    - `str inchi`: a string to match the ``inchikey`` field.
      See https://iupac.org/who-we-are/divisions/division-details/inchi/ for more.
    - `str trivial_name`: a string to match the ``trivialname`` field.
    - `str structural_formula`: a string to match the ``structuralformula`` field.
    - `str name`: a string to match the ``name`` field.
    - `str stoichiometric_formula`: a string to match the ``stoichiometricformula`` field.
    - `str isotopolog`: a string to match the ``isotopolog`` field.
    - `str state`: a string to match the ``isotopolog`` or the ``state_html`` field.
    - `int degrees_of_freedom`: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
- `print(**kwargs)` prints a table of the filtered catalog entries.
  It accepts all the arguments valid for the `filter` function.

### `downloader`

###### Sample usage:
```python
import downloader
downloader.save_catalog('catalog.json.gz', (115000, 178000), qt_json_filename='catalog.qbjsz', qt_json_zipped=True)
```

###### Functions:
- `get_catalog(frequency_limits: Tuple[float, float] = (-math.inf, math.inf)) ->
  List[Dict[str, Union[int, str, List[Dict[str, float]]]]]` downloads the spectral lines catalog data.
  It returns a list of the spectral lines catalog entries.
  The parameter `frequency_limits` is the frequency range of the catalog entries to keep.
  By default, there are no limits.
- `save_catalog(filename: str, frequency_limits: Tuple[float, float] = (-math.inf, math.inf), *,
  qt_json_filename: str = '', qt_json_zipped: bool = True)` downloads and saves the spectral lines catalog data.
  Inside, the `get_catalog` function is called.
  The parameters of `save_catalog` are the following:
    - `str filename`: the name of the file to save the downloaded catalog to.
      It should end with `'.json.gz'`, otherwise `'.json.gz'` is appended to it.
    - `tuple frequency_limits`: the tuple of the maximal and the minimal frequencies of the lines being stored.
      All the lines outside the specified frequency range are omitted. By default, there are no limits.
    - `str qt_json_filename`: the name of the catalog saved as a binary representation of `QJsonDocument`.
      If the value is omitted, nothing gets stored.
    - `bool qt_json_zipped`: the flag to indicate whether the data stored into ``qt_json_filename`` is compressed.
      Default is `True`.

### Requirements

The code is developed under `python 3.7.5`. It should work under `python 3.6` but not tested.

If you want to save the catalog as a [Qt JSON Document](https://doc.qt.io/qt-5/qjsondocument.html),
then `PyQt5` is needed. Otherwise, only the built-ins are used.
