# -*- coding: utf-8 -*-
import sys

try:
    import gui
except ImportError as ex:
    tb = sys.exc_info()[2]
    print(ex.with_traceback(tb))
    print('Ensure that PyQt5-sip and PyQt5 are installed')
except SyntaxError:
    print('Get a newer Python!')
else:
    if __name__ == '__main__':
        import subprocess

        child = subprocess.Popen([sys.executable, '-c',
                                  'from PyQt5.QtWidgets import QApplication; QApplication([])'],
                                 stderr=subprocess.PIPE)
        child.wait()
        ret_code = child.returncode
        if ret_code == 0:
            gui.run()
        else:
            print('This platform is not supported by Qt5')
