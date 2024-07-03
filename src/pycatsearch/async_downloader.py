# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
import random
from contextlib import suppress
from math import inf
from pathlib import Path
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

from .catalog import Catalog, CatalogEntryType, CatalogType
from .catalog_entry import CatalogEntry
from .utils import FREQUENCY, LINES, SPECIES_TAG, DEGREES_OF_FREEDOM, VERSION, within, save_catalog_to_file

__all__ = ["Downloader", "get_catalog", "save_catalog", "download"]

logger: logging.Logger = logging.getLogger("async_downloader")


class Downloader(Thread):
    def __init__(
        self,
        frequency_limits: tuple[float, float] = (-inf, inf),
        *,
        existing_catalog: Catalog | None = None,
        state_queue: Queue[tuple[int, int]] | None = None,
    ) -> None:
        super().__init__()
        self._state_queue: Queue[tuple[int, int]] | None = state_queue
        self._frequency_limits: tuple[float, float] = frequency_limits
        self._catalog: CatalogType = dict()
        self._existing_catalog: Catalog | None = existing_catalog

        self._run: bool = False
        self._tasks: list[asyncio.Task] = []

    def __del__(self) -> None:
        self.stop()

    @property
    def catalog(self) -> CatalogType:
        return self._catalog.copy()

    def stop(self) -> None:
        self._run = False

    def join(self, timeout: float | None = None) -> None:
        self.stop()
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

        async def async_get_catalog() -> CatalogType:
            session: aiohttp.ClientSession
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(),  # disable timeout checks
                trust_env=True,
            ) as session:

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
                            logger.warning(f"{url}: {str(ex.message)}")
                        except aiohttp.client_exceptions.ClientConnectorError as ex:
                            logger.warning(f"{str(ex.args[1])} to {url}")
                        except aiohttp.client_exceptions.ClientOSError as ex:
                            logger.warning(f"{url}: {str(ex)}")
                        except aiohttp.client_exceptions.ClientPayloadError as ex:
                            logger.warning(f"{url}: {str(ex)}")
                        except aiohttp.client_exceptions.ClientError as ex:
                            logger.error(f"{url}: {str(ex)}", exc_info=ex)
                        with suppress(asyncio.exceptions.CancelledError):
                            await asyncio.sleep(random.random())
                    return bytes()

                async def post(url: str, data: dict[str, Any], headers: Mapping[str, str] | None = None) -> bytes:
                    async with session.post(url, data=urlencode(data).encode(), headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"Status {response.status} ({response.reason}) while posting to {url}")
                            return b""
                        return await response.read()

                async def get_species() -> list[dict[str, int | str]]:
                    def purge_null_data(entry: dict[str, None | int | str]) -> dict[str, int | str]:
                        return dict(
                            (key, value)
                            for key, value in entry.items()
                            if value is not None and value not in ("", "None")
                        )

                    def trim_strings(entry: dict[str, None | int | str]) -> dict[str, None | int | str]:
                        key: str
                        for key in entry:
                            if isinstance(entry[key], str):
                                entry[key] = cast(str, entry[key]).strip()
                        return entry

                    def ensure_unique_species_tags(entries: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
                        items_to_delete: set[int] = set()
                        for i in range(len(entries) - 1):
                            for j in range(i + 1, len(entries)):
                                if entries[i][SPECIES_TAG] == entries[j][SPECIES_TAG]:
                                    if entries[i][VERSION] < entries[j][VERSION]:
                                        items_to_delete.add(i)
                                    else:
                                        items_to_delete.add(j)
                        if items_to_delete:
                            return [entries[i] for i in range(len(entries)) if i not in items_to_delete]
                        else:
                            return entries

                    species_list: bytes = await post(
                        "https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/",
                        {"database": -1},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    if not species_list:
                        import gzip

                        try:
                            # try using a local copy of the data
                            with gzip.open(Path(__file__).parent / "species.json.gz", "rb") as f_in:
                                species_list = f_in.read()
                        except (OSError, EOFError, Exception):
                            return []

                    data: dict[str, int | str | list[dict[str, None | int | str]]] = json.loads(species_list)
                    return ensure_unique_species_tags(
                        [purge_null_data(trim_strings(s)) for s in data.get("species", [])]
                    )

                async def get_substance_catalog(species_entry: dict[str, int | str]) -> CatalogEntryType:
                    def entry_url(_species_tag: int) -> str:
                        entry_filename: str = f"c{_species_tag:06}.cat"

                        if entry_filename in ("c044009.cat", "c044012.cat"):
                            return ""  # merged with c044004.cat — Brian J. Drouin
                        if _species_tag % 1000 > 500:
                            return "https://cdms.astro.uni-koeln.de/classic/entries/" + entry_filename
                        else:
                            return "https://spec.jpl.nasa.gov/ftp/pub/catalog/" + entry_filename

                    if SPECIES_TAG not in species_entry:
                        # nothing to go on with
                        logger.error(f"{SPECIES_TAG!r} not in the species entry: {species_entry!r}")
                        return dict()

                    if (
                        self._existing_catalog is not None
                        and self._existing_catalog.min_frequency <= min(self._frequency_limits)
                        and self._existing_catalog.max_frequency >= max(self._frequency_limits)
                    ):
                        species_tag: int
                        existing_catalog_entry: CatalogEntryType
                        for species_tag, existing_catalog_entry in self._existing_catalog.catalog.items():
                            if all(
                                existing_catalog_entry.get(key, type(value)()) == value
                                for key, value in species_entry.items()
                            ):
                                logger.debug(f"using existing entry for species tag {species_tag}")
                                _catalog_entry = existing_catalog_entry.copy()
                                _catalog_entry[LINES] = [
                                    _line
                                    for _line in existing_catalog_entry.get(LINES, [])
                                    if within(_line[FREQUENCY], self._frequency_limits)
                                ]
                                return _catalog_entry

                    fn: str = entry_url(cast(int, species_entry[SPECIES_TAG]))
                    if not fn:  # no need to download a file for the species tag
                        logger.debug(f"skipping species tag {species_entry[SPECIES_TAG]}")
                        return dict()
                    try:
                        lines = (await get(fn)).decode().splitlines()
                    except HTTPError as ex:
                        logger.error(fn, exc_info=ex)
                        return dict()
                    catalog_entries = [CatalogEntry(line) for line in lines]
                    if not catalog_entries:
                        if self._run:
                            logger.warning("no entries in the catalog")
                        return dict()
                    return {
                        **species_entry,
                        DEGREES_OF_FREEDOM: catalog_entries[0].degrees_of_freedom,
                        LINES: [
                            _catalog_entry.to_dict()
                            for _catalog_entry in catalog_entries
                            if within(_catalog_entry.frequency, self._frequency_limits)
                        ],
                    }

                species: list[dict[str, int | str]] = await get_species()
                catalog: CatalogType = dict()
                species_count: Final[int] = len(species)
                skipped_count: int = 0
                if self._state_queue is not None:
                    self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))
                self._tasks = [asyncio.create_task(get_substance_catalog(_e)) for _e in species]
                catalog_entry: CatalogEntryType
                future_entry: asyncio.Future[CatalogEntryType]
                for future_entry in asyncio.as_completed(self._tasks):
                    catalog_entry = await future_entry
                    if SPECIES_TAG in catalog_entry:
                        catalog[catalog_entry[SPECIES_TAG]] = catalog_entry
                        if self._state_queue is not None:
                            self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))
                    else:
                        skipped_count += 1
                        if self._state_queue is not None and self._run:
                            self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))

            return catalog

        with suppress(
            RuntimeError, asyncio.exceptions.CancelledError  # it might be “cannot schedule new futures after shutdown”
        ):
            self._catalog = asyncio.run(async_get_catalog())


