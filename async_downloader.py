# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import gzip
import json
import sys
from math import inf
from typing import Any, BinaryIO, cast
from urllib.error import HTTPError
from urllib.parse import urlencode

import aiohttp
import aiohttp.client_exceptions

from catalog_entry import CatalogEntry
from utils import *

__all__ = ['get_catalog', 'save_catalog']


def get_catalog(frequency_limits: tuple[float, float] = (-inf, inf)) \
        -> list[dict[str, int | str | list[dict[str, float]]]]:
    """
    Download the spectral lines catalog data

    :param tuple frequency_limits: the frequency range of the catalog entries to keep.
    :return: a list of the spectral lines catalog entries.
    """

    async def async_get_catalog() -> list[dict[str, int | str | list[dict[str, float]]]]:
        # the two following variables are to protect the server (and the network channel) from overloading
        max_get_requests: int = 1 << 32
        get_requests: int = 0

        async def get(url: str) -> str:
            nonlocal get_requests, max_get_requests
            async with aiohttp.ClientSession() as session:
                while True:
                    try:
                        get_requests += 1
                        while get_requests > max_get_requests:
                            await asyncio.sleep(1)
                        async with session.get(url, ssl=False) as response:
                            get_requests -= 1
                            return (await response.read()).decode()
                    except aiohttp.client_exceptions.ClientConnectorError as ex:
                        get_requests -= 1
                        max_get_requests = get_requests
                        print(str(ex.args[1]), 'to', url)
                        await asyncio.sleep(1)

        async def post(url: str, data: dict[str, Any]) -> str:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=urlencode(data).encode()) as response:
                    return (await response.read()).decode()

        async def get_species() -> list[dict[str, int | str]]:
            def purge_null_data(entry: dict[str, None | int | str]) -> dict[str, int | str]:
                key: str
                value: None | int | str
                return dict((key, value) for key, value in entry.items()
                            if value is not None and value not in ('', 'None'))

            def trim_strings(entry: dict[str, None | int | str]) -> dict[str, None | int | str]:
                key: str
                for key in entry:
                    if isinstance(entry[key], str):
                        entry[key] = cast(str, entry[key]).strip()
                return entry

            data: dict[str, int | str | list[dict[str, None | int | str]]] \
                = json.loads(await post('https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/',
                                        {'database': -1}))
            if 'species' in data:
                return [purge_null_data(trim_strings(s)) for s in data['species']]
            else:
                return []

        async def get_substance_catalog(species_entry: dict[str, int | str]) \
                -> dict[str, int | str | list[dict[str, float]]]:
            if SPECIES_TAG not in species_entry:
                # nothing to go on with
                return dict()
            species_tag: int = cast(int, species_entry[SPECIES_TAG])
            fn: str = f'c{species_tag:06}.cat'
            if species_tag % 1000 >= 500:
                fn = 'https://cdms.astro.uni-koeln.de/classic/entries/' + fn
            else:
                if fn in ('c044009.cat', 'c044012.cat'):  # merged with c044004.cat — Brian J. Drouin
                    return dict()
                else:
                    fn = 'https://spec.jpl.nasa.gov/ftp/pub/catalog/' + fn
            try:
                lines = (await get(fn)).splitlines()
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

        catalog: list[dict[str, int | str | list[dict[str, float]]]] \
            = list(await asyncio.gather(*[asyncio.create_task(get_substance_catalog(_e))
                                          for _e in await get_species()]))
        return [catalog_entry for catalog_entry in catalog
                if catalog_entry and LINES in catalog_entry and catalog_entry[LINES]]

    return asyncio.run(async_get_catalog())


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
        import importlib

        qt_core = None
        for qt in ('PySide6', 'PyQt6', 'PyQt5', 'PySide2'):
            try:
                qt_core = importlib.import_module(f'{qt}.QtCore')
            except (ImportError, ModuleNotFoundError):
                pass
            else:
                break
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
            print('No Qt realization found', file=sys.stderr)
    return True


if __name__ == '__main__':
    from datetime import datetime

    print(datetime.now())
    save_catalog('catalog_110-170.json.gz', (110000, 170000))
    print(datetime.now())
