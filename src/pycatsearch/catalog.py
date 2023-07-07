# -*- coding: utf-8 -*-
from __future__ import annotations

import bz2
import gzip
import lzma
import math
from contextlib import contextmanager
from datetime import datetime, timezone
from os import PathLike, fsync
from pathlib import Path
from typing import Any, AnyStr, BinaryIO, Callable, Dict, List, NamedTuple, Optional, TextIO, Union, cast

try:
    import orjson as json
except ImportError:
    import json

from .utils import (M_LOG10E, T0, c, h, k, CATALOG, BUILD_TIME, LINES, FREQUENCY, INTENSITY, STRUCTURAL_FORMULA,
                    STOICHIOMETRIC_FORMULA, MOLECULE_SYMBOL, SPECIES_TAG, NAME, TRIVIAL_NAME, ISOTOPOLOG, STATE,
                    STATE_HTML, INCHI_KEY, DEGREES_OF_FREEDOM, LOWER_STATE_ENERGY,
                    merge_sorted, search_sorted)

__all__ = ['Catalog', 'CatalogSourceInfo', 'LineType', 'LinesType', 'CatalogEntryType']

LineType = Dict[str, float]
LinesType = List[LineType]
CatalogEntryType = Dict[str, Union[int, str, LinesType]]


class CatalogSourceInfo(NamedTuple):
    filename: Path
    build_datetime: datetime | None = None


class CatalogData:
    def __init__(self) -> None:
        self.catalog: list[CatalogEntryType] = []
        self.frequency_limits: tuple[tuple[float, float], ...] = ()

    def append(self,
               catalog: list[CatalogEntryType],
               frequency_limits: tuple[float, float]) -> None:
        def squash_same_species_tag_entries() -> None:
            i: int = 0
            while i < len(self.catalog) - 1:
                while i < len(self.catalog) - 1 and self.catalog[i][SPECIES_TAG] == self.catalog[i + 1][SPECIES_TAG]:
                    self.catalog[i][LINES] = cast(LinesType,
                                                  merge_sorted(self.catalog[i][LINES],
                                                               self.catalog[i + 1][LINES],
                                                               key=lambda line: (line[FREQUENCY],
                                                                                 line[INTENSITY],
                                                                                 line[LOWER_STATE_ENERGY])
                                                               )
                                                  )
                    del self.catalog[i + 1]
                i += 1

        def merge_frequency_tuples(*args: tuple[float, float] | list[float]) -> tuple[tuple[float, float], ...]:
            if not args:
                return tuple()
            ranges: tuple[tuple[float, float], ...] = tuple()
            skip: int = 0
            for i in range(len(args)):
                if skip > 0:
                    skip -= 1
                    continue
                current_range: tuple[float, float] = (float(args[i][0]), float(args[i][-1]))
                current_min: float = min(current_range)
                current_max: float = max(current_range)
                for r in args[1 + i:]:
                    if current_min <= min(r) <= current_max:
                        current_max = max(current_max, *r)
                        skip += 1
                ranges += ((current_min, current_max),)
            return ranges

        self.catalog.extend(sorted(catalog, key=lambda entry: entry[SPECIES_TAG]))
        squash_same_species_tag_entries()
        self.frequency_limits = merge_frequency_tuples(*self.frequency_limits, frequency_limits)


