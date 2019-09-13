# -*- coding: utf-8 -*-
import gzip
import json
import math
import os.path
import sys
from typing import Any, Dict, List, Tuple, Union

from utils import *

if sys.version_info < (3, 6):
    raise ImportError('Compatible only with Python 3.6 and newer')


_CATALOG: str = 'catalog'
_FREQUENCY: str = 'frequency'
_INTENSITY: str = 'intensity'
_DEGREES_OF_FREEDOM: str = 'degreesoffreedom'
_LOWER_STATE_ENERGY: str = 'lowerstateenergy'


class Catalog:
    def __init__(self, *catalog_file_names: str):
        self._data: Union[None,
                          Dict[str, Union[Tuple[Tuple[float, float], ...],
                                          List[Dict[str, Union[int,
                                                               str,
                                                               List[Dict[str, float]]]]]]]] = None
        self._min_frequency = math.nan
        self._max_frequency = math.nan

        def merge_catalogs(*args: List[Dict[str, Union[int, str, List[Dict[str, float]]]]]):
            return sum(args)

        def merge_frequency_tuples(*args: Tuple[float, float]) -> Tuple[Tuple[float, float], ...]:
            if not args:
                return tuple()
            ranges: Tuple[Tuple[float, float], ...] = tuple()
            skip: int = 0
            for i in range(len(args)):
                if skip > 0:
                    skip -= 1
                    continue
                current_range: Tuple[float, float] = args[i]
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
                # print(filename)
                with gzip.GzipFile(filename, 'rb') if filename.endswith('.json.gz') else open(filename, 'r') as fin:
                    content = fin.read()
                    if isinstance(content, bytes):
                        content = content.decode()
                    try:
                        json_data = json.loads(content)
                    except json.decoder.JSONDecodeError:
                        json_data = None
                    if json_data is not None and self._data is None:
                        self._data = {
                            _CATALOG: json_data[_CATALOG],
                            _FREQUENCY: (json_data[_FREQUENCY],)
                        }
                    else:
                        self._data = {
                            _CATALOG: merge_catalogs(self._data[_CATALOG], json_data[_CATALOG]),
                            _FREQUENCY: merge_frequency_tuples(*self._data[_FREQUENCY], json_data[_FREQUENCY])
                        }

    @property
    def catalog(self) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
        return self._data[_CATALOG] if self._data else []

    @property
    def frequency_limits(self) -> Tuple[Tuple[float, float], ...]:
        return self._data[_FREQUENCY] if self._data else (-math.inf, math.inf)

    @staticmethod
    def _filter_by_frequency_and_intensity(catalog_entry: Dict[str, Union[int, str, List[Dict[str, float]]]],
                                           min_frequency: float = -math.inf,
                                           max_frequency: float = math.inf,
                                           min_intensity: float = -math.inf,
                                           max_intensity: float = math.inf,
                                           *, temperature: float = -math.inf) \
            -> Dict[str, Union[int, str, List[Dict[str, float]]]]:
        def intensity(entry) -> float:
            if catalog_entry[_DEGREES_OF_FREEDOM] >= 0 and temperature > 0. and temperature != T0:
                return entry[_INTENSITY] \
                       + ((0.5 * catalog_entry[_DEGREES_OF_FREEDOM] + 1.0) * math.log(T0 / temperature)
                          - ((1 / temperature - 1 / T0) * entry[_LOWER_STATE_ENERGY] * 100. * h * c / k)) / M_LOG10E
            else:
                return entry[_INTENSITY]

        new_catalog_entry = catalog_entry.copy()
        if _CATALOG in new_catalog_entry:
            new_catalog_entry[_CATALOG] = \
                list(filter(lambda e: (min_frequency <= e[_FREQUENCY] <= max_frequency
                                       and min_intensity <= intensity(e) <= max_intensity),
                            catalog_entry[_CATALOG]))
        else:
            new_catalog_entry[_CATALOG] = []
        return new_catalog_entry

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
               degrees_of_freedom: Union[None, int] = None
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
        :param str species_tag: a string to match the ``speciestag`` field.
        :param str inchi: a string to match the ``inchikey`` field.
                          See https://iupac.org/who-we-are/divisions/division-details/inchi/ for more.
        :param str trivial_name: a string to match the ``trivialname`` field.
        :param str structural_formula: a string to match the ``structuralformula`` field.
        :param str name: a string to match the ``name`` field.
        :param str stoichiometric_formula: a string to match the ``stoichiometricformula`` field.
        :param str isotopolog: a string to match the ``isotopolog`` field.
        :param str state: a string to match the ``isotopolog`` or the ``state_html`` field.
        :param int degrees_of_freedom: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
        :raises: :class:`ValueError`: Invalid frequency range
                 if the specified frequency range does not intersect with the catalog one.
        :return: a list of substances with non-empty lists of absorption lines that match all the conditions.
        """

        def same_entry(entry_1: Dict[str, Union[int, str, List[Dict[str, float]]]],
                       entry_2: Dict[str, Union[int, str, List[Dict[str, float]]]]) -> bool:
            if len(entry_1) != len(entry_2):
                return False
            for key, value in entry_1.items():
                if key not in entry_2:
                    return False
                if key != _CATALOG and value != entry_2[key]:
                    return False
                if key == _CATALOG and len(value) != len(entry_2[key]):
                    return False
            return True

        if (min_frequency > max_frequency
                or min_frequency > self._max_frequency
                or max_frequency < self._min_frequency):
            raise ValueError('Invalid frequency range')
        if (species_tag or inchi or trivial_name or structural_formula or name or stoichiometric_formula
                or isotopolog or state or degrees_of_freedom):
            selected_entries = []
            for e in self.catalog:
                if ((not species_tag or e['speciestag'] == species_tag)
                        and (not inchi or e['inchikey'] == inchi)
                        and (not trivial_name or e['trivialname'] == trivial_name)
                        and (not structural_formula or e['structuralformula'] == structural_formula)
                        and (not name or e['name'] == name)
                        and (not stoichiometric_formula or e['stoichiometricformula'] == stoichiometric_formula)
                        and (not isotopolog or e['isotopolog'] == isotopolog)
                        and (not state or e['state'] == state or e['state_html'] == state)
                        and (degrees_of_freedom is None or e[_DEGREES_OF_FREEDOM] == degrees_of_freedom)
                        and (not any_name or e['trivialname'] == any_name or e['name'] == any_name)
                        and (not any_formula
                             or e['structuralformula'] == any_formula
                             or e['moleculesymbol'] == any_formula
                             or e['stoichiometricformula'] == any_formula
                             or e['isotopolog'] == any_formula)
                        and (not any_name_or_formula
                             or e['trivialname'] == any_name_or_formula
                             or e['name'] == any_name_or_formula
                             or e['structuralformula'] == any_name_or_formula
                             or e['moleculesymbol'] == any_name_or_formula
                             or e['stoichiometricformula'] == any_name_or_formula
                             or e['isotopolog'] == any_name_or_formula)):
                    filtered_entry = self._filter_by_frequency_and_intensity(e,
                                                                             min_frequency, max_frequency,
                                                                             min_intensity, max_intensity,
                                                                             temperature=temperature)
                    if filtered_entry[_CATALOG]:
                        selected_entries.append(filtered_entry)
        else:
            filtered_entries = [self._filter_by_frequency_and_intensity(e,
                                                                        min_frequency, max_frequency,
                                                                        min_intensity, max_intensity,
                                                                        temperature=temperature)
                                for e in self._data[_CATALOG]]
            selected_entries = [e for e in filtered_entries if e[_CATALOG]]
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

    def print(self, **kwargs):
        """
        Print a table of the filtered catalog entries

        :param kwargs: all arguments that are valid for :func:`filter <catalog.Catalog.filter>`
        :return: nothing
        """
        entries: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = self.filter(**kwargs)
        names: List[str] = []
        frequencies: List[float] = []
        intensities: List[float] = []
        for e in entries:
            for line in e[_CATALOG]:
                names.append(e['name'])
                frequencies.append(line[_FREQUENCY])
                intensities.append(line[_INTENSITY])

        def max_width(items: List[Any]) -> int:
            w: int = 0
            for item in items:
                s = str(item)
                w = max(w, len(s))
            return w

        names_width: int = max_width(names)
        frequencies_width: int = max_width(frequencies)
        intensities_width: int = max_width(intensities)
        for j, (n, f, i) in enumerate(zip(names, frequencies, intensities)):
            print(f'{n:<{names_width}} {f:>{frequencies_width}} {i:>{intensities_width}}')
