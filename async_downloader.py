# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import gzip
import json
import logging
import random
from contextlib import suppress
from math import inf
from queue import Empty, Queue
from threading import Thread
from typing import Any, BinaryIO, Final, cast
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse

import aiohttp
import aiohttp.client_exceptions

from catalog_entry import CatalogEntry
from utils import *

__all__ = ['Downloader', 'get_catalog', 'save_catalog']

logger: logging.Logger = logging.getLogger('async_downloader')


class Downloader(Thread):
    def __init__(self,
                 frequency_limits: tuple[float, float] = (-inf, inf),
                 state_queue: Queue[tuple[int, int]] | None = None) -> None:
        super().__init__()
        self._state_queue: Queue[tuple[int, int]] | None = state_queue
        self._frequency_limits: tuple[float, float] = frequency_limits
        self._catalog: list[dict[str, int | str | list[dict[str, float]]]] = []

        self._run: bool = False

    @property
    def catalog(self) -> list[dict[str, int | str | list[dict[str, float]]]]:
        return self._catalog.copy()

    def join(self, timeout: float | None = ...) -> None:
        self._run = False
        super().join(timeout=timeout)

    def run(self) -> None:
        self._run = True

        async def async_get_catalog() -> list[dict[str, int | str | list[dict[str, float]]]]:

            sessions: dict[str, aiohttp.ClientSession] = dict()

            def session_for_url(url: str) -> aiohttp.ClientSession:
                domain: str = urlparse(url).netloc
                if domain not in sessions:
                    sessions[domain] = aiohttp.ClientSession(trust_env=True)
                return sessions[domain]

            async def close_all_sessions() -> None:
                domain: str
                session: aiohttp.ClientSession
                for domain, session in sessions.items():
                    if not session.closed:
                        await session.close()

            async def get(url: str) -> str:
                session: aiohttp.ClientSession = session_for_url(url)
                while self._run:
                    try:
                        async with session.get(url, ssl=False) as response:
                            return (await response.read()).decode()
                    except aiohttp.client_exceptions.ServerDisconnectedError as ex:
                        logger.warning(f'{url}: {str(ex.message)}')
                    except aiohttp.client_exceptions.ClientConnectorError as ex:
                        logger.warning(f'{str(ex.args[1])} to {url}')
                    except aiohttp.client_exceptions.ClientError as ex:
                        logger.warning(f'{url}: ClientError', exc_info=ex)
                    await asyncio.sleep(random.random())
                return ''

            async def post(url: str, data: dict[str, Any]) -> str:
                session: aiohttp.ClientSession = session_for_url(url)
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
                    lines = (await get(fn)).splitlines()
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
                    LINES: [_catalog_entry.to_dict()
                            for _catalog_entry in catalog_entries
                            if within(_catalog_entry.frequency, self._frequency_limits)]
                }

            species: list[dict[str, int | str]] = await get_species()
            catalog: list[dict[str, int | str | list[dict[str, float]]]] = []
            species_count: Final[int] = len(species)
            catalog_entry: dict[str, int | str | list[dict[str, float]]]
            future_entry_index: int
            future_entry: asyncio.Future[dict[str, int | str | list[dict[str, float]]]]
            for future_entry_index, future_entry in enumerate(asyncio.as_completed(
                    [asyncio.create_task(get_substance_catalog(_e)) for _e in species]), start=1):
                catalog_entry = await future_entry
                if catalog_entry and LINES in catalog_entry and catalog_entry[LINES]:
                    catalog.append(catalog_entry)
                if self._state_queue is not None:
                    self._state_queue.put((len(catalog), species_count - future_entry_index))

            await close_all_sessions()

            return catalog

        with suppress(RuntimeError):  # it might be “cannot schedule new futures after shutdown”
            self._catalog = asyncio.run(async_get_catalog())


def get_catalog(frequency_limits: tuple[float, float] = (-inf, inf)) \
        -> list[dict[str, int | str | list[dict[str, float]]]]:
    """
    Download the spectral lines catalog data

    :param tuple frequency_limits: the frequency range of the catalog entries to keep.
    :return: a list of the spectral lines catalog entries.
    """

    state_queue: Queue[tuple[int, int]] = Queue()
    downloader: Downloader = Downloader(frequency_limits=frequency_limits, state_queue=state_queue)
    downloader.start()
    while downloader.is_alive():
        cataloged_species: int
        not_yet_processed_species: int
        try:
            cataloged_species, not_yet_processed_species = state_queue.get(block=True, timeout=0.1)
        except Empty:
            continue
        else:
            logger.info(f'got {cataloged_species} entries, {not_yet_processed_species} left')

    return downloader.catalog


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
            logger.error('No Qt realization found')
    return True


if __name__ == '__main__':
    from datetime import datetime

    logging.basicConfig(level=logging.DEBUG)
    print(datetime.now())
    save_catalog('catalog_110-170.json.gz', (110000, 170000))
    print(datetime.now())