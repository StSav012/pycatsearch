import atexit
import enum
import http
import platform
import shutil
import sys
from argparse import ArgumentParser, Namespace, ZERO_OR_MORE
from pathlib import Path
from tempfile import mkdtemp

__author__ = "StSav012"
__original_name__ = "pycatsearch"

try:
    from ._version import __version__
except ImportError:
    __version__ = ""


if sys.version_info < (3, 10):

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

    annotations_needed: bool = False
    for f in list_files(my_parent):
        if f.is_file():
            if f.suffix == me.suffix:
                lines: "list[str]" = f.read_text().splitlines()
                if not any(line.startswith("from __future__ import annotations") for line in lines):
                    annotations_needed = True

    if annotations_needed:
        tmp_dir: Path = Path(mkdtemp())
        sys.path.insert(0, str(tmp_dir))

        annotations_added: bool = False

        for f in list_files(my_parent):
            if f.is_file():
                (tmp_dir / __original_name__ / f.relative_to(my_parent)).parent.mkdir(parents=True, exist_ok=True)
                if f.suffix == me.suffix:
                    lines: "list[str]" = f.read_text().splitlines()
                    if not any(line.startswith("from __future__ import annotations") for line in lines):
                        lines.insert(0, "from __future__ import annotations")
                        annotations_added = True
                    new_text: str = "\n".join(lines)
                    new_text = new_text.replace("ParamSpec", "TypeVar")
                    (tmp_dir / __original_name__ / f.relative_to(my_parent)).write_text(new_text)
                else:
                    (tmp_dir / __original_name__ / f.relative_to(my_parent)).write_bytes(f.read_bytes())
            elif f.is_dir():
                (tmp_dir / __original_name__ / f.relative_to(my_parent)).mkdir()

        if annotations_added:
            for m in list(sys.modules):
                if m.startswith(my_parent.name):
                    if m in sys.modules:  # check again in case the module's gone midway
                        sys.modules.pop(m)

            import pycatsearch

        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)

if sys.version_info < (3, 11):

    class HTTPMethod(enum.Enum):
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
