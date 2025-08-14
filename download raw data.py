import json
import locale
import logging
import random
import time
from contextlib import suppress
from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from io import BytesIO
from os import PathLike
from pathlib import Path
from queue import Empty, Queue
from tarfile import TarFile, TarInfo
from threading import Event, Thread
from typing import Any, Final, Mapping, cast
from urllib.error import HTTPError
from urllib.parse import ParseResult, urlencode, urlparse

from pycatsearch.utils import BUILD_TIME, SPECIES_TAG, VERSION

__all__ = ["Downloader", "get_catalog", "save_catalog", "download"]

logger: logging.Logger = logging.getLogger("downloader")


def now_to_string() -> str:
    loc: tuple[str | None, str | None] = locale.getlocale(category=locale.LC_TIME)
    locale.setlocale(category=locale.LC_TIME, locale="C")
    s: str = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")
    locale.setlocale(category=locale.LC_TIME, locale=loc)
    return s


def string_to_time(s: str) -> datetime:
    loc: tuple[str | None, str | None] = locale.getlocale(category=locale.LC_TIME)
    locale.setlocale(category=locale.LC_TIME, locale="C")
    t: datetime = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
    locale.setlocale(category=locale.LC_TIME, locale=loc)
    return t


class Downloader(Thread):
    def __init__(
        self,
        tar_file: TarFile,
        *,
        state_queue: Queue[tuple[int, int]] | None = None,
    ) -> None:
        super().__init__()
        self._tar_file: TarFile = tar_file
        self._state_queue: Queue[tuple[int, int]] | None = state_queue
        self._clear_to_run: Event = Event()
        self._sessions: dict[tuple[str, str], HTTPConnection | HTTPSConnection] = dict()

    def __del__(self) -> None:
        self.stop()
        session: HTTPConnection | HTTPSConnection
        for session in self._sessions.values():
            session.close()

    def stop(self) -> None:
        self._clear_to_run.clear()

    def join(self, timeout: float | None = None) -> None:
        self.stop()
        session: HTTPConnection | HTTPSConnection
        for session in self._sessions.values():
            session.close()
        super().join(timeout=timeout)

    def run(self) -> None:
        self._clear_to_run.set()

        def session_for_url(scheme: str, location: str) -> HTTPConnection | HTTPSConnection:
            if (scheme, location) not in self._sessions:
                if scheme == "http":
                    self._sessions[(scheme, location)] = HTTPConnection(location)
                elif scheme == "https":
                    self._sessions[(scheme, location)] = HTTPSConnection(location)
                else:
                    raise ValueError(f"Unknown scheme: {scheme}")
            return self._sessions[(scheme, location)]

        def get(url: str, headers: Mapping[str, str] | None = None) -> tuple[bytes, datetime]:
            parse_result: ParseResult = urlparse(url)
            session: HTTPConnection | HTTPSConnection = session_for_url(parse_result.scheme, parse_result.netloc)
            response: HTTPResponse
            while self._clear_to_run.is_set():
                try:
                    session.request(method=HTTPMethod.GET, url=parse_result.path, headers=(headers or dict()))
                    response = session.getresponse()
                except ConnectionResetError as ex:
                    logger.warning(ex)
                    time.sleep(random.random())
                else:
                    if response.closed:
                        break
                    with suppress(AttributeError):  # `response.fp` became `None` before the socket began closing
                        return response.read(), string_to_time(response.getheader("Last-Modified", now_to_string()))
            return b"", datetime.now(tz=timezone.utc)

        def post(url: str, data: dict[str, Any], headers: Mapping[str, str] | None = None) -> tuple[bytes, datetime]:
            parse_result: ParseResult = urlparse(url)
            session: HTTPConnection | HTTPSConnection = session_for_url(parse_result.scheme, parse_result.netloc)
            response: HTTPResponse
            while self._clear_to_run.is_set():
                try:
                    session.request(
                        method=HTTPMethod.POST,
                        url=parse_result.path,
                        body=urlencode(data),
                        headers=(headers or dict()),
                    )
                    response = session.getresponse()
                except ConnectionResetError as ex:
                    logger.warning(ex)
                    time.sleep(random.random())
                else:
                    if response.closed:
                        logger.error(f"Stream closed before read the response from {url}")
                        break
                    if response.status != HTTPStatus.OK:
                        logger.error(f"Status {response.status} ({response.reason}) while posting to {url}")
                        return b"", string_to_time(
                            response.getheader("Date", now_to_string()),
                        )
                    try:
                        return response.read(), string_to_time(
                            response.getheader("Date", now_to_string()),
                        )
                    except AttributeError:
                        logger.warning("`response.fp` became `None` before the socket began closing")
                        break
            return b"", datetime.fromtimestamp(0, tz=timezone.utc)

        def get_species() -> list[dict[str, int | str]]:
            def purge_null_data(entry: dict[str, None | int | str]) -> dict[str, int | str]:
                return dict((key, value) for key, value in entry.items() if value not in (None, "", "None"))

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

            species_list_data: bytes
            ts: datetime
            species_list_data, ts = post(
                "https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/",
                {"database": -1},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if not species_list_data:
                import gzip

                try:
                    # try using a local copy of the data
                    with gzip.open(Path(__file__).parent / "species.json.gz", "rb") as f_in:
                        species_list_data = f_in.read()
                except (OSError, EOFError, Exception):
                    return []

            ti: TarInfo = TarInfo(name="species.json")
            ti.size = len(species_list_data)
            ti.mtime = ts.timestamp()
            self._tar_file.addfile(tarinfo=ti, fileobj=BytesIO(species_list_data))

            ti = TarInfo(name="metadata.json")
            metadata: bytes = json.dumps(
                {
                    "credit": {
                        "copyright": "I. Physikalisches Institut der Universität zu Köln",
                        "url": "https://cdms.astro.uni-koeln.de/",
                        "references": [
                            "https://doi.org/10.1016/j.jms.2016.03.005",
                            "https://doi.org/10.1016/j.molstruc.2005.01.027",
                            "https://doi.org/10.1051/0004-6361:20010367",
                        ],
                    },
                    BUILD_TIME: ts.isoformat(),
                },
                ensure_ascii=False,
                indent=4,
            ).encode(encoding="utf-8")
            ti.size = len(metadata)
            ti.mtime = ts.timestamp()
            self._tar_file.addfile(tarinfo=ti, fileobj=BytesIO(metadata))

            data: dict[str, int | str | list[dict[str, None | int | str]]] = json.loads(species_list_data)
            return ensure_unique_species_tags([purge_null_data(trim_strings(s)) for s in data.get("species", [])])

        def get_substance_catalog(species_entry: dict[str, int | str]) -> tuple[bytes, datetime]:
            if not self._clear_to_run.is_set():
                return b"", datetime.now(tz=timezone.utc)  # quickly exit the function

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
                return b"", datetime.now(tz=timezone.utc)

            fn: str = entry_url(cast(int, species_entry[SPECIES_TAG]))
            if not fn:  # no need to download a file for the species tag
                logger.debug(f"skipping species tag {species_entry[SPECIES_TAG]}")
                return b"", datetime.now(tz=timezone.utc)
            try:
                logger.debug(f"getting {fn}")
                return get(fn)
            except HTTPError as ex:
                logger.error(fn, exc_info=ex)
                return b"", datetime.now(tz=timezone.utc)

        species: list[dict[str, int | str]] = get_species()
        species_count: Final[int] = len(species)
        added_count: int = 0
        skipped_count: int = 0
        if self._state_queue is not None:
            self._state_queue.put((added_count, species_count - added_count - skipped_count))
        catalog_entry: bytes
        timestamp: datetime
        _e: dict[str, int | str]
        for _e in species:
            catalog_entry, timestamp = get_substance_catalog(_e)
            if catalog_entry:
                tar_info = TarInfo(name=f"c{_e[SPECIES_TAG]:06d}.cat")
                tar_info.size = len(catalog_entry)
                tar_info.mtime = timestamp.timestamp()
                self._tar_file.addfile(tarinfo=tar_info, fileobj=BytesIO(catalog_entry))
                added_count += 1
                if self._state_queue is not None:
                    self._state_queue.put((added_count, species_count - added_count - skipped_count))
            else:
                skipped_count += 1
                if self._state_queue is not None and self._clear_to_run.is_set():
                    self._state_queue.put((added_count, species_count - added_count - skipped_count))


def get_catalog(tar_file: TarFile) -> None:
    """
    Download the spectral lines catalog data

    :param TarFile tar_file: The file to save the catalog data to.
    """

    state_queue: Queue[tuple[int, int]] = Queue()
    downloader: Downloader = Downloader(tar_file=tar_file, state_queue=state_queue)
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


def save_catalog(filename: str | PathLike[str]) -> None:
    """
    Download and save the spectral lines catalog data

    :param str | PathLike[str] filename: The name of the file to save the downloaded catalog to.
        If it ends with an unknown suffix, `'.tar'` is appended to it.
    """

    if not isinstance(filename, Path):
        filename = Path(filename)

    for ext, mode in {
        ".tar": "w|",
        (".tar.gz", ".tgz"): "w|gz",
        (".tar.bz2", ".tbz2"): "w|bz2",
        (".tar.xz", ".txz"): "w|xz",
    }.items():
        if filename.name.casefold().endswith(ext):
            with TarFile.open(name=str(filename), mode=mode) as t:
                return get_catalog(t)
    raise ValueError("Unknown mode")


def download() -> None:
    import argparse
    from datetime import datetime
    from pathlib import Path

    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        allow_abbrev=True,
        description="Download JPL and CDMS spectroscopy catalogs for offline search.\n"
        "Find more at https://github.com/StSav012/pycatsearch.",
    )
    ap.add_argument("catalog", type=Path, help="the catalog location to save into (required)")
    args: argparse.Namespace = ap.parse_intermixed_args()

    logging.basicConfig(level=logging.DEBUG)
    logger.info(f"started at {datetime.now()}")
    save_catalog(args.catalog)
    logger.info(f"finished at {datetime.now()}")


if __name__ == "__main__":
    download()