class Catalog:
    DEFAULT_SUFFIX: str = '.json.gz'

    class Opener:
        OPENERS_BY_SUFFIX: dict[str, Callable] = {
            '.json': open,
            '.json.gz': gzip.open,
            '.json.bz2': bz2.open,
            '.json.xz': lzma.open,
            '.json.lzma': lzma.open,
        }

        OPENERS_BY_SIGNATURE: dict[str, Callable] = {
            b'{': open,
            b'\x1F\x8B': gzip.open,
            b'BZh': bz2.open,
            b'\xFD\x37\x7A\x58\x5A\x00': lzma.open,
        }

        def __init__(self, path: str | PathLike[str]) -> None:
            self._path: Path = Path(path)
            self._opener: Callable
            suffix: str = ''
            s: str
            for s in reversed(self._path.suffixes):
                suffix = s + suffix
                if suffix in Catalog.Opener.OPENERS_BY_SUFFIX:
                    self._opener = Catalog.Opener.OPENERS_BY_SUFFIX[suffix]
                    return
            if self._path.exists():
                max_signature_length: int = max(map(len, Catalog.Opener.OPENERS_BY_SIGNATURE.keys()))
                f: BinaryIO
                with self._path.open('rb') as f:
                    init_bytes: bytes = f.read(max_signature_length)
                key: bytes
                value: Callable
                for key, value in Catalog.Opener.OPENERS_BY_SIGNATURE.items():
                    if init_bytes.startswith(key):
                        self._opener = value
                        return

            raise ValueError(f'Unknown file: {path}')

        @contextmanager
        def open(self, mode: str, encoding: str | None = None,
                 errors: str | None = None, newline: str | None = None) -> TextIO | BinaryIO:
            """
            Open a file in a safe way. Create a temporary file when writing.

            See https://stackoverflow.com/a/29491523/8554611, https://stackoverflow.com/a/2333979/8554611
            """
            writing: bool = 'w' in mode.casefold()
            if encoding is None and 'b' not in mode.casefold():
                encoding = 'utf-8'
            tmp_path: Path = self._path.with_name(self._path.name + '.part')
            file: TextIO | BinaryIO
            with self._opener(tmp_path if writing else self._path, mode=mode,
                              encoding=encoding, errors=errors, newline=newline) as file:
                try:
                    yield file
                finally:
                    if writing:
                        file.flush()
                        fsync(file.fileno())
                        tmp_path.replace(self._path)

    def __init__(self, *catalog_file_names: str | PathLike[str]) -> None:
        self._data: CatalogData = CatalogData()
        self._sources: list[CatalogSourceInfo] = []

        filename: Path
        for filename in map(Path, catalog_file_names):
            if filename.exists() and filename.is_file():
                f_in: BinaryIO
                with Catalog.Opener(filename).open('rb') as f_in:
                    content: bytes = f_in.read()
                    try:
                        json_data: dict[str, list[float | None] | list[CatalogEntryType]] = json.loads(content)
                    except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                        pass
                    else:
                        self._data.append(catalog=json_data[CATALOG],
                                          frequency_limits=(json_data[FREQUENCY][0],
                                                            (math.inf if json_data[FREQUENCY][1] is None
                                                             else json_data[FREQUENCY][1])))
                        build_datetime: datetime | None = None
                        if BUILD_TIME in json_data:
                            build_datetime = datetime.fromisoformat(cast(str, json_data[BUILD_TIME]))
                        self._sources.append(CatalogSourceInfo(filename=filename, build_datetime=build_datetime))

    def __bool__(self) -> bool:
        return bool(self._data.catalog)

    @property
    def is_empty(self) -> bool:
        return not bool(self)

    @property
    def sources(self) -> list[Path]:
        source: CatalogSourceInfo
        return [source.filename for source in self._sources]

    @property
    def sources_info(self) -> list[CatalogSourceInfo]:
        return self._sources.copy()

    @property
    def catalog(self) -> list[CatalogEntryType]:
        return self._data.catalog

    @property
    def entries_count(self) -> int:
        return len(self._data.catalog)

    @property
    def frequency_limits(self) -> tuple[tuple[float, float], ...]:
        return self._data.frequency_limits if self._data.catalog else (0.0, math.inf)

    @property
    def min_frequency(self) -> float:
        return min(min(f) for f in self._data.frequency_limits) if self._data.frequency_limits else 0.0

    @property
    def max_frequency(self) -> float:
        return max(max(f) for f in self._data.frequency_limits) if self._data.frequency_limits else math.inf

    def filter(self, *,
               min_frequency: float = 0.0,
               max_frequency: float = math.inf,
               min_intensity: float = -math.inf,
               max_intensity: float = math.inf,
               temperature: float = -math.inf,
               any_name: str = '',
               any_formula: str = '',
               any_name_or_formula: str = '',
               anything: str = '',
               species_tag: int = 0,
               inchi_key: str = '',
               trivial_name: str = '',
               structural_formula: str = '',
               name: str = '',
               stoichiometric_formula: str = '',
               isotopolog: str = '',
               state: str = '',
               degrees_of_freedom: Optional[int] = None,
               ) -> list[CatalogEntryType]:
        """
        Extract only the entries that match all the specified conditions

        :param float min_frequency: the lower frequency [MHz] to take.
        :param float max_frequency: the upper frequency [MHz] to take.
        :param float min_intensity: the minimal intensity [log10(nm²×MHz)] to take.
        :param float max_intensity: the maximal intensity [log10(nm²×MHz)] to take, use to avoid meta-stable substances.
        :param float temperature: the temperature to calculate the line intensity at,
                                  use the catalog intensity if not set.
        :param str any_name: a string to match the ``trivialname`` or the ``name`` field.
        :param str any_formula: a string to match the ``structuralformula``, ``moleculesymbol``,
                                ``stoichiometricformula``, or ``isotopolog`` field.
        :param str any_name_or_formula: a string to match any field used by :param:any_name and :param:any_formula.
        :param str anything: a string to match any field at all.
        :param int species_tag: a number to match the ``speciestag`` field.
        :param str inchi_key: a string to match the ``inchikey`` field.
                              See https://iupac.org/who-we-are/divisions/division-details/inchi/ for more.
        :param str trivial_name: a string to match the ``trivialname`` field.
        :param str structural_formula: a string to match the ``structuralformula`` field.
        :param str name: a string to match the ``name`` field.
        :param str stoichiometric_formula: a string to match the ``stoichiometricformula`` field.
        :param str isotopolog: a string to match the ``isotopolog`` field.
        :param str state: a string to match the ``state`` or the ``state_html`` field.
        :param int degrees_of_freedom: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
        :return: a list of substances with non-empty lists of absorption lines that match all the conditions.
        """

        if self.is_empty:
            return []

        def filter_by_frequency_and_intensity(catalog_entry: CatalogEntryType) -> CatalogEntryType:
            def intensity(_line: LineType) -> float:
                if catalog_entry[DEGREES_OF_FREEDOM] >= 0 and temperature > 0. and temperature != T0:
                    return (_line[INTENSITY] +
                            ((0.5 * catalog_entry[DEGREES_OF_FREEDOM] + 1.0) * math.log(T0 / temperature)
                             - ((1 / temperature - 1 / T0) * _line[LOWER_STATE_ENERGY] * 100. * h * c / k)) / M_LOG10E)
                else:
                    return _line[INTENSITY]

            new_catalog_entry: CatalogEntryType = catalog_entry.copy()
            if LINES in new_catalog_entry and new_catalog_entry[LINES]:
                min_frequency_index: int = search_sorted(min_frequency, new_catalog_entry[LINES],
                                                         key=lambda line: line[FREQUENCY]) + 1
                max_frequency_index: int = search_sorted(max_frequency, new_catalog_entry[LINES],
                                                         key=lambda line: line[FREQUENCY], maybe_equal=True)
                new_catalog_entry[LINES] = \
                    [line for line in new_catalog_entry[LINES][min_frequency_index:(max_frequency_index + 1)]
                     if min_intensity <= intensity(line) <= max_intensity]
            else:
                new_catalog_entry[LINES] = []
            return new_catalog_entry

        if (min_frequency > max_frequency
                or min_frequency > self.max_frequency
                or max_frequency < self.min_frequency):
            return []
        if (species_tag or inchi_key or trivial_name or structural_formula or name or stoichiometric_formula
                or isotopolog or state or degrees_of_freedom or any_name or any_formula or any_name_or_formula
                or anything):
            trivial_name: str = trivial_name.casefold()
            name: str = name.casefold()
            any_name: str = any_name.casefold()
            any_name_or_formula_lowercase: str = any_name_or_formula.casefold()
            anything_lowercase: str = anything.casefold()
            selected_entries: list[CatalogEntryType] = []
            for entry in self.catalog:
                if ((not species_tag or entry.get(SPECIES_TAG, 0) == species_tag)
                        and (not inchi_key or entry.get(INCHI_KEY, '') == inchi_key)
                        and (not trivial_name or entry.get(TRIVIAL_NAME, '').casefold() == trivial_name)
                        and (not structural_formula or entry.get(STRUCTURAL_FORMULA, '') == structural_formula)
                        and (not name or entry.get(NAME, '').casefold() == name)
                        and (not stoichiometric_formula
                             or entry.get(STOICHIOMETRIC_FORMULA, '') == stoichiometric_formula)
                        and (not isotopolog or entry.get(ISOTOPOLOG, '') == isotopolog)
                        and (not state or state in (entry.get(STATE, ''), entry.get(STATE_HTML, '')))
                        and (degrees_of_freedom is None or entry.get(DEGREES_OF_FREEDOM, -1) == degrees_of_freedom)
                        and (not any_name
                             or any_name in (entry.get(TRIVIAL_NAME, '').casefold(),
                                             entry.get(NAME, '').casefold(),))
                        and (not any_formula
                             or any_formula in (entry.get(STRUCTURAL_FORMULA, ''),
                                                entry.get(MOLECULE_SYMBOL, ''),
                                                entry.get(STOICHIOMETRIC_FORMULA, ''),
                                                entry.get(ISOTOPOLOG, ''),))
                        and (not any_name_or_formula
                             or any_name_or_formula_lowercase in (entry.get(TRIVIAL_NAME, '').casefold(),
                                                                  entry.get(NAME, '').casefold(),)
                             or any_name_or_formula in (entry.get(STRUCTURAL_FORMULA, ''),
                                                        entry.get(MOLECULE_SYMBOL, ''),
                                                        entry.get(STOICHIOMETRIC_FORMULA, ''),
                                                        entry.get(ISOTOPOLOG, ''),))
                        and (not anything
                             or anything in (str(entry[key]) for key in entry if key != LINES)
                             or anything_lowercase in (entry.get(TRIVIAL_NAME, '').casefold(),
                                                       entry.get(NAME, '').casefold(),))
                ):
                    filtered_entry: CatalogEntryType = filter_by_frequency_and_intensity(entry)
                    if filtered_entry[LINES]:
                        selected_entries.append(filtered_entry)
        else:
            filtered_entries: list[CatalogEntryType] = [
                filter_by_frequency_and_intensity(entry)
                for entry in self._data.catalog
            ]
            selected_entries = [entry for entry in filtered_entries if entry[LINES]]
        return selected_entries

    def print(self, **kwargs: None | int | float | str) -> None:
        """
        Print a table of the filtered catalog entries

        :param kwargs: all arguments that are valid for :func:`filter <catalog.Catalog.filter>`
        :return: nothing
        """
        entries: list[CatalogEntryType] = self.filter(**kwargs)
        if not entries:
            print('nothing found')
            return

        names: list[str] = []
        frequencies: list[float] = []
        intensities: list[float] = []
        for entry in entries:
            for line in cast(LinesType, entry[LINES]):
                names.append(entry[NAME])
                frequencies.append(line[FREQUENCY])
                intensities.append(line[INTENSITY])

        def max_width(items: list[Any]) -> int:
            return max(len(str(item)) for item in items)

        names_width: int = max_width(names)
        frequencies_width: int = max_width(frequencies)
        intensities_width: int = max_width(intensities)
        for j, (n, f, i) in enumerate(zip(names, frequencies, intensities)):
            print(f'{n:<{names_width}} {f:>{frequencies_width}} {i:>{intensities_width}}')

    @staticmethod
    def save(filename: str | PathLike[str],
             catalog: list[CatalogEntryType],
             frequency_limits: tuple[float, float] = (0.0, math.inf),
             build_time: datetime | None = None) -> None:
        if build_time is None:
            build_time = datetime.now(tz=timezone.utc)
        data_to_save: dict[str, list[CatalogEntryType] | tuple[float, float] | str] = {
            CATALOG: catalog,
            FREQUENCY: list(frequency_limits),
            BUILD_TIME: build_time.isoformat(),
        }
        opener: Catalog.Opener
        try:
            opener = Catalog.Opener(filename)
        except ValueError:
            filename = Path(filename)
            opener = Catalog.Opener(filename.with_name(filename.name + Catalog.DEFAULT_SUFFIX))

        def ensure_bytes(data: AnyStr) -> bytes:
            if isinstance(data, str):
                return data.encode('utf-8')
            if isinstance(data, bytes):
                return data
            raise TypeError('Unknown conversion to bytes')

        f: BinaryIO
        with opener.open('wb') as f:
            f.write(ensure_bytes(json.dumps(data_to_save)))
