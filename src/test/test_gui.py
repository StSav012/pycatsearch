#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def _third_party_modules() -> list[str]:
    import site
    import sys

    prefixes: list[str] = site.getsitepackages([sys.exec_prefix, sys.prefix])
    third_party_modules: list[str] = []
    for module_name, module in sys.modules.copy().items():
        paths = getattr(module, "__path__", [])
        if (
            "." not in module_name
            and module_name != "_distutils_hack"
            and paths
            and getattr(module, "__package__", "")
            and any(p.startswith(prefix) for p in paths for prefix in prefixes)
        ):
            third_party_modules.append(module_name)

    return third_party_modules


def test_gui():
    from pycatsearch import main_gui as main

    third_party_modules: list[str]

    third_party_modules = _third_party_modules()
    assert third_party_modules == [], third_party_modules

    # intentionally fail the app after letting it import everything it needs
    from qtpy.QtCore import QCoreApplication

    app = QCoreApplication()
    assert (r := main()) != 0, r
    assert app is not None  # to ensure the app still exists

    expected_third_party_modules: list[str] = [
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "aiohttp",
        "aiosignal",
        "attr",
        "frozenlist",
        "idna",
        "multidict",
        "orjson",
        "packaging",
        "qtawesome",
        "qtpy",
        "shiboken2",
        "shiboken6",
        "yarl",
    ]
    third_party_modules = _third_party_modules()
    assert third_party_modules
    assert set(third_party_modules).issubset(expected_third_party_modules), third_party_modules


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_gui()
