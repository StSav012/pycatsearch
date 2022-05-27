# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from typing import Final


__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'py''cat''search'

REQUIREMENTS: Final[list[str]] = ['PyQt5', 'pathvalidate', 'aiohttp']

if __name__ == '__main__':
    if not hasattr(sys, '_MEI''PASS') and not Path('.git').exists():
        try:
            import updater

            updater.update(__author__, __original_name__)
        except (OSError, ModuleNotFoundError):
            pass

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
                        raise ex
                    pip_updated = True
                if subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]):
                    tb = sys.exc_info()[2]
                    print(ex.with_traceback(tb))
    try:
        import gui
    except ImportError as ex:
        tb = sys.exc_info()[2]
        print(ex.with_traceback(tb))
        if 'qt' in str(ex.with_traceback(tb)).casefold():
            print('Ensure that PyQt5-sip and PyQt5 are installed')
    except SyntaxError:
        print('Get a newer Python!')
    else:
        gui.run()
