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


def test_cli():
    import sys
    from importlib.util import find_spec

    from pycatsearch import main_cli as main

    third_party_modules: list[str]

    third_party_modules = _third_party_modules()
    assert third_party_modules == [], third_party_modules

    assert main() != 0

    sys.argv.append("catalog.json.gz")
    assert main() != 0

    sys.argv.extend("--min-frequency 118749 --max-frequency 118751 -n oxygen".split())
    assert main() == 0

    third_party_modules = _third_party_modules()
    assert third_party_modules == ["orjson"] * (find_spec("orjson") is not None), third_party_modules


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_cli()
