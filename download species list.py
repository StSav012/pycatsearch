# coding=utf-8
"""
Download the species list and save it to ./species.json 
and to ./src/pycatsearch/species.json.gz if the ./src/pycatsearch/ path exists.

Backup the existing files.

The JSON is prepended with the copyright notice and appended with the timestamp it was received at.

The code will crash unless the operations are permitted.
"""

from __future__ import annotations

import gzip
import json
import logging
import random
import time
from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import ParseResult, urlencode, urlparse

from pycatsearch.utils import SPECIES_TAG

logger: logging.Logger = logging.getLogger(__file__)


def session_for_url(scheme: str, location: str) -> HTTPConnection | HTTPSConnection:
    if scheme == "http":
        return HTTPConnection(location)
    elif scheme == "https":
        return HTTPSConnection(location)
    else:
        raise ValueError(f"Unknown scheme: {scheme}")


def post(url: str, data: dict[str, Any], headers: Mapping[str, str] | None = None) -> tuple[bytes, str]:
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
        return b"", ""
    if response.status != HTTPStatus.OK:
        logger.error(f"Status {response.status} ({response.reason}) while posting to {url}")
        return b"", response.getheader("Date", datetime.now(tz=timezone.utc).isoformat())
    try:
        return response.read(), response.getheader("Date", datetime.now(tz=timezone.utc).isoformat())
    except AttributeError:
        logger.warning("`response.fp` became `None` before the socket began closing")
        return b"", ""


def main() -> None:
    species_list_data: bytes
    timestamp: str
    species_list_data, timestamp = post(
        "https://cdms.astro.uni-koeln.de/cdms/portal/json_list/species/",
        {"database": -1},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not species_list_data:
        print("got no data, exiting")
        return

    data: dict[str, int | str | list[dict[str, None | int | str]]] = json.loads(species_list_data)

    data = {
        "credit": {
            "copyright": "I. Physikalisches Institut der Universität zu Köln",
            "url": "https://cdms.astro.uni-koeln.de/",
            "references": [
                "https://doi.org/10.1016/j.jms.2016.03.005",
                "https://doi.org/10.1016/j.molstruc.2005.01.027",
                "https://doi.org/10.1051/0004-6361:20010367",
            ],
        },
        **data,
        "timestamp": timestamp,
    }

    file: Path = Path("species.json")

    prev_data: dict[str, int | str | list[dict[str, None | int | str]]] = {}
    if file.exists():
        prev_data = json.loads(file.read_text(encoding="utf-8"))
        file.rename(file.with_stem("~" + file.stem))
    species_list_text: str = json.dumps(data, indent=2)
    file.write_text(species_list_text, encoding="utf-8")

    print("saved", len(data.get("species", 0)), "species")
    if prev_data:
        current_tags: set[int] = {s[SPECIES_TAG] for s in data.get("species")}
        prev_tags: set[int] = {s[SPECIES_TAG] for s in prev_data.get("species")}
        print("removed tags:", prev_tags - current_tags)
        print("new tags:", current_tags - prev_tags)

    gzip_file: Path = Path("src") / "pycatsearch" / "species.json.gz"
    if gzip_file.exists():
        gzip_file.rename(gzip_file.with_stem("~" + gzip_file.stem))

    if gzip_file.parent.exists():
        # do not save the archive if the directory tree is missing
        with gzip.open(gzip_file, "wt", encoding="utf-8") as f_out:
            f_out.write(species_list_text)
    else:
        print("skipping", gzip_file)


if __name__ == "__main__":
    main()
