#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import platform
import sys
from contextlib import suppress
from pathlib import Path
from typing import Final, Sequence

from catalog import Catalog

__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'py''cat''search'


def _version_tuple(version_string: str) -> tuple[int | str, ...]:
    result: tuple[int | str, ...] = tuple()
    part: str
    for part in version_string.split('.'):
        try:
            result += (int(part),)
        except ValueError:
            result += (part,)
    return result


qt_list: Sequence[str]
uname: platform.uname_result = platform.uname()
if ((uname.system == 'Windows'
     and _version_tuple(uname.version) < _version_tuple('10.0.19044'))  # Windows 10 21H2 or later required
        or uname.machine not in ('x86_64', 'AMD64')):
    qt_list = ('PyQt5',)  # Qt6 does not support the OSes
else:
    qt_list = ('PyQt6', 'PySide6', 'PyQt5')
if sys.version_info < (3, 11):  # PySide2 does not support Python 3.11 and newer
    qt_list = *qt_list, 'PySide2'

REQUIREMENTS: Final[list[str | Sequence[str]]] = ['qtpy',
                                                  [qt + '.QtCore' for qt in qt_list]]

if __name__ == '__main__':
    def update() -> None:
        """ Download newer files from GitHub and replace the existing ones """
        with suppress(BaseException):  # ignore really all exceptions, for there are dozens of the sources
            import updater

            updater.update(__author__, __original_name__)


    def is_package_importable(package_name: str) -> bool:
        try:
            __import__(package_name, locals=locals(), globals=globals())
        except (ModuleNotFoundError,):
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


    update_by_default: bool = (uname.system == 'Windows'
                               and not hasattr(sys, '_MEI''PASS')
                               and not Path('.git').exists())
    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n'
                    'Find more at https://github.com/StSav012/pycatsearch.')
    ap.add_argument('catalog', type=str, help='the catalog location to load (required)',
                    nargs=argparse.ZERO_OR_MORE)
    ap_group = ap.add_argument_group(title='Search options',
                                     description='If any of the following arguments specified, a search conducted.')
    ap_group.add_argument('-f''min', '--min-frequency', type=float, help='the lower frequency [MHz] to take')
    ap_group.add_argument('-f''max', '--max-frequency', type=float, help='the upper frequency [MHz] to take')
    ap_group.add_argument('-i''min', '--min-intensity', type=float, help='the minimal intensity [log10(nm²×MHz)] to take')
    ap_group.add_argument('-i''max', '--max-intensity', type=float, help='the maximal intensity [log10(nm²×MHz)] to take')
    ap_group.add_argument('-T', '--temperature', type=float,
                          help='the temperature [K] to calculate the line intensity at, use the catalog intensity if not set')
    ap_group.add_argument('-t', '--tag', '--species-tag', type=int, dest='species_tag',
                          help='a number to match the `species''tag` field')
    ap_group.add_argument('-n', '--any-name-or-formula', type=str,
                          help='a string to match any field used by `any_name` and `any_formula` options')
    ap_group.add_argument('--any-name', type=str, help='a string to match the `trivial''name` or the `name` field')
    ap_group.add_argument('--any-formula', type=str,
                          help='a string to match the `structural''formula`, `molecule''symbol`, '
                               '`stoichiometric''formula`, or `isotopolog` field')
    ap_group.add_argument('--InChI', '--inchi', '--inchi-key', type=str, dest='inchi',
                          help='a string to match the `inchikey` field, '
                               'which contains the IUPAC International Chemical Identifier (InChI™)')
    ap_group.add_argument('--trivial-name', type=str, help='a string to match the `trivial''name` field')
    ap_group.add_argument('--structural-formula', type=str, help='a string to match the `structural''formula` field')
    ap_group.add_argument('--name', type=str, help='a string to match the `name` field')
    ap_group.add_argument('--stoichiometric-formula', type=str,
                          help='a string to match the `stoichiometric''formula` field')
    ap_group.add_argument('--isotopolog', type=str, help='a string to match the `isotopolog` field')
    ap_group.add_argument('--state', type=str, help='a string to match the `state` or `state_html` field')
    ap_group.add_argument('--dof', '--degrees_of_freedom', type=int, dest='degrees_of_freedom',
                          help='0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules')
    ap_group.add_argument('--timeout', type=float, help='maximum time span for the filtering to take')
    if not hasattr(sys, '_MEI''PASS'):  # if not embedded into an executable
        ap_group = ap.add_argument_group(title='Service options')
        if not update_by_default:
            ap_group.add_argument('-U', '--update', '--upgrade',
                                  action='store_true', dest='update',
                                  help='update the code from the repo before executing the main code')
        else:
            ap_group.add_argument('--no-update', '--no-upgrade',
                                  action='store_false', dest='update',
                                  help='don\'t update the code from the GitHub repo before executing the main code')
        ap_group.add_argument('-r', '--ensure-requirements',
                              action='store_true',
                              help='install the required packages using `pip` (might fail)')

    args: argparse.Namespace = ap.parse_intermixed_args()
    if not hasattr(sys, '_MEI''PASS'):  # if not embedded into an executable
        if args.update:
            update()
        if args.ensure_requirements:
            pip_updated: bool = False
            for package in REQUIREMENTS:
                pip_updated = not ensure_package(package, upgrade_pip=not pip_updated)

    arg_names: Sequence[str] = ['min_frequency', 'max_frequency', 'min_intensity', 'max_intensity',
                                'temperature', 'species_tag', 'any_name_or_formula', 'any_name', 'any_formula',
                                'inchi', 'trivial_name', 'structural_formula', 'name', 'stoichiometric_formula',
                                'isotopolog', 'state', 'degrees_of_freedom', 'timeout']
    search_args: dict[str, str | float | int] = dict((arg, getattr(args, arg)) for arg in arg_names
                                                     if getattr(args, arg) is not None)
    if search_args:
        c: Catalog = Catalog(*args.catalog)
        c.print(**search_args)
        exit(0)

    try:
        import gui
    except Exception as ex:
        import tkinter.messagebox
        import traceback

        traceback.print_exception(ex)
        if isinstance(ex, SyntaxError):
            tkinter.messagebox.showerror(title='Syntax Error',
                                         message=('Python ' + platform.python_version() + ' is not supported.\n' +
                                                  'Get a newer Python!'))
        elif isinstance(ex, ImportError):
            tkinter.messagebox.showerror(title='Package Missing',
                                         message=('Module ' + repr(ex.name) +
                                                  ' is either missing from the system ' +
                                                  'or cannot be loaded for another reason.\n' +
                                                  'Try to install or reinstall it.'))
        else:
            tkinter.messagebox.showerror(title='Error', message=str(ex))
    else:
        gui.run()
