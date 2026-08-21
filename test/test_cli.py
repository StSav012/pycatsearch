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


def _cleanup_qtapp() -> None:
    import sys

    for m in sys.modules:
        if m.partition(".")[2] == "QtWidgets":
            instance = sys.modules[m].QApplication.instance()
            if instance is not None:
                instance.shutdown()


def test_cli():
    import sys
    from importlib.util import find_spec

    from src.pycatsearch import main

    third_party_modules: list[str]

    third_party_modules = _third_party_modules()
    assert third_party_modules == [], third_party_modules

    assert main() != 0
    _cleanup_qtapp()
    third_party_modules_after_gui: list[str] = _third_party_modules()

    sys.argv.append("catalog.json.gz")
    assert main() != 0
    _cleanup_qtapp()

    sys.argv.extend(["--min-frequency", "118749", "--max-frequency", "118751", "-n", "oxygen"])
    assert main() == 0

    third_party_modules = _third_party_modules()
    assert frozenset(third_party_modules) == frozenset(
        third_party_modules_after_gui + ["orjson"] * (find_spec("orjson") is not None)
    ), third_party_modules


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_cli()
