#!/usr/bin/env python3
# ruff: noqa: UP037
import sys
from pathlib import Path

__author__ = "StSav012"
__original_name__ = "pycatsearch"

if sys.version_info < (3, 10, 0) and __file__ != "<string>":
    import re
    from collections.abc import Sequence
    from importlib.abc import ExecutionLoader, MetaPathFinder
    from importlib.machinery import ModuleSpec
    from importlib.util import spec_from_file_location
    from types import ModuleType

    class StringImporter(MetaPathFinder):
        class StringLoader(ExecutionLoader):
            def __init__(self, modules: "dict[str, str | dict]") -> None:
                self._modules: "dict[str, str | dict]" = modules

            def is_package(self, fullname: str) -> bool:
                try:
                    return isinstance(self._modules[fullname], dict)
                except LookupError:
                    return super().is_package(fullname)

            def create_module(self, spec: ModuleSpec) -> "ModuleType | None":
                return ModuleType(spec.name)

            def get_source(self, fullname: str) -> "str | None":
                if isinstance((source := self._modules.get(fullname)), str):
                    return source
                return None

            def exec_module(self, module: ModuleType) -> None:
                module_name: str = module.__name__
                if module_name not in self._modules:
                    super().exec_module(module)
                    return

                sys.modules[module_name] = module
                substituted_module: "str | dict" = self._modules[module_name]
                if not isinstance(substituted_module, dict):
                    exec(substituted_module, module.__dict__)
                else:
                    for sub_module in substituted_module:
                        self._modules[f"{module_name}.{sub_module}"] = substituted_module[sub_module]
                    exec(substituted_module.get("__init__", ""), module.__dict__)

            def get_filename(self, fullname: str) -> str:
                if fullname == __original_name__:
                    return str(me)
                if fullname.startswith(__original_name__ + "."):
                    return str(my_parent / Path(*fullname.split(".")[1:]))
                raise ImportError(fullname)

        def __init__(self, **modules: "str | dict") -> None:
            self._modules: "dict[str, str | dict]" = modules
            self._loader = StringImporter.StringLoader(modules)

        def find_spec(
            self,
            fullname: str,
            path: "Sequence[str] | None",
            target: "ModuleType | None" = None,
        ) -> "ModuleSpec | None":
            if fullname in self._modules:
                spec: "ModuleSpec | None" = spec_from_file_location(fullname, loader=self._loader)
                if spec is not None:
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
            lines.insert(1, "from typing import Dict, List, Set, Tuple, TypeVar")
            new_text: str = (
                "\n".join(lines)
                .replace("dict[", "Dict[")
                .replace("list[", "List[")
                .replace("set[", "Set[")
                .replace("tuple[", "Tuple[")
            )
            new_text = re.sub(r"from typing import TypeGuard$", "", new_text)
            new_text = re.sub(r"(from typing import) TypeGuard,(.*)", r"\1\2", new_text)
            new_text = re.sub(r"(from typing import\b.*?), TypeGuard\b(.*)", r"\1\2", new_text)
            new_text = re.sub(r"TypeGuard\[\w+](?=:)", "bool", new_text)
            new_text = re.sub(r"from typing import Self$", "", new_text)
            new_text = re.sub(r"(from typing import) Self,(.*)", r"\1\2", new_text)
            new_text = re.sub(r"(from typing import\b.*?), Self\b(.*)", r"\1\2", new_text)
            new_text = re.sub(r"Self(?=:)", "object", new_text)
            parts: "tuple[str, ...]" = f.relative_to(my_parent).parts
            p: "dict[str, str | dict]" = py38_modules
            for part in parts[:-1]:
                if part not in p:
                    p[part] = {}
                elif isinstance((p_part := p[part]), dict):
                    p = p_part
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

    def main() -> int:
        try:
            import tkinter.messagebox
        except (ModuleNotFoundError, ImportError):
            pass
        else:
            try:
                root: tkinter.Tk = tkinter.Tk()
            except tkinter.TclError:
                pass
            else:
                root.withdraw()
                tkinter.messagebox.showerror(
                    title="PyCatSearch Error",
                    message="Failed to load PyCatSearch GUI.",
                )
                root.destroy()
        return 1

    try:
        from pycatsearch import main_gui as main
    except (ModuleNotFoundError, ImportError):
        try:
            from src.pycatsearch import main_gui as main
        except (ModuleNotFoundError, ImportError):
            try:
                from updater import update_with_pip
            except (ModuleNotFoundError, ImportError):
                pass
            else:
                update_with_pip(__original_name__)

                try:
                    from pycatsearch import main_gui as main
                except (ModuleNotFoundError, ImportError):
                    try:
                        from updater import update_from_github, update_with_git
                    except (ModuleNotFoundError, ImportError):
                        pass
                    else:
                        update_with_git() or update_from_github(__author__, __original_name__)

                        try:
                            from src.pycatsearch import main_gui as main
                        except (ModuleNotFoundError, ImportError):
                            pass

    exit(main())
