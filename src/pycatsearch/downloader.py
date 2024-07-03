# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import random
import time
from http import HTTPMethod, HTTPStatus
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from math import inf
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any, Final, Mapping, cast
from urllib.error import HTTPError
from urllib.parse import ParseResult, urlencode, urlparse

try:
    import orjson as json
except ImportError:
    import json

from .catalog import Catalog, CatalogEntryType, CatalogType
from .catalog_entry import CatalogEntry
from .utils import FREQUENCY, LINES, SPECIES_TAG, DEGREES_OF_FREEDOM, VERSION, within, save_catalog_to_file

__all__ = ["Downloader", "get_catalog", "save_catalog", "download"]

logger: logging.Logger = logging.getLogger("downloader")


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
        self._sessions: dict[tuple[str, str], HTTPConnection | HTTPSConnection] = dict()

    def __del__(self) -> None:
        self.stop()
        session: HTTPConnection | HTTPSConnection
        for session in self._sessions.values():
            session.close()

    @property
    def catalog(self) -> CatalogType:
        return self._catalog.copy()

    def stop(self) -> None:
        self._run = False

    def join(self, timeout: float | None = None) -> None:
        self.stop()
        session: HTTPConnection | HTTPSConnection
        for session in self._sessions.values():
            session.close()
        super().join(timeout=timeout)

    def run(self) -> None:
        self._run = True

        def session_for_url(scheme: str, location: str) -> HTTPConnection | HTTPSConnection:
            if (scheme, location) not in self._sessions:
                if scheme == "http":
                    self._sessions[(scheme, location)] = HTTPConnection(location)
                elif scheme == "https":
                    self._sessions[(scheme, location)] = HTTPSConnection(location)
                else:
                    raise ValueError(f"Unknown scheme: {scheme}")
            return self._sessions[(scheme, location)]

        def get(url: str, headers: Mapping[str, str] | None = None) -> str:
            parse_result: ParseResult = urlparse(url)
            session: HTTPConnection | HTTPSConnection = session_for_url(parse_result.scheme, parse_result.netloc)
            response: HTTPResponse
            while True:
                try:
                    session.request(method=HTTPMethod.GET, url=parse_result.path, headers=(headers or dict()))
                    response = session.getresponse()
                except ConnectionResetError:
                    time.sleep(random.random())
                else:
                    break
            if response.closed:
                return ""
            try:
                return response.read().decode()
            except AttributeError:  # `response.fp` became `None` before the socket began closing
                return ""

        def post(url: str, data: dict[str, Any], headers: Mapping[str, str] | None = None) -> bytes:
            parse_result: ParseResult = urlparse(url)
            session: HTTPConnection | HTTPSConnection = session_for_url(parse_result.scheme, parse_result.netloc)
            response: HTTPResponse
            while True:
                try:
                    session.request(
                        method=HTTPMethod.POST,
                        url=parse_result.path,
                        body=urlencode(data),
                        headers=(headers or dict()),
                    )
                    response = session.getresponse()
                except ConnectionResetError:
                    time.sleep(random.random())
                else:
                    break
            if response.closed:
                logger.error(f"Stream closed before read the response from {url}")
                return b""
            if response.status != HTTPStatus.OK:
                logger.error(f"Status {response.status} ({response.reason}) while posting to {url}")
                return b""
            try:
                return response.read()
            except AttributeError:
                logger.warning("`response.fp` became `None` before the socket began closing")
                return b""

        def get_species() -> list[dict[str, int | str]]:
            def purge_null_data(entry: dict[str, None | int | str]) -> dict[str, int | str]:
                return dict(
                    (key, value) for key, value in entry.items() if value is not None and value not in ("", "None")
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

            species_list: bytes = b""
            if not species_list:
                import gzip

                try:
                    # try using a local copy of the data
                    with gzip.open(Path(__file__).parent / "species.json.gz", "rb") as f_in:
                        species_list = f_in.read()
                except (OSError, EOFError, Exception):
                    return []

            data: dict[str, int | str | list[dict[str, None | int | str]]] = json.loads(species_list)
            return ensure_unique_species_tags([purge_null_data(trim_strings(s)) for s in data.get("species", [])])

        def get_substance_catalog(species_entry: dict[str, int | str]) -> CatalogEntryType:
            if not self._run:
                return dict()  # quickly exit the function

            def entry_url(_species_tag: int) -> str:
                entry_filename: str = f"c{_species_tag:06}.cat"
                if entry_filename in ("c044009.cat", "c044012.cat"):  # merged with c044004.cat — Brian J. Drouin
                    return ""
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
                        existing_catalog_entry.get(key, type(value)()) == value for key, value in species_entry.items()
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
                logger.debug(f"getting {fn}")
                lines = get(fn).splitlines()
            except HTTPError as ex:
                logger.error(fn, exc_info=ex)
                return dict()
            catalog_entries = [CatalogEntry(line) for line in lines]
            if not catalog_entries:
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

        species: list[dict[str, int | str]] = get_species()
        catalog: CatalogType = dict()
        species_count: Final[int] = len(species)
        skipped_count: int = 0
        if self._state_queue is not None:
            self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))
        catalog_entry: CatalogEntryType
        _e: dict[str, int | str]
        for _e in species:
            catalog_entry = get_substance_catalog(_e)
            if SPECIES_TAG in catalog_entry:
                catalog[catalog_entry[SPECIES_TAG]] = catalog_entry
                if self._state_queue is not None:
                    self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))
            else:
                skipped_count += 1
                if self._state_queue is not None and self._run:
                    self._state_queue.put((len(catalog), species_count - len(catalog) - skipped_count))

        self._catalog = catalog


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
        frequency_limits=frequency_limits, state_queue=state_queue, existing_catalog=existing_catalog
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
