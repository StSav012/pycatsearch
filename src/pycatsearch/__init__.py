import http
import platform
import sys
from argparse import ArgumentParser, Namespace, ZERO_OR_MORE
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
from pathlib import Path
from types import ModuleType

__author__ = "StSav012"
__original_name__ = "pycatsearch"


try:
    from ._version import __version__
except ImportError:
    __version__ = ""

if sys.version_info < (3, 10) and __file__ != "<string>":

    class StringImporter(MetaPathFinder):
        class Loader(Loader):
            def __init__(self, modules: "dict[str, str | dict]") -> None:
                self._modules: "dict[str, str | dict]" = modules

            # noinspection PyMethodMayBeStatic
            def is_package(self, module_name: str) -> bool:
                return isinstance(self._modules[module_name], dict)

            # noinspection PyMethodMayBeStatic
            def get_code(self, module_name: str):
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
        for m in list(sys.modules):
            if m.startswith(__original_name__):
                if m in sys.modules:  # check again in case the module's gone midway
                    sys.modules.pop(m)

        sys.meta_path.insert(0, StringImporter(**{__original_name__: py38_modules}))
        if __original_name__ not in sys.modules:
            sys.modules[__original_name__] = import_module(__original_name__)

if sys.version_info < (3, 11):

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


def _argument_parser() -> ArgumentParser:
    ap: ArgumentParser = ArgumentParser(
        allow_abbrev=True,
        description="Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n"
        f"Find more at https://github.com/{__author__}/{__original_name__}.",
    )
    ap.add_argument("catalog", type=Path, help="the catalog location to load", nargs=ZERO_OR_MORE)
    return ap


def _cli_argument_parser() -> ArgumentParser:
    ap: ArgumentParser = _argument_parser()
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


def main_cli() -> int:
    ap: ArgumentParser = _cli_argument_parser()
    args: Namespace = ap.parse_intermixed_args()

    search_args: dict[str, str | float | int] = dict(
        (key, value) for key, value in args.__dict__.items() if key != "catalog" and value is not None
    )
    if any(value is not None for value in search_args.values()):
        from .catalog import Catalog

        c: Catalog = Catalog(*args.catalog)
        c.print(**search_args)
        return 0
    else:
        print("No search parameter specified", file=sys.stderr)
        ap.print_help(file=sys.stderr)
        return 1


def _show_exception(ex: Exception) -> None:
    from traceback import format_exception

    error_message: str = ""
    if isinstance(ex, SyntaxError):
        error_message = "Python %s is not supported.\nGet a newer Python!" % platform.python_version()
    elif isinstance(ex, ImportError):
        if ex.name is not None:
            if "from" in ex.msg.split():
                error_message = (
                    "Module %s lacks a part, or the latter cannot be loaded for a reason.\n"
                    "Try to update the module." % repr(ex.name)
                )
            elif ex.path is None:
                error_message = "Module %s cannot be found.\nTry to install it." % repr(ex.name)
            else:
                error_message = (
                    "Module %s cannot be loaded for an unspecified reason.\n"
                    "Try to install or reinstall it." % repr(ex.name)
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
        root: tkinter.Tk = tkinter.Tk()
        root.withdraw()
        if isinstance(ex, SyntaxError):
            tkinter.messagebox.showerror(title="Syntax Error", message=error_message)
        elif isinstance(ex, ImportError):
            tkinter.messagebox.showerror(title="Package Missing", message=error_message)
        else:
            tkinter.messagebox.showerror(title="Error", message=error_message)
        root.destroy()


def main_gui() -> int:
    ap: ArgumentParser = _argument_parser()
    args: Namespace = ap.parse_intermixed_args()

    try:
        from . import gui
    except Exception as ex:
        _show_exception(ex)
        return 1
    else:
        try:
            return gui.run(*args.catalog)
        except Exception as ex:
            _show_exception(ex)
            return 1


def download() -> None:
    from . import downloader

    downloader.download()


def async_download() -> None:
    from . import async_downloader

    async_downloader.download()
