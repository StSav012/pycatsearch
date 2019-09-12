# -*- coding: utf-8 -*-
import gzip
import json
import math
import sys
from typing import Dict, List, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from catalog_entry import CatalogEntry


if sys.version_info < (3, 6):
    raise ImportError('Compatible only with Python 3.6 and newer')


def within(x: float, limits: Tuple[float, float]):
    return min(limits) <= x <= max(limits)


def get(url: str) -> str:
    response = urlopen(url)
    return response.read().decode()


def post(url: str, data: Dict) -> str:
    response = urlopen(Request(url, data=urlencode(data).encode()))
    return response.read().decode()


def get_species() -> List[Dict[str, Union[int, str]]]:
    data = json.loads(post('https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/', {'database': -1}))
    if 'species' in data:
        return data['species']
    else:
        return []


def get_substance_catalog(species_entry: Dict[str, Union[int, str]],
                          frequency_limits: Tuple[float, float] = (-math.inf, math.inf)) \
        -> Dict[str, Union[int, str, List[Dict[str, float]]]]:
    species_tag: int = species_entry['speciestag']
    # print(species_entry['speciestag'], species_entry['name'])
    fn: str = f'c{species_tag:06}.cat'
    if species_tag % 1000 > 500:
        fn = 'https://cdms.astro.uni-koeln.de/classic/entries/' + fn
    else:
        if fn == 'c044009.cat':  # 404 on spec.jpl.nasa.gov
            fn = 'https://cdms.astro.uni-koeln.de/cdms/portal//getfile/2923/'
        elif fn == 'c044012.cat':  # 404 on spec.jpl.nasa.gov
            fn = 'https://cdms.astro.uni-koeln.de/cdms/portal//getfile/2926/'
        else:
            fn = 'https://spec.jpl.nasa.gov/ftp/pub/catalog/' + fn
    try:
        lines = get(fn).splitlines()
    except HTTPError as ex:
        print(str(ex), fn)
        return dict()
    catalog = [CatalogEntry(line) for line in lines]
    # if not all([(catalog[0].degreesOfFreedom == e.degreesOfFreedom) for e in catalog]):
    #     print('degrees of freedom changes', species_entry['speciestag'], species_entry['name'])
    return {
        **species_entry,
        'degreesoffreedom': catalog[0].degrees_of_freedom,
        'catalog': [catalog_entry.to_dict()
                    for catalog_entry in catalog
                    if within(catalog_entry.frequency, frequency_limits)]
    }


def get_full_catalog(frequency_limits: Tuple[float, float] = (-math.inf, math.inf)) -> \
        List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
    catalog: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] \
        = [get_substance_catalog(e, frequency_limits) for e in get_species()]
    return [catalog_entry for catalog_entry in catalog if catalog_entry and catalog_entry['catalog']]


def save_catalog(filename: str,
                 frequency_limits: Tuple[float, float] = (-math.inf, math.inf)):
    if not filename.endswith('.json.gz'):
        filename += '.json.gz'
    with gzip.open(filename, 'wb') as f:
        f.write(json.dumps({
            'catalog': get_full_catalog(frequency_limits),
            'frequency': frequency_limits
        }, indent=4).encode())
