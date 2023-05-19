# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
import random
from contextlib import suppress
from math import inf
from queue import Empty, Queue
from threading import Thread
from typing import Any, Final, Mapping, cast
from urllib.error import HTTPError
from urllib.parse import urlencode

import aiohttp
import aiohttp.client_exceptions

try:
    import orjson as json
except ImportError:
    import json

from .catalog_entry import CatalogEntry
from .utils import *

__all__ = ['Downloader', 'get_catalog', 'save_catalog', 'download']

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
        self._tasks: list[asyncio.Task] = []

    def __del__(self) -> None:
        self._run = False

    @property
    def catalog(self) -> list[dict[str, int | str | list[dict[str, float]]]]:
        return self._catalog.copy()

    def join(self, timeout: float | None = ...) -> None:
        self._run = False
        self.cancel()
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        loop.stop()
        loop.close()
        super().join(timeout=timeout)

    def cancel(self) -> None:
        for task in self._tasks:
            if not task.done():
                task.cancel()

    def run(self) -> None:
        self._run = True

        async def async_get_catalog() -> list[dict[str, int | str | list[dict[str, float]]]]:

            session: aiohttp.ClientSession
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(),  # disable timeout checks
                                             trust_env=True) as session:

                async def get(url: str, headers: Mapping[str, str] | None = None) -> bytes:
                    response: aiohttp.ClientResponse
                    while self._run:
                        try:
                            async with session.get(url, headers=headers) as response:
                                return await response.read()
                        except asyncio.exceptions.CancelledError as ex:
                            if self._run:
                                logger.error(str(ex), exc_info=ex)
                        except aiohttp.client_exceptions.ServerDisconnectedError as ex:
                            logger.warning(f'{url}: {str(ex.message)}')
                        except aiohttp.client_exceptions.ClientConnectorError as ex:
                            logger.warning(f'{str(ex.args[1])} to {url}')
                        except aiohttp.client_exceptions.ClientOSError as ex:
                            logger.warning(f'{url}: {str(ex)}')
                        except aiohttp.client_exceptions.ClientError as ex:
                            logger.error(f'{url}: {str(ex)}', exc_info=ex)
                        with suppress(asyncio.exceptions.CancelledError):
                            await asyncio.sleep(random.random())
                    return bytes()

                async def post(url: str, data: dict[str, Any], headers: Mapping[str, str] | None = None) -> str:
                    async with session.post(url, data=urlencode(data).encode(), headers=headers) as response:
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
                                                {'database': -1},
                                                headers={'Content-Type': 'application/x-www-form-urlencoded'}))
                    if 'species' in data:
                        return [purge_null_data(trim_strings(s)) for s in data['species']]
                    else:
                        return []

                async def get_substance_catalog(species_entry: dict[str, int | str]) \
                        -> dict[str, int | str | list[dict[str, float]]]:
                    def entry_url(species_tag: int) -> str:
                        entry_filename: str = f'c{species_tag:06}.cat'

                        if entry_filename in ('c044009.cat', 'c044012.cat'):
                            return ''  # merged with c044004.cat — Brian J. Drouin
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
                        lines = (await get(fn)).decode().splitlines()
                    except HTTPError as ex:
                        logger.error(fn, exc_info=ex)
                        return dict()
                    catalog_entries = [CatalogEntry(line) for line in lines]
                    if not catalog_entries:
                        if self._run:
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
                self._tasks = [asyncio.create_task(get_substance_catalog(_e)) for _e in species]
                catalog: list[dict[str, int | str | list[dict[str, float]]]] = []
                species_count: Final[int] = len(species)
                catalog_entry: dict[str, int | str | list[dict[str, float]]]
                future_entry_index: int
                future_entry: asyncio.Future[dict[str, int | str | list[dict[str, float]]]]
                for future_entry_index, future_entry in enumerate(asyncio.as_completed(self._tasks), start=1):
                    catalog_entry = await future_entry
                    if catalog_entry and LINES in catalog_entry and catalog_entry[LINES]:
                        catalog.append(catalog_entry)
                    if self._state_queue is not None:
                        self._state_queue.put((len(catalog), species_count - future_entry_index))

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
                 frequency_limits: tuple[float, float] = (0, inf)) -> bool:
    """
    Download and save the spectral lines catalog data

    :param str filename: the name of the file to save the downloaded catalog to.
        If it ends with an unknown suffix, `'.json.gz'` is appended to it.
    :param tuple frequency_limits: the tuple of the maximal and the minimal frequencies of the lines being stored.
        All the lines outside the specified frequency range are omitted.
    """

    return save_catalog_to_file(filename=filename,
                                catalog=get_catalog(frequency_limits),
                                frequency_limits=frequency_limits)


def download() -> None:
    import argparse
    from datetime import datetime

    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='Download JPL and CDMS spectroscopy catalogs for offline search.\n'
                    'Find more at https://github.com/StSav012/pycatsearch.')
    ap.add_argument('catalog', type=str, help='the catalog location to save into (required)')
    ap.add_argument('-f''min', '--min-frequency', type=float, help='the lower frequency [MHz] to take', default=-inf)
    ap.add_argument('-f''max', '--max-frequency', type=float, help='the upper frequency [MHz] to take', default=+inf)
    args: argparse.Namespace = ap.parse_intermixed_args()

    logging.basicConfig(level=logging.DEBUG)
    logger.info(f'started at {datetime.now()}')
    save_catalog(args.catalog, (args.min_frequency, args.max_frequency))
    logger.info(f'finished at {datetime.now()}')
