import sys
from argparse import ZERO_OR_MORE, ArgumentParser, Namespace
from pathlib import Path

__author__ = "StSav012"
__original_name__ = "pycatsearch"


try:
    from ._version import __version__
except ImportError:
    __version__ = ""

if sys.version_info < (3, 10, 0) and __file__ != "<string>":  # noqa: UP036
    from collections.abc import Sequence
    from importlib import import_module
    from importlib.abc import ExecutionLoader, MetaPathFinder
    from importlib.machinery import ModuleSpec
    from importlib.util import spec_from_file_location
    from types import ModuleType

    class StringImporter(MetaPathFinder):
        class StringLoader(ExecutionLoader):
            def __init__(self, modules: "dict[str, str | dict]") -> None:
                self._modules: dict[str, str | dict] = modules

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
                substituted_module: str | dict = self._modules[module_name]
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
            self._modules: dict[str, str | dict] = modules
            self._loader = StringImporter.StringLoader(modules)

        def find_spec(
            self,
            fullname: str,
            path: "Sequence[str] | None",
            target: "ModuleType | None" = None,
        ) -> "ModuleSpec | None":
            if fullname in self._modules:
                spec: ModuleSpec | None = spec_from_file_location(fullname, loader=self._loader)
                if spec is not None:
                    spec.origin = "<string>"
                return spec
            return None

    def list_files(path: Path, *, suffix: "str | None" = None) -> "list[Path]":
        files: list[Path] = []
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
            parts: "tuple[str, ...]" = f.relative_to(my_parent).parts
            p: "dict[str, str | dict]" = py38_modules
            for part in parts[:-1]:
                if part not in p:
                    p[part] = {}
                elif isinstance((p_part := p[part]), dict):
                    p = p_part
            p[parts[-1][: -len(me.suffix)]] = new_text

    if py38_modules:
        for m in list(sys.modules):
            # check again in case the module's gone midway
            if m.partition(".")[0] == __original_name__ and m in sys.modules:
                sys.modules.pop(m)

        sys.meta_path.insert(0, StringImporter(**{__original_name__: py38_modules}))
        if __original_name__ not in sys.modules:
            sys.modules[__original_name__] = import_module(__original_name__)

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


def _cli_argument_parser() -> ArgumentParser:
    ap: ArgumentParser = ArgumentParser(
        allow_abbrev=True,
        description="Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n"
        f"Find more at https://github.com/{__author__}/{__original_name__}.",
    )
    if __version__:
        ap.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("catalog", type=Path, help="the catalog location to load", nargs=ZERO_OR_MORE)
    ap.add_argument("-fmin", "--min-frequency", type=float, help="the lower frequency [MHz] to take")
    ap.add_argument("-fmax", "--max-frequency", type=float, help="the upper frequency [MHz] to take")
    ap.add_argument(
        "-imin",
        "--min-intensity",
        type=float,
        help="the minimal intensity [log10(nm²×MHz)] to take",
    )
    ap.add_argument(
        "-imax",
        "--max-intensity",
        type=float,
        help="the maximal intensity [log10(nm²×MHz)] to take",
    )
    ap.add_argument(
        "-T",
        "--temperature",
        type=float,
        help="the temperature [K] to calculate the line intensity at, use the catalog intensity if not set",
    )
    ap.add_argument(
        "-t",
        "--tag",
        "--species-tag",
        type=int,
        dest="species_tag",
        help="a number to match the `speciestag` field",
    )
    ap.add_argument(
        "-n",
        "--any-name-or-formula",
        type=str,
        help="a string to match any field used by `any_name` and `any_formula` options",
    )
    ap.add_argument("-a", "--anything", type=str, help="a string to match any field")
    ap.add_argument("--any-name", type=str, help="a string to match the `trivial name` or the `name` field")
    ap.add_argument(
        "--any-formula",
        type=str,
        help="a string to match the `structuralformula`, `moleculesymbol`, `stoichiometricformula`, or `isotopolog` field",
    )
    ap.add_argument(
        "--InChI-key",
        "--inchi-key",
        type=str,
        dest="inchi_key",
        help="a string to match the `inchikey` field, which contains the IUPAC International Chemical Identifier (InChI™)",
    )
    ap.add_argument("--trivial-name", type=str, help="a string to match the `trivial name` field")
    ap.add_argument("--structural-formula", type=str, help="a string to match the `structural formula` field")
    ap.add_argument("--name", type=str, help="a string to match the `name` field")
    ap.add_argument("--stoichiometric-formula", type=str, help="a string to match the `stoichiometric formula` field")
    ap.add_argument("--isotopolog", type=str, help="a string to match the `isotopolog` field")
    ap.add_argument("--state", type=str, help="a string to match the `state` or `state_html` field")
    ap.add_argument(
        "--dof",
        "--degrees_of_freedom",
        type=int,
        dest="degrees_of_freedom",
        help="0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules",
    )

    return ap


