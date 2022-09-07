# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import urllib.request
from http.client import HTTPResponse
from pathlib import Path
from typing import Final

__all__ = ['update']

logger: logging.Logger = logging.getLogger('updater')


def get_github_date(user: str, repo_name: str, branch: str = 'master') -> str:
    import json

    url: str = f'https://api.github.com/repos/{user}/{repo_name}/commits?sha={branch}&page=1&per_page=1'
    logger.debug(f'Requesting {url}')
    r: HTTPResponse = urllib.request.urlopen(url, timeout=1)
    logger.debug(f'Response code: {r.getcode()}')
    if r.getcode() != 200:
        logger.warning(f'Response code is not OK: {r.getcode()}')
        return ''
    content: bytes = r.read()
    if not content:
        logger.warning(f'No data received from {url}')
        return ''
    d: list[dict[str,
                 str
                 |
                 dict[str,
                      str | int | bool | dict[str,
                                              None | str | bool]]
                 |
                 list[dict[str, str]]]] \
        = json.loads(content)
    if not isinstance(d, list) or not d:
        logger.warning(f'Malformed JSON received: {d}')
        return ''
    d_0: dict[str,
              str
              |
              dict[str,
                   str | int | bool | dict[str,
                                           None | str | bool]]
              |
              list[dict[str, str]]] = d[0]
    commit: dict[str,
                 str | int | dict[str,
                                  None | str | bool]] \
        = d_0.get('commit', dict())
    if not isinstance(commit, dict):
        logger.warning(f'Malformed commit info received: {commit}')
        return ''
    author: dict[str, str] = commit.get('author', dict())
    if not isinstance(author, dict):
        logger.warning(f'Malformed commit author info received: {author}')
        return ''
    return author.get('date', '')


def get_current_version_date(root_path: Path) -> str:
    """ Safely get the UPDATED value from version.py """

    import ast

    if not (root_path / Path('version.py')).exists():
        logger.info('No `version.py` file exists (yet).')
        return ''

    date: str = ''
    text: str = (root_path / Path('version.py')).read_text()
    o: ast.AST
    for o in ast.parse(text, mode='single').body:
        if isinstance(o, ast.AnnAssign) and isinstance(o.target, ast.Name) and isinstance(o.value, ast.Constant):
            if o.target.id == 'UPDATED' and isinstance(o.value.value, str):
                date = o.value.value
                logger.debug(f'Found {o.target.id} = {date}')
    return date


def upgrade_files(code_directory: Path, user: str, repo_name: str, branch: str = 'master') -> None:
    """ Replace the files in `code_directory` with the newer versions acquired from GitHub """

    import io
    import zipfile

    url: str = f'https://github.com/{user}/{repo_name}/archive/{branch}.zip'
    logger.debug(f'Requesting {url}')
    r: HTTPResponse = urllib.request.urlopen(url, timeout=1)
    logger.debug(f'Response code: {r.getcode()}')
    if r.getcode() != 200:
        logger.warning(f'Response code is not OK: {r.getcode()}')
        return
    with zipfile.ZipFile(io.BytesIO(r.read())) as inner_zip:
        root: Path = Path(f'{repo_name}-{branch}/')
        member: zipfile.ZipInfo
        for member in inner_zip.infolist():
            logger.debug(f'Un-zipping {member.filename}')
            if member.is_dir():
                logger.debug('it is a directory')
                continue
            content = inner_zip.read(member)
            (code_directory / Path(member.filename).relative_to(root)).parent.mkdir(parents=True, exist_ok=True)
            (code_directory / Path(member.filename).relative_to(root)).write_bytes(content)
            logger.info(f'{(code_directory / Path(member.filename).relative_to(root))} written')


def update(user: str, repo_name: str, branch: str = 'master') -> None:
    code_directory: Path = Path(__file__).parent

    github_date: Final[str] = get_github_date(user=user, repo_name=repo_name)
    if not github_date:
        logger.warning('Failed to fetch the last commit date from GitHub')
        return
    if get_current_version_date(code_directory) == github_date:
        logger.info('Current files are up to date')
        return

    upgrade_files(code_directory=code_directory, user=user, repo_name=repo_name, branch=branch)

    # and if everything went fine...
    (code_directory / Path('version.py')).write_text(f'UPDATED: str = "{github_date}"\n')
    logger.info(f'{github_date} written into {(code_directory / Path("version.py"))}')
