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
from utils import *

if sys.version_info < (3, 6):
    raise ImportError('Compatible only with Python 3.6 and newer')


def get_catalog(frequency_limits: Tuple[float, float] = (-math.inf, math.inf)) -> \
        List[Dict[str, Union[int, str, List[Dict[str, float]]]]]:
    """
    Download the spectral lines catalog data

    :param tuple frequency_limits: the frequency range of the catalog entries to keep.
    :return: a list of the spectral lines catalog entries.
    """

    def get(url: str) -> str:
        response = urlopen(url)
        return response.read().decode()

    def post(url: str, data: Dict) -> str:
        response = urlopen(Request(url, data=urlencode(data).encode()))
        return response.read().decode()

    def get_species() -> List[Dict[str, Union[int, str]]]:
        def purge_null_data(entry: Dict[str, Union[None, int, str]]) -> Dict[str, Union[int, str]]:
            for key, value in entry.copy().items():
                if value is None or value in ('', 'None'):
                    del entry[key]
            return entry

        data = json.loads(post('https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/', {'database': -1}))
        if 'species' in data:
            return [purge_null_data(s) for s in data['species']]
        else:
            return []

    def get_substance_catalog(species_entry: Dict[str, Union[int, str]]) \
            -> Dict[str, Union[int, str, List[Dict[str, float]]]]:
        if SPECIES_TAG not in species_entry:
            # nothing to go on with
            return dict()
        species_tag: int = species_entry[SPECIES_TAG]
        fn: str = f'c{species_tag:06}.cat'
        if species_tag % 1000 > 500:
            fn = 'https://cdms.astro.uni-koeln.de/classic/entries/' + fn
        else:
            if fn in ('c044009.cat', 'c044012.cat'):  # merged with c044004.cat — Brian J. Drouin
                return dict()
            else:
                fn = 'https://spec.jpl.nasa.gov/ftp/pub/catalog/' + fn
        try:
            lines = get(fn).splitlines()
        except HTTPError as ex:
            print(str(ex), fn)
            return dict()
        catalog_entries = [CatalogEntry(line) for line in lines]
        return {
            **species_entry,
            DEGREES_OF_FREEDOM: catalog_entries[0].degrees_of_freedom,
            LINES: [catalog_entry.to_dict()
                    for catalog_entry in catalog_entries
                    if within(catalog_entry.frequency, frequency_limits)]
        }

    catalog: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] \
        = [get_substance_catalog(e) for e in get_species()]
    return [catalog_entry for catalog_entry in catalog
            if catalog_entry and LINES in catalog_entry and catalog_entry[LINES]]


def save_catalog(filename: str,
                 frequency_limits: Tuple[float, float] = (-math.inf, math.inf), *,
                 qt_json_filename: str = '', qt_json_zipped: bool = True):
    """
    Download and save the spectral lines catalog data

    :param str filename: the name of the file to save the downloaded catalog to.
        It should end with `'.json.gz'`, otherwise `'.json.gz'` is appended to it.
    :param tuple frequency_limits: the tuple of the maximal and the minimal frequencies of the lines being stored.
        All the lines outside the specified frequency range are omitted.
    :param str qt_json_filename: the name of the catalog saved as a binary representation of `QJsonDocument`.
        If the value is omitted, nothing gets stored.
    :param bool qt_json_zipped: the flag to indicate whether the data stored into ``qt_json_filename`` is compressed.
        Default is `True`.
    """
    if not filename.endswith('.json.gz'):
        filename += '.json.gz'
    catalog: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = get_catalog(frequency_limits)
    if catalog:
        with gzip.open(filename, 'wb') as f:
            f.write(json.dumps({
                CATALOG: catalog,
                FREQUENCY: frequency_limits
            }, indent=4).encode())
        if qt_json_filename:
            from PyQt5.QtCore import qCompress, QJsonDocument
            if qt_json_zipped:
                with open(qt_json_filename, 'wb') as f:
                    f.write(qCompress(QJsonDocument({
                        CATALOG: catalog,
                        FREQUENCY: frequency_limits
                    }).toBinaryData()).data())
            else:
                with open(qt_json_filename, 'wb') as f:
                    f.write(QJsonDocument({
                        CATALOG: catalog,
                        FREQUENCY: frequency_limits
                    }).toBinaryData().data())


if __name__ == '__main__':
    save_catalog('/tmp/c2', (115000, 178000), qt_json_filename='/tmp/c2.qbjsz')
