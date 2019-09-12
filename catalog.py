# -*- coding: utf-8 -*-
import math
import gzip
import json
import os.path
from typing import Union, Tuple, List, Dict, Any


def within(x: float, limits: Tuple[float, float]):
    return min(limits) <= x <= max(limits)


class Catalog:
    def __init__(self, catalog_file_name: str):
        if (catalog_file_name.endswith('.json.gz')
                and os.path.exists(catalog_file_name) and os.path.isfile(catalog_file_name)):
            # print(filename)
            with gzip.GzipFile(catalog_file_name, 'rb') as fin:
                content = fin.read().decode()
                try:
                    self._data = json.loads(content)
                except json.decoder.JSONDecodeError:
                    self._data = None

    @property
    def catalog(self) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
        return self._data['catalog'] if self._data else []

    @property
    def frequency_limits(self):
        return self._data['frequency'] if self._data else (-math.inf, math.inf)

    @staticmethod
    def _filter_by_frequency_and_intensity(catalog_entry: Dict[str, Union[int, str, List[Dict[str, float]]]],
                                           min_frequency: float = -math.inf,
                                           max_frequency: float = math.inf,
                                           min_intensity: float = -math.inf,
                                           max_intensity: float = math.inf) \
            -> Dict[str, Union[int, str, List[Dict[str, float]]]]:
        new_catalog_entry = catalog_entry.copy()
        if 'catalog' in new_catalog_entry:
            new_catalog_entry['catalog'] = list(filter(lambda e: (min_frequency <= e['frequency'] <= max_frequency
                                                                  and min_intensity <= e['intensity'] <= max_intensity),
                                                       catalog_entry['catalog']))
        else:
            new_catalog_entry['catalog'] = []
        return new_catalog_entry

    def filter(self, *,
               min_frequency: float = -math.inf,
               max_frequency: float = math.inf,
               min_intensity: float = -math.inf,
               max_intensity: float = math.inf,
               any_name: str = '',
               any_formula: str = '',
               any_name_or_formula: str = '',
               species_tag: int = 0,
               inchi: str = '',  # https://iupac.org/who-we-are/divisions/division-details/inchi/
               trivial_name: str = '',
               structural_formula: str = '',
               name: str = '',
               stoichiometric_formula: str = '',
               isotopolog: str = '',
               state: str = '',
               degrees_of_freedom: Union[None, int] = None
               ) -> List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
        if (min_frequency > max_frequency
                or min_frequency > max(self.frequency_limits)
                or max_frequency < min(self.frequency_limits)):
            print('invalid frequency range')
            return []
        if (species_tag or inchi or trivial_name or structural_formula or name or stoichiometric_formula
                or isotopolog or state or degrees_of_freedom):
            selected_entries = []
            for e in self._data['catalog']:
                if ((not species_tag or e['speciestag'] == species_tag)
                        and (not inchi or e['inchikey'] == inchi)
                        and (not trivial_name or e['trivialname'] == trivial_name)
                        and (not structural_formula or e['structuralformula'] == structural_formula)
                        and (not name or e['name'] == name)
                        and (not stoichiometric_formula or e['stoichiometricformula'] == stoichiometric_formula)
                        and (not isotopolog or e['isotopolog'] == isotopolog)
                        and (not state or e['state'] == state or e['state_html'] == state)
                        and (degrees_of_freedom is None or e['degreesoffreedom'] == degrees_of_freedom)
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
                    selected_entries.append(self._filter_by_frequency_and_intensity(e,
                                                                                    min_frequency, max_frequency,
                                                                                    min_intensity, max_intensity))
        else:
            selected_entries = [self._filter_by_frequency_and_intensity(e,
                                                                        min_frequency, max_frequency,
                                                                        min_intensity, max_intensity)
                                for e in self._data['catalog']]
        return selected_entries

    def print(self, **kwargs):
        entries: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = self.filter(**kwargs)
        names: List[str] = []
        frequencies: List[float] = []
        intensities: List[float] = []
        for e in entries:
            for line in e['catalog']:
                names.append(e['name'])
                frequencies.append(line['frequency'])
                intensities.append(line['intensity'])

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
