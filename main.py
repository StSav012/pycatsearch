# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from typing import Type

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()

__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'pycatsearch'

if __name__ == '__main__':
    if not hasattr(sys, '_MEIPASS') and not Path('.git').exists():
        try:
            import updater

            updater.update(__author__, __original_name__)
        except (OSError, ModuleNotFoundError):
            pass
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
