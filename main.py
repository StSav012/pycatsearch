# -*- coding: utf-8 -*-
try:
    import gui
except ImportError as ex:
    import sys

    tb = sys.exc_info()[2]
    print(ex.with_traceback(tb))
    print('Ensure that PyQt5-sip and PyQt5 are installed')
except SyntaxError:
    print('Get a newer Python!')
else:
    if __name__ == '__main__':
        gui.run()
