# coding=utf-8
from __future__ import annotations

from functools import lru_cache

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # type: ignore


@lru_cache(maxsize=None, typed=True)
def required_packages() -> list[str]:
    import sys
    if sys.version_info < (3, 8):
        return []

    import platform
    from typing import NamedTuple, Sequence

    from pkg_resources import parse_version

    class PackageRequirement(NamedTuple):
        package_name: str
        import_name: str
        min_version: str = ''

        def __str__(self) -> str:
            if self.min_version:
                return self.package_name + '>=' + self.min_version
            return self.package_name

    def is_package_importable(package_requirement: PackageRequirement) -> bool:
        from importlib import import_module
        from importlib.metadata import version

        try:
            import_module(package_requirement.import_name)
        except (ModuleNotFoundError,):
            return False
        else:
            if (package_requirement.min_version
                    and (parse_version(version(package_requirement.package_name))
                         < parse_version(package_requirement.min_version))):
                return False
        return True

    def required_package(package_requirement: PackageRequirement | Sequence[PackageRequirement]) -> PackageRequirement:
        """
        Install packages if missing

        :param package_requirement: a package name or a sequence of the names of alternative packages;
                             if none of the packages installed beforehand, install the first one given
        :returns bool: True if a package is importable, False when an attempt to install the package made
        """

        if not package_requirement:
            raise ValueError('No package requirements given')

        if isinstance(package_requirement, PackageRequirement) and is_package_importable(package_requirement):
            return package_requirement

        if not isinstance(package_requirement, PackageRequirement) and isinstance(package_requirement, Sequence):
            for _package_requirement in package_requirement:
                if is_package_importable(_package_requirement):
                    return _package_requirement

        if isinstance(package_requirement, Sequence):
            return package_requirement[0]
        return package_requirement

    qt_list: list[PackageRequirement]
    uname: platform.uname_result = platform.uname()
    if ((uname.system == 'Windows'
         and parse_version(uname.version) < parse_version('10.0.19044'))  # Windows 10 21H2 or later required
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

    requirements: list[PackageRequirement | Sequence[PackageRequirement]] = [
        PackageRequirement(package_name='qtpy', import_name='qtpy', min_version='2.3.1'),
        qt_list,
    ]
    return [str(required_package(requirement)) for requirement in requirements]


def get_requires_for_build_sdist(config_settings=None):
    return _orig.get_requires_for_build_sdist(config_settings) + required_packages()


def get_requires_for_build_wheel(config_settings=None):
    return _orig.get_requires_for_build_wheel(config_settings) + required_packages()