def main() -> int:
    ap: ArgumentParser = _cli_argument_parser()
    args: Namespace = ap.parse_intermixed_args()

    search_args: dict[str, str | float | int] = {
        key: value for key, value in args.__dict__.items() if key != "catalog" and value is not None
    }
    if any(value is not None for value in search_args.values()):
        from .catalog import Catalog

        c: Catalog = Catalog(*args.catalog)
        c.print(**search_args)
        return 0
    else:
        print("No search parameter specified", file=sys.stderr)
        ap.print_help(file=sys.stderr)
        print("\nTrying the GUI", file=sys.stderr)
        main_gui()
        return 1


def _show_exception(ex: Exception) -> None:
    from traceback import format_exception

    error_message: str = ""
    if isinstance(ex, ImportError):
        if ex.name is not None:
            if "from" in ex.msg.split():
                error_message = (
                    f"Module {ex.name!r} lacks a part, or the latter cannot be loaded for a reason.\n"
                    "Try to update the module."
                )
            elif ex.path is None:
                error_message = f"Module {ex.name!r} cannot be found.\nTry to install it."
            else:
                error_message = (
                    f"Module {ex.name!r} cannot be loaded for an unspecified reason.\nTry to install or reinstall it."
                )
        else:
            error_message = str(ex)
    if error_message:
        error_message += "\n"

    error_message += "".join(format_exception(*sys.exc_info()))

    print(error_message, file=sys.stderr)

    try:
        import tkinter
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
            if isinstance(ex, SyntaxError):
                tkinter.messagebox.showerror(title="Syntax Error", message=error_message)
            elif isinstance(ex, ImportError):
                tkinter.messagebox.showerror(title="Package Missing", message=error_message)
            else:
                tkinter.messagebox.showerror(title="Error", message=error_message)
            root.destroy()


def download() -> None:
    from . import downloader

    downloader.download()


def async_download() -> None:
    from . import async_downloader

    async_downloader.download()


def main_gui() -> int:
    def decode(b: bytes) -> str:
        from contextlib import suppress
        from encodings import aliases
        from random import shuffle

        if isinstance(b, str):
            return b

        encodings: list[str] = list(set(aliases.aliases.values()))
        shuffle(encodings)
        encodings = ["utf-8", sys.getdefaultencoding()] + encodings
        for encoding in encodings:
            with suppress(UnicodeError):
                return b.decode(encoding=encoding)
        return b.decode(errors="replace")

    try:
        try:
            # noinspection PyUnresolvedReferences,PyPackageRequirements
            from pycatsearch_qt import main
        except (ModuleNotFoundError, ImportError):
            approved: bool
            try:
                import tkinter
                import tkinter.messagebox
            except (ModuleNotFoundError, ImportError):
                approved = True
            else:
                try:
                    root: tkinter.Tk = tkinter.Tk()
                except tkinter.TclError:
                    approved = True
                else:
                    root.withdraw()
                    approved = tkinter.messagebox.askyesno(
                        title="No GUI found",
                        message="There is no GUI. Would you like to install one?",
                    )
                    root.destroy()
            if approved:
                import subprocess
                from importlib.util import find_spec
                from shutil import which

                args: list[str]
                if find_spec("pip") is not None:
                    args = [sys.executable, "-m", "pip", "install", "-U", "pycatsearch-qt"]
                elif which("uv") is not None:
                    args = ["uv", "pip", "install", "-U", "pycatsearch-qt"]
                elif which("pip") is not None:
                    args = ["pip", "install", "-U", "pycatsearch-qt"]
                else:
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
                                title="No GUI found",
                                message="Failed to install GUI.",
                            )
                            root.destroy()
                    return 1

                for _ in range(2):
                    process: subprocess.CompletedProcess = subprocess.run(
                        args=args,
                        capture_output=True,
                        check=False,
                    )
                    if process.stdout:
                        sys.stdout.write(decode(process.stdout))
                    if process.stderr:
                        sys.stderr.write(decode(process.stderr))

                    try:
                        # noinspection PyUnresolvedReferences,PyPackageRequirements
                        from pycatsearch_qt import main
                    except (ModuleNotFoundError, ImportError):
                        try:
                            import tkinter.messagebox
                        except (ModuleNotFoundError, ImportError):
                            pass
                        else:
                            if b"--break-system-packages" in process.stderr:
                                try:
                                    root: tkinter.Tk = tkinter.Tk()
                                except tkinter.TclError:
                                    pass
                                else:
                                    root.withdraw()
                                    decision: bool = tkinter.messagebox.askretrycancel(
                                        title="No GUI found",
                                        message="Failed to install GUI.",
                                        detail="This environment is externally managed. "
                                        "Should we try breaking into system packages?",
                                    )
                                    root.destroy()
                                    if decision:
                                        args.append("--break-system-packages")
                                        continue
                            else:
                                try:
                                    root: tkinter.Tk = tkinter.Tk()
                                except tkinter.TclError:
                                    pass
                                else:
                                    root.withdraw()
                                    tkinter.messagebox.showerror(
                                        title="No GUI found",
                                        message="Failed to install GUI.",
                                        detail=decode(process.stderr),
                                    )
                                    root.destroy()
                        return process.returncode or 1
                    else:
                        return main()
            else:
                return 1
        else:
            return main()
    except Exception as ex:
        _show_exception(ex)
        return -1
