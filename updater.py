# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from contextlib import suppress
from http.client import HTTPResponse
from pathlib import Path
from typing import BinaryIO, Final, TextIO, cast

__all__ = ['update']


def update(user: str, repo_name: str, branch: str = 'master') -> None:
    extraction_root: Path = Path.cwd()

    url: str
    r: HTTPResponse
    url = f'https://api.github.com/repos/{user}/{repo_name}/commits?page=1&per_page=1'
    r = urllib.request.urlopen(url, timeout=1)
    if r.getcode() != 200:
        return
    content: bytes = r.read()
    if not content:
        return
    d: list[dict[str,
                 str | dict[str,
                            str | int | bool | dict[str,
                                                    None | str | bool]],
                 list[dict[str, str]]]] \
        = json.loads(content)
    if not isinstance(d, list) or not d:
        return
    date: Final[str] = cast(str, d[0].get('commit', dict()).get('author', dict()).get('date', ''))
    if (extraction_root / Path('version.py')).exists():
        with suppress(OSError, ImportError, ModuleNotFoundError):
            import version

            if version.UPDATED == f'{date}':
                return
    (extraction_root / Path('version.py')).write_text(f'UPDATED: str = "{date}"\n')

    url = f'https://github.com/{user}/{repo_name}/archive/{branch}.zip'
    r = urllib.request.urlopen(url, timeout=1)
    if r.getcode() != 200:
        return
    with zipfile.ZipFile(io.BytesIO(r.read())) as inner_zip:
        root: Path = Path(f'{repo_name}-{branch}/')
        member: zipfile.ZipInfo
        for member in inner_zip.infolist():
            if member.is_dir():
                continue
            content = inner_zip.read(member)
            (extraction_root / Path(member.filename).relative_to(root)).parent.mkdir(parents=True, exist_ok=True)
            (extraction_root / Path(member.filename).relative_to(root)).write_bytes(content)
