# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from contextlib import suppress
from pathlib import Path
from typing import Final, Sequence

__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'py''cat''search'

REQUIREMENTS: Final[list[str]] = [('PyQt5.QtCore', 'PySide6.QtCore', 'PyQt6.QtCore', 'PySide2.QtCore'),
                                  'pathvalidate', 'aiohttp']

if __name__ == '__main__':
    def update() -> None:
        """ Download newer files from GitHub and replace the existing ones """
        with suppress(OSError, ModuleNotFoundError):
            import updater

            updater.update(__author__, __original_name__)


    def is_package_importable(package_name: str) -> bool:
        try:
            __import__(package_name, locals=locals(), globals=globals())
        except (ModuleNotFoundError, ):
            return False
        return True


    def ensure_package(package_name: str | Sequence[str], upgrade_pip: bool = False) -> bool:
        """ Install packages if missing """

        if not package_name:
            raise ValueError('No package name given')

        if isinstance(package_name, str) and is_package_importable(package_name):
            return True

        if not isinstance(package_name, str) and isinstance(package_name, Sequence):
            for _package_name in package_name:
                if is_package_importable(_package_name):
                    return True

        import subprocess

        if not isinstance(package_name, str) and isinstance(package_name, Sequence):
            package_name = package_name[0]
        if upgrade_pip:
            subprocess.check_call((sys.executable, '-m', 'pip', 'install', '-U', 'pip'))
        if '.' in package_name:  # take only the root part of the package path
            package_name = package_name.split('.', maxsplit=1)[0]
        subprocess.check_call((sys.executable, '-m', 'pip', 'install', package_name))
        return False

    if not hasattr(sys, '_MEI''PASS') and not Path('.git').exists():
        update()

    if not hasattr(sys, '_MEI''PASS'):  # if not embedded into an executable
        pip_updated: bool = False

        for package in REQUIREMENTS:
            pip_updated = not ensure_package(package, upgrade_pip=not pip_updated)
    try:
        import gui
    except SyntaxError:
        print('Get a newer Python!')
    else:
        gui.run()
