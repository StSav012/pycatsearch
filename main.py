#!/usr/bin/env python3
import sys
from pathlib import Path

if sys.version_info < (3, 8, 0):
    message = (
        "The Python version "
        + ".".join(map(str, sys.version_info[:2]))
        + " is not supported.\n"
        + "Use Python 3.8 or newer."
    )
    try:
        import tkinter
    except ImportError:
        input(message)  # wait for the user to see the text
    else:
        print(message, file=sys.stderr)

        import tkinter.messagebox

        _root = tkinter.Tk()
        _root.withdraw()
        tkinter.messagebox.showerror(title="Outdated Python", message=message)
        _root.destroy()

    exit(1)

if sys.version_info < (3, 10, 0) and __file__ != "<string>":
    from importlib.abc import Loader, MetaPathFinder
    from importlib.machinery import ModuleSpec
    from importlib.util import spec_from_file_location
    from types import CodeType, ModuleType

    class StringImporter(MetaPathFinder):
        class Loader(Loader):
            def __init__(self, modules: "dict[str, str | dict]") -> None:
                self._modules: "dict[str, str | dict]" = modules

            # noinspection PyMethodMayBeStatic
            def is_package(self, module_name: str) -> bool:
                return isinstance(self._modules[module_name], dict)

            # noinspection PyMethodMayBeStatic
            def get_code(self, module_name: str) -> CodeType:
                return compile(self._modules[module_name], filename="<string>", mode="exec")

            def create_module(self, spec: ModuleSpec) -> "ModuleType | None":
                return ModuleType(spec.name)

            def exec_module(self, module: ModuleType) -> None:
                if module.__name__ not in self._modules:
                    raise ImportError(module.__name__)

                sys.modules[module.__name__] = module
                if not self.is_package(module.__name__):
                    exec(self._modules[module.__name__], module.__dict__)
                else:
                    for sub_module in self._modules[module.__name__]:
                        self._modules[".".join((module.__name__, sub_module))] = self._modules[module.__name__][
                            sub_module
                        ]
                    exec(self._modules[module.__name__].get("__init__", ""), module.__dict__)

        def __init__(self, **modules: "str | dict") -> None:
            self._modules: "dict[str, str | dict]" = modules
            self._loader = StringImporter.Loader(modules)

        def find_spec(
            self,
            fullname: str,
            path: "str | None",
            target: "ModuleType | None" = None,
        ) -> "ModuleSpec | None":
            if fullname in self._modules:
                spec: ModuleSpec = spec_from_file_location(fullname, loader=self._loader)
                spec.origin = "<string>"
                return spec
            return None

    def list_files(path: Path, *, suffix: "str | None" = None) -> "list[Path]":
        files: "list[Path]" = []
        if path.name.startswith("."):
            # ignore hidden files
            return []
        if path.is_dir():
            for file in path.iterdir():
                files.extend(list_files(file, suffix=suffix))
        elif path.is_file() and (suffix in (None, path.suffix)):
            files.append(path.absolute())
        return files

    me: Path = Path(__file__).resolve()
    my_parent: Path = me.parent

    py38_modules: "dict[str, str | dict]" = {}

    for f in list_files(my_parent, suffix=me.suffix):
        lines: "list[str]" = f.read_text(encoding="utf-8").splitlines()
        if not any(line.startswith("from __future__ import annotations") for line in lines):
            lines.insert(0, "from __future__ import annotations")
            new_text: str = "\n".join(lines)
            new_text = new_text.replace("ParamSpec", "TypeVar")
            parts: "tuple[str, ...]" = f.relative_to(my_parent).parts
            p: "dict[str, str | dict]" = py38_modules
            for part in parts[:-1]:
                if part not in p:
                    p[part] = {}
                p = p[part]
            p[parts[-1][: -len(me.suffix)]] = new_text

    if py38_modules:
        sys.meta_path.insert(0, StringImporter(**py38_modules))


if sys.version_info < (3, 11, 0):
    import http

    class HTTPMethod:
        CONNECT = "CONNECT"
        DELETE = "DELETE"
        GET = "GET"
        HEAD = "HEAD"
        OPTIONS = "OPTIONS"
        PATCH = "PATCH"
        POST = "POST"
        PUT = "PUT"
        TRACE = "TRACE"

    http.HTTPMethod = HTTPMethod


if __name__ == "__main__":
    try:
        from pycatsearch import main_gui as main
    except ImportError:
        try:
            from src.pycatsearch import main_gui as main
        except ImportError:
            __author__ = "StSav012"
            __original_name__ = "pycatsearch"

            try:
                from updater import update_with_pip

                update_with_pip(__original_name__)

                from pycatsearch import main_gui as main
            except ImportError:
                from updater import update_from_github, update_with_git, update_with_pip

                update_with_git() or update_from_github(__author__, __original_name__)

                from src.pycatsearch import main_gui as main
    exit(main())