def get_catalog(
    frequency_limits: tuple[float, float] = (-inf, inf),
    *,
    existing_catalog: Catalog | None = None,
) -> CatalogType:
    """
    Download the spectral lines catalog data

    :param tuple frequency_limits: The frequency range of the catalog entries to keep.
    :param Catalog | None existing_catalog: An existing catalog to base the data on.
        If specified, only the entries not presented in it will be downloaded.
    :return: A list of the spectral lines catalog entries.
    """

    state_queue: Queue[tuple[int, int]] = Queue()
    downloader: Downloader = Downloader(
        frequency_limits=frequency_limits,
        state_queue=state_queue,
        existing_catalog=existing_catalog,
    )
    downloader.start()

    cataloged_species: int
    not_yet_processed_species: int
    while downloader.is_alive():
        try:
            cataloged_species, not_yet_processed_species = state_queue.get(block=True, timeout=0.1)
        except Empty:
            continue
        except KeyboardInterrupt:
            downloader.stop()
        else:
            logger.info(f"got {cataloged_species} entries, {not_yet_processed_species} left")

    while downloader.is_alive():
        try:
            cataloged_species, not_yet_processed_species = state_queue.get(block=True, timeout=0.1)
        except Empty:
            continue
        except KeyboardInterrupt:
            downloader.join(0.1)
        else:
            logger.info(f"got {cataloged_species} entries, {not_yet_processed_species} left")

    while not state_queue.empty():
        try:
            cataloged_species, not_yet_processed_species = state_queue.get()
        except KeyboardInterrupt:
            downloader.join(0.1)
        else:
            logger.info(f"got {cataloged_species} entries, {not_yet_processed_species} left")

    downloader.join()

    return downloader.catalog


def save_catalog(
    filename: str,
    frequency_limits: tuple[float, float] = (0, inf),
    *,
    existing_catalog: Catalog | None = None,
) -> bool:
    """
    Download and save the spectral lines catalog data

    :param str filename: The name of the file to save the downloaded catalog to.
        If it ends with an unknown suffix, `'.json.gz'` is appended to it.
    :param tuple frequency_limits: The tuple of the maximal and the minimal frequencies of the lines being stored.
        All the lines outside the specified frequency range are omitted.
    :param Catalog | None existing_catalog: An existing catalog to base the data on.
        If specified, only the entries not presented in it will be downloaded.
    """

    return save_catalog_to_file(
        filename=filename,
        catalog=get_catalog(frequency_limits, existing_catalog=existing_catalog),
        frequency_limits=frequency_limits,
    )


def download() -> None:
    import argparse
    from datetime import datetime
    from pathlib import Path

    from .catalog import Catalog

    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        allow_abbrev=True,
        description="Download JPL and CDMS spectroscopy catalogs for offline search.\n"
        "Find more at https://github.com/StSav012/pycatsearch.",
    )
    ap.add_argument("catalog", type=Path, help="the catalog location to save into (required)")
    ap.add_argument("-f" "min", "--min-frequency", type=float, help="the lower frequency [MHz] to take", default=-inf)
    ap.add_argument("-f" "max", "--max-frequency", type=float, help="the upper frequency [MHz] to take", default=+inf)
    ap.add_argument("-b", "--base", type=Path, help="an existing catalog to base the data on", default=None)
    args: argparse.Namespace = ap.parse_intermixed_args()

    logging.basicConfig(level=logging.DEBUG)
    logger.info(f"started at {datetime.now()}")
    save_catalog(
        args.catalog,
        (args.min_frequency, args.max_frequency),
        existing_catalog=Catalog(args.base) if args.base is not None else None,
    )
    logger.info(f"finished at {datetime.now()}")
