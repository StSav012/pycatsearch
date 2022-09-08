# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import json
import logging
from http.client import HTTPResponse
from math import inf
from types import ModuleType
from typing import Any, BinaryIO, cast
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from catalog_entry import CatalogEntry
from utils import *

__all__ = ['get_catalog', 'save_catalog']

logger: logging.Logger = logging.getLogger('downloader')


def get_catalog(frequency_limits: tuple[float, float] = (-inf, inf)) -> \
        list[dict[str, int | str | list[dict[str, float]]]]:
    """
    Download the spectral lines catalog data

    :param tuple frequency_limits: the frequency range of the catalog entries to keep.
    :return: a list of the spectral lines catalog entries.
    """

    def get(url: str) -> str:
        response: HTTPResponse = urlopen(url)
        return response.read().decode()

    def post(url: str, data: dict[str, Any]) -> str:
        response: HTTPResponse = urlopen(Request(url, data=urlencode(data).encode()))
        return response.read().decode()

    def get_species() -> list[dict[str, int | str]]:
        def purge_null_data(entry: dict[str, None | int | str]) -> dict[str, int | str]:
            key: str
            value: None | int | str
            return dict((key, value) for key, value in entry.items() if value is not None and value not in ('', 'None'))

        def trim_strings(entry: dict[str, None | int | str]) -> dict[str, None | int | str]:
            key: str
            for key in entry:
                if isinstance(entry[key], str):
                    entry[key] = cast(str, entry[key]).strip()
            return entry

        data: dict[str, int | str | list[dict[str, None | int | str]]] \
            = json.loads(post('https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/', {'database': -1}))
        if 'species' in data:
            return [purge_null_data(trim_strings(s)) for s in data['species']]
        else:
            return []

    def get_substance_catalog(species_entry: dict[str, int | str]) -> dict[str, int | str | list[dict[str, float]]]:
        def entry_url(species_tag: int) -> str:
            entry_filename: str = f'c{species_tag:06}.cat'
            if entry_filename in ('c044009.cat', 'c044012.cat'):  # merged with c044004.cat — Brian J. Drouin
                return ''
            if species_tag % 1000 > 500:
                return 'https://cdms.astro.uni-koeln.de/classic/entries/' + entry_filename
            else:
                return 'https://spec.jpl.nasa.gov/ftp/pub/catalog/' + entry_filename

        if SPECIES_TAG not in species_entry:
            # nothing to go on with
            return dict()
        fn: str = entry_url(species_tag=cast(int, species_entry[SPECIES_TAG]))
        if not fn:  # no need to download a file for the species tag
            return dict()
        try:
            logger.debug(f'getting {fn}')
            lines = get(fn).splitlines()
        except HTTPError as ex:
            logger.error(fn, exc_info=ex)
            return dict()
        catalog_entries = [CatalogEntry(line) for line in lines]
        if not catalog_entries:
            logger.warning('no entries in the catalog')
            return dict()
        return {
            **species_entry,
            DEGREES_OF_FREEDOM: catalog_entries[0].degrees_of_freedom,
            LINES: [catalog_entry.to_dict()
                    for catalog_entry in catalog_entries
                    if within(catalog_entry.frequency, frequency_limits)]
        }

    catalog: list[dict[str, int | str | list[dict[str, float]]]] = [get_substance_catalog(_e) for _e in get_species()]
    return [catalog_entry for catalog_entry in catalog
            if catalog_entry and LINES in catalog_entry and catalog_entry[LINES]]


def save_catalog(filename: str,
                 frequency_limits: tuple[float, float] = (-inf, inf), *,
                 qt_json_filename: str = '', qt_json_zipped: bool = True) -> bool:
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
    catalog: list[dict[str, int | str | list[dict[str, float]]]] = get_catalog(frequency_limits)
    if not catalog:
        return False

    f: BinaryIO | gzip.GzipFile
    with gzip.open(filename, 'wb') as f:
        f.write(json.dumps({
            CATALOG: catalog,
            FREQUENCY: frequency_limits
        }, indent=4).encode())
    if qt_json_filename:
        qt_core: ModuleType | None = find_qt_core()
        if qt_core is not None:
            with open(qt_json_filename, 'wb') as f:
                if qt_json_zipped:
                    f.write(qt_core.qCompress(qt_core.QJsonDocument({
                        CATALOG: catalog,
                        FREQUENCY: frequency_limits
                    }).toBinaryData()).data())
                else:
                    f.write(qt_core.QJsonDocument({
                        CATALOG: catalog,
                        FREQUENCY: frequency_limits
                    }).toBinaryData().data())
        else:
            logger.error('No Qt realization found')
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    save_catalog('catalog.json.gz', (115000, 178000))
