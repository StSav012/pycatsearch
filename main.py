#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Final

__author__: Final[str] = 'StSav012'
__original_name__: Final[str] = 'py''cat''search'

del Final

if __name__ == '__main__':
    import argparse
    import platform
    import sys
    from contextlib import suppress
    from datetime import datetime, timedelta, timezone
    from pathlib import Path
    from typing import Final, NamedTuple, Sequence

    from catalog import Catalog


    def _version_tuple(version_string: str) -> tuple[int | str, ...]:
        result: tuple[int | str, ...] = tuple()
        part: str
        for part in version_string.split('.'):
            try:
                result += (int(part),)
            except ValueError:
                result += (part,)
        return result


    class PackageRequirement(NamedTuple):
        package_name: str
        import_name: str
        min_version: str = ''

        def __str__(self) -> str:
            if self.min_version:
                return self.package_name + '>=' + self.min_version
            return self.package_name


    def update() -> None:
        """ Download newer files from GitHub and replace the existing ones """
        with suppress(BaseException):  # ignore really all exceptions, for there are dozens of the sources
            import updater

            updater.update(__author__, __original_name__)


    def is_package_importable(package_requirement: PackageRequirement) -> bool:
        from importlib import import_module
        from importlib.metadata import version

        try:
            import_module(package_requirement.import_name)
        except (ModuleNotFoundError,):
            return False
        else:
            if (package_requirement.min_version
                    and (_version_tuple(version(package_requirement.package_name))
                         < _version_tuple(package_requirement.min_version))):
                return False
        return True


    def ensure_package(package_requirement: PackageRequirement | Sequence[PackageRequirement],
                       upgrade_pip: bool = False) -> bool:
        """
        Install packages if missing

        :param package_requirement: a package name or a sequence of the names of alternative packages;
                             if none of the packages installed beforehand, install the first one given
        :param upgrade_pip: upgrade `pip` before installing the package (if necessary)
        :returns bool: True if a package is importable, False when an attempt to install the package made
        """

        if not package_requirement:
            raise ValueError('No package requirements given')

        if not sys.executable:
            return False  # nothing to do

        if isinstance(package_requirement, PackageRequirement) and is_package_importable(package_requirement):
            return True

        if not isinstance(package_requirement, PackageRequirement) and isinstance(package_requirement, Sequence):
            for _package_requirement in package_requirement:
                if is_package_importable(_package_requirement):
                    return True

        import subprocess

        if isinstance(package_requirement, Sequence):
            package_requirement = package_requirement[0]
        if upgrade_pip:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', str(package_requirement)])
        return False


    def warn_about_outdated_package(package_name: str, package_version: str, release_time: datetime) -> None:
        """ Display a warning about an outdated package a year after the package released """
        if datetime.utcnow().replace(tzinfo=timezone(timedelta())) - release_time > timedelta(days=366):
            import tkinter.messagebox
            tkinter.messagebox.showwarning(
                title='Package Outdated',
                message=f'Please update {package_name} package to {package_version} or newer')


    def make_old_qt_compatible_again() -> None:
        from qtpy import QT6, PYSIDE2
        from qtpy.QtCore import QLibraryInfo, Qt
        from qtpy.QtWidgets import QApplication, QDialog

        if PYSIDE2:
            QApplication.exec = QApplication.exec_
            QDialog.exec = QDialog.exec_

        if not QT6:
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        from qtpy import __version__

        if _version_tuple(__version__) < _version_tuple('2.3.1'):
            warn_about_outdated_package(package_name='QtPy', package_version='2.3.1',
                                        release_time=datetime.fromisoformat('2023-03-28T23:06:05Z'))
            if QT6:
                QLibraryInfo.LibraryLocation = QLibraryInfo.LibraryPath
        if _version_tuple(__version__) < _version_tuple('2.4.0'):
            # 2.4.0 is not released yet, so no warning until there is the release time
            if not QT6:
                QLibraryInfo.path = lambda *args, **kwargs: QLibraryInfo.location(*args, **kwargs)
                QLibraryInfo.LibraryPath = QLibraryInfo.LibraryLocation


    def main() -> None:
        qt_list: list[PackageRequirement]
        uname: platform.uname_result = platform.uname()
        if ((uname.system == 'Windows'
             and _version_tuple(uname.version) < _version_tuple('10.0.19044'))  # Windows 10 21H2 or later required
                or uname.machine not in ('x86_64', 'AMD64')):
            # Qt6 does not support the OSes
            qt_list = [PackageRequirement(package_name='PyQt5', import_name='PyQt5.QtCore')]
        else:
            qt_list = [
                PackageRequirement(package_name='PySide6-Essentials', import_name='PySide6.QtCore'),
                PackageRequirement(package_name='PyQt6', import_name='PyQt6.QtCore'),
                PackageRequirement(package_name='PyQt5', import_name='PyQt5.QtCore'),
            ]
        if sys.version_info < (3, 11):  # PySide2 from pypi is not available for Python 3.11 and newer
            qt_list.append(PackageRequirement(package_name='PySide2', import_name='PySide2.QtCore'))

        requirements: Final[list[PackageRequirement | Sequence[PackageRequirement]]] = [
            PackageRequirement(package_name='qtpy', import_name='qtpy', min_version='2.3.1'),
            qt_list,
        ]

        update_by_default: bool = (uname.system == 'Windows'
                                   and not hasattr(sys, '_MEI''PASS')
                                   and not Path('.git').exists())
        ap: argparse.ArgumentParser = argparse.ArgumentParser(
            allow_abbrev=True,
            description='Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n'
                        f'Find more at https://github.com/{__author__}/{__original_name__}.')
        ap.add_argument('catalog', type=str, help='the catalog location to load',
                        nargs=argparse.ZERO_OR_MORE)
        ap_group = ap.add_argument_group(title='Search options',
                                         description='If any of the following arguments specified, a search conducted.')
        ap_group.add_argument('-f''min', '--min-frequency', type=float, help='the lower frequency [MHz] to take')
        ap_group.add_argument('-f''max', '--max-frequency', type=float, help='the upper frequency [MHz] to take')
        ap_group.add_argument('-i''min', '--min-intensity', type=float,
                              help='the minimal intensity [log10(nm²×MHz)] to take')
        ap_group.add_argument('-i''max', '--max-intensity', type=float,
                              help='the maximal intensity [log10(nm²×MHz)] to take')
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
        ap_group.add_argument('--structural-formula', type=str,
                              help='a string to match the `structural''formula` field')
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
                for package in requirements:
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
            make_old_qt_compatible_again()

            import gui
        except Exception as ex:
            import tkinter
            import tkinter.messagebox
            import traceback

            traceback.print_exc()

            root: tkinter.Tk = tkinter.Tk()
            root.withdraw()
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
            root.destroy()
        else:
            gui.run()


    main()
