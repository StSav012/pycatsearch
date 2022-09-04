# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from contextlib import suppress
from pathlib import Path
from typing import Final


__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'py''cat''search'

REQUIREMENTS: Final[list[str]] = ['PyQt5', 'pathvalidate', 'aiohttp']

if __name__ == '__main__':
    if not hasattr(sys, '_MEI''PASS') and not Path('.git').exists():
        with suppress(OSError, ModuleNotFoundError):
            import updater

            updater.update(__author__, __original_name__)

    if not hasattr(sys, '_MEI''PASS'):  # if not embedded into an executable
        import importlib

        pip_updated: bool = False

        for package in REQUIREMENTS:
            try:
                importlib.import_module(package)
            except (ImportError, ModuleNotFoundError) as ex:
                import subprocess

                if not pip_updated:
                    if subprocess.check_call((sys.executable, '-m', 'pip', 'install', '-U', 'pip')):
                        raise
                    pip_updated = True
                if subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]):
                    tb = sys.exc_info()[2]
                    print(ex.with_traceback(tb), file=sys.stderr)
    try:
        import gui
    except ImportError as ex:
        tb = sys.exc_info()[2]
        print(ex.with_traceback(tb), file=sys.stderr)
        if 'qt' in str(ex.with_traceback(tb)).casefold():
            print('Ensure that PyQt5-sip and PyQt5 are installed')
    except SyntaxError:
        print('Get a newer Python!')
    else:
        gui.run()
