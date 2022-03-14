# -*- coding: utf-8 -*-
import gzip
import json
import math
import os.path
import time
from numbers import Real
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from utils import *

__all__ = ['Catalog']


class Catalog:
    def __init__(self, *catalog_file_names: str) -> None:
        self._data: Optional[
            Dict[str, Union[Tuple[Tuple[float, float], ...],
                            List[Dict[str, Union[int,
                                                 str,
                                                 List[Dict[str, float]]]]]]]] = None
        self._min_frequency: float = math.nan
        self._max_frequency: float = math.nan
        self._sources: List[str] = []

        def merge_catalogs(*args: List[Dict[str, Union[int, str, List[Dict[str, float]]]]]) \
                -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
            return sum(args, [])

        def merge_frequency_tuples(*args: Union[Tuple[float, float], List[Real]]) -> Tuple[Tuple[float, float], ...]:
            if not args:
                return tuple()
            ranges: Tuple[Tuple[float, float], ...] = tuple()
            skip: int = 0
            for i in range(len(args)):
                if skip > 0:
                    skip -= 1
                    continue
                current_range: Tuple[float, float] = (float(args[i][0]), float(args[i][-1]))
                current_min: float = min(current_range)
                current_max: float = max(current_range)
                for r in args[1 + i:]:
                    if current_min <= min(r) <= current_max:
                        current_max = max(current_max, *r)
                        skip += 1
                ranges += ((current_min, current_max),)
                if math.isnan(self._min_frequency) or self._min_frequency > current_min:
                    self._min_frequency = current_min
                if math.isnan(self._max_frequency) or self._max_frequency < current_max:
                    self._max_frequency = current_max
            return ranges

        for filename in catalog_file_names:
            if os.path.exists(filename) and os.path.isfile(filename):
                with (gzip.GzipFile(filename, 'rb')
                      if filename.casefold().endswith('.json.gz')
                      else open(filename, 'r')) as fin:
                    content = fin.read()
                    if isinstance(content, bytes):
                        content = content.decode()
                    try:
                        json_data: Dict[str, Union[List[Real],
                                                   List[Dict[str, Union[int, str, List[Dict[str, float]]]]]]] \
                            = json.loads(content)
                    except json.decoder.JSONDecodeError:
                        pass
                    else:
                        if self._data is None:
                            self._data = {
                                CATALOG: json_data[CATALOG],
                                FREQUENCY: (json_data[FREQUENCY],)
                            }
                        else:
                            self._data = {
                                CATALOG: merge_catalogs(self.catalog, json_data[CATALOG]),
                                FREQUENCY: merge_frequency_tuples(*self._data[FREQUENCY], json_data[FREQUENCY])
                            }
                        self._sources.append(filename)

    @property
    def is_empty(self) -> bool:
        return self._data is None

    @property
    def sources(self) -> List[str]:
        return self._sources[:]

    @property
    def catalog(self) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
        return self._data[CATALOG] if self._data else []

    @property
    def frequency_limits(self) -> Tuple[Tuple[float, float], ...]:
        return self._data[FREQUENCY] if self._data else (-math.inf, math.inf)

    @property
    def min_frequency(self) -> float:
        return min(min(f) for f in self._data[FREQUENCY]) if self._data else -math.inf

    @property
    def max_frequency(self) -> float:
        return max(max(f) for f in self._data[FREQUENCY]) if self._data else math.inf

    def filter(self, *,
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
               degrees_of_freedom: Optional[int] = None,
               timeout: Optional[float] = None
               ) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
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
        :param str species_tag: a number to match the ``speciestag`` field.
        :param str inchi: a string to match the ``inchikey`` field.
                          See https://iupac.org/who-we-are/divisions/division-details/inchi/ for more.
        :param str trivial_name: a string to match the ``trivialname`` field.
        :param str structural_formula: a string to match the ``structuralformula`` field.
        :param str name: a string to match the ``name`` field.
        :param str stoichiometric_formula: a string to match the ``stoichiometricformula`` field.
        :param str isotopolog: a string to match the ``isotopolog`` field.
        :param str state: a string to match the ``isotopolog`` or the ``state_html`` field.
        :param int degrees_of_freedom: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
        :param float timeout: if positive, the maximum time [seconds] for filtering.
        :raises: :class:`ValueError`: Invalid frequency range
                 if the specified frequency range does not intersect with the catalog one.
        :return: a list of substances with non-empty lists of absorption lines that match all the conditions.
        """

        if self.is_empty:
            return []

        def same_entry(entry_1: Dict[str, Union[int, str, List[Dict[str, float]]]],
                       entry_2: Dict[str, Union[int, str, List[Dict[str, float]]]]) -> bool:
            if len(entry_1) != len(entry_2):
                return False
            for key, value in entry_1.items():
                if key not in entry_2:
                    return False
                if key != LINES and value != entry_2[key]:
                    return False
                if key == LINES and len(value) != len(entry_2[key]):
                    return False
            return True

        def filter_by_frequency_and_intensity(catalog_entry: Dict[str, Union[int, str, List[Dict[str, float]]]]) \
                -> Dict[str, Union[int, str, List[Dict[str, float]]]]:
            def intensity(_entry: Dict[str, float]) -> float:
                if catalog_entry[DEGREES_OF_FREEDOM] >= 0 and temperature > 0. and temperature != T0:
                    return (_entry[INTENSITY]
                            + ((0.5 * catalog_entry[DEGREES_OF_FREEDOM] + 1.0) * math.log(T0 / temperature)
                               - ((1 / temperature - 1 / T0) * _entry[
                                        LOWER_STATE_ENERGY] * 100. * h * c / k)) / M_LOG10E)
                else:
                    return _entry[INTENSITY]

            new_catalog_entry: Dict[str, Union[int, str, List[Dict[str, float]]]] = catalog_entry.copy()
            if LINES in new_catalog_entry:
                new_catalog_entry[LINES] = \
                    list(filter(lambda _e: (min_frequency <= _e[FREQUENCY] <= max_frequency
                                            and min_intensity <= intensity(_e) <= max_intensity),
                                catalog_entry[LINES]))
            else:
                new_catalog_entry[LINES] = []
            return new_catalog_entry

        if (min_frequency > max_frequency
                or min_frequency > self._max_frequency
                or max_frequency < self._min_frequency):
            raise ValueError('Invalid frequency range')
        start_time: float = time.monotonic()
        if (species_tag or inchi or trivial_name or structural_formula or name or stoichiometric_formula
                or isotopolog or state or degrees_of_freedom or any_name or any_formula or any_name_or_formula):
            selected_entries = []
            for entry in self.catalog:
                if timeout is not None and 0.0 < timeout <= time.monotonic() - start_time:
                    break
                if ((not species_tag or (SPECIES_TAG in entry and entry[SPECIES_TAG] == species_tag))
                        and (not inchi or (INCHI_KEY in entry and entry[INCHI_KEY] == inchi))
                        and (not trivial_name
                             or (TRIVIAL_NAME in entry and entry[TRIVIAL_NAME] == trivial_name))
                        and (not structural_formula
                             or (STRUCTURAL_FORMULA in entry and entry[STRUCTURAL_FORMULA] == structural_formula))
                        and (not name or (NAME in entry and entry[NAME] == name))
                        and (not stoichiometric_formula
                             or (STOICHIOMETRIC_FORMULA in entry
                                 and entry[STOICHIOMETRIC_FORMULA] == stoichiometric_formula))
                        and (not isotopolog or (ISOTOPOLOG in entry and entry[ISOTOPOLOG] == isotopolog))
                        and (not state
                             or (STATE in entry and entry[STATE] == state)
                             or (STATE_HTML in entry and entry[STATE_HTML] == state))
                        and (degrees_of_freedom is None
                             or (DEGREES_OF_FREEDOM in entry and entry[DEGREES_OF_FREEDOM] == degrees_of_freedom))
                        and (not any_name
                             or (TRIVIAL_NAME in entry and entry[TRIVIAL_NAME] == any_name)
                             or (NAME in entry and entry[NAME] == any_name))
                        and (not any_formula
                             or (STRUCTURAL_FORMULA in entry and entry[STRUCTURAL_FORMULA] == any_formula)
                             or (MOLECULE_SYMBOL in entry and entry[MOLECULE_SYMBOL] == any_formula)
                             or (STOICHIOMETRIC_FORMULA in entry and entry[STOICHIOMETRIC_FORMULA] == any_formula)
                             or (ISOTOPOLOG in entry and entry[ISOTOPOLOG] == any_formula))
                        and (not any_name_or_formula
                             or (TRIVIAL_NAME in entry and entry[TRIVIAL_NAME] == any_name_or_formula)
                             or (NAME in entry and entry[NAME] == any_name_or_formula)
                             or (STRUCTURAL_FORMULA in entry and entry[STRUCTURAL_FORMULA] == any_name_or_formula)
                             or (MOLECULE_SYMBOL in entry and entry[MOLECULE_SYMBOL] == any_name_or_formula)
                             or (STOICHIOMETRIC_FORMULA in entry
                                 and entry[STOICHIOMETRIC_FORMULA] == any_name_or_formula)
                             or (ISOTOPOLOG in entry and entry[ISOTOPOLOG] == any_name_or_formula))):
                    filtered_entry = filter_by_frequency_and_intensity(entry)
                    if filtered_entry[LINES]:
                        selected_entries.append(filtered_entry)
        else:
            filtered_entries = [filter_by_frequency_and_intensity(entry)
                                for entry in self._data[CATALOG]
                                if timeout is None or (timeout > 0.0 and timeout >= time.monotonic() - start_time)]
            selected_entries = [entry for entry in filtered_entries if entry[LINES]]
        unique_entries = selected_entries
        all_unique: bool = True  # unless the opposite is proven
        for i in range(len(selected_entries)):
            unique: bool = True
            for j in range(i + 1, len(selected_entries)):
                if same_entry(selected_entries[i], selected_entries[j]):
                    unique = False
                    if all_unique:
                        unique_entries = []
                        all_unique = False
            if unique and not all_unique:
                unique_entries.append(selected_entries[i])
        return unique_entries

    def print(self, **kwargs: Union[None, int, float, str]) -> None:
        """
        Print a table of the filtered catalog entries

        :param kwargs: all arguments that are valid for :func:`filter <catalog.Catalog.filter>`
        :return: nothing
        """
        entries: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = self.filter(**kwargs)
        names: List[str] = []
        frequencies: List[float] = []
        intensities: List[float] = []
        for entry in entries:
            for line in cast(List[Dict[str, float]], entry[LINES]):
                names.append(entry[NAME])
                frequencies.append(line[FREQUENCY])
                intensities.append(line[INTENSITY])

        def max_width(items: List[Any]) -> int:
            return max(len(str(item)) for item in items)

        names_width: int = max_width(names)
        frequencies_width: int = max_width(frequencies)
        intensities_width: int = max_width(intensities)
        for j, (n, f, i) in enumerate(zip(names, frequencies, intensities)):
            print(f'{n:<{names_width}} {f:>{frequencies_width}} {i:>{intensities_width}}')
