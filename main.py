#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    message = ('The Python version ' + '.'.join(map(str, sys.version_info[:3])) + ' is not supported.\n' +
               'Use Python 3.8 or newer.')
    try:
        import tkinter
    except ImportError:
        input(message)  # wait for the user to see the text
    else:
        print(message, file=sys.stderr)

        import tkinter.messagebox

        _root = tkinter.Tk()
        _root.withdraw()
        tkinter.messagebox.showerror(title='Outdated Python', message=message)
        _root.destroy()

    exit(1)


if __name__ == '__main__':
    try:
        from pycatsearch import main
    except ImportError:
        from src.pycatsearch import main
    main()
