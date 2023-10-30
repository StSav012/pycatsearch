# coding=utf-8
from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

__author__ = "StSav012"
__original_name__ = "py" "cat" "search"

try:
    from ._version import __version__
except ImportError:
    __version__ = ""


def main() -> int:
    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        allow_abbrev=True,
        description="Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n"
        f"Find more at https://github.com/{__author__}/{__original_name__}.",
    )
    ap.add_argument("catalog", type=Path, help="the catalog location to load", nargs=argparse.ZERO_OR_MORE)
    ap_group = ap.add_argument_group(
        title="Search options",
        description="If any of the following arguments are specified, a search is conducted.",
    )
    ap_group.add_argument("-f" "min", "--min-frequency", type=float, help="the lower frequency [MHz] to take")
    ap_group.add_argument("-f" "max", "--max-frequency", type=float, help="the upper frequency [MHz] to take")
    ap_group.add_argument(
        "-i" "min",
        "--min-intensity",
        type=float,
        help="the minimal intensity [log10(nm²×MHz)] to take",
    )
    ap_group.add_argument(
        "-i" "max",
        "--max-intensity",
        type=float,
        help="the maximal intensity [log10(nm²×MHz)] to take",
    )
    ap_group.add_argument(
        "-T",
        "--temperature",
        type=float,
        help="the temperature [K] to calculate the line intensity at, use the catalog intensity if not set",
    )
    ap_group.add_argument(
        "-t",
        "--tag",
        "--species-tag",
        type=int,
        dest="species_tag",
        help="a number to match the `speciestag` field",
    )
    ap_group.add_argument(
        "-n",
        "--any-name-or-formula",
        type=str,
        help="a string to match any field used by `any_name` and `any_formula` options",
    )
    ap_group.add_argument("-a", "--anything", type=str, help="a string to match any field")
    ap_group.add_argument("--any-name", type=str, help="a string to match the `trivial" "name` or the `name` field")
    ap_group.add_argument(
        "--any-formula",
        type=str,
        help="a string to match the `structuralformula`, `moleculesymbol`, `stoichiometricformula`, or `isotopolog` field",
    )
    ap_group.add_argument(
        "--InChI-key",
        "--inchi-key",
        type=str,
        dest="inchi_key",
        help="a string to match the `inchikey` field, which contains the IUPAC International Chemical Identifier (InChI™)",
    )
    ap_group.add_argument("--trivial-name", type=str, help="a string to match the `trivial" "name` field")
    ap_group.add_argument("--structural-formula", type=str, help="a string to match the `structural" "formula` field")
    ap_group.add_argument("--name", type=str, help="a string to match the `name` field")
    ap_group.add_argument(
        "--stoichiometric-formula", type=str, help="a string to match the `stoichiometric" "formula` field"
    )
    ap_group.add_argument("--isotopolog", type=str, help="a string to match the `isotopolog` field")
    ap_group.add_argument("--state", type=str, help="a string to match the `state` or `state_html` field")
    ap_group.add_argument(
        "--dof",
        "--degrees_of_freedom",
        type=int,
        dest="degrees_of_freedom",
        help="0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules",
    )

    args: argparse.Namespace = ap.parse_intermixed_args()

    arg_names: list[str] = [
        "min_frequency",
        "max_frequency",
        "min_intensity",
        "max_intensity",
        "temperature",
        "species_tag",
        "any_name_or_formula",
        "anything",
        "any_name",
        "any_formula",
        "inchi_key",
        "trivial_name",
        "structural_formula",
        "name",
        "stoichiometric_formula",
        "isotopolog",
        "state",
        "degrees_of_freedom",
    ]
    search_args: dict[str, str | float | int] = dict(
        (arg, getattr(args, arg)) for arg in arg_names if getattr(args, arg) is not None
    )
    if search_args:
        from .catalog import Catalog

        c: Catalog = Catalog(*args.catalog)
        c.print(**search_args)
        return 0

    ret_code: int = main_gui()
    if ret_code != 0:
        if (ex := getattr(main_gui, "exception", None)) is not None:
            error_message: str
            if isinstance(ex, SyntaxError):
                error_message = "Python %s is not supported.\nGet a newer Python!" % platform.python_version()
            elif isinstance(ex, ImportError):
                if ex.name is not None:
                    error_message = (
                        "Module %s is either missing from the system or cannot be loaded for another reason.\n"
                        "Try to install or reinstall it." % repr(ex.name)
                    )
                else:
                    error_message = str(ex)
            else:
                import traceback

                error_message = "".join(traceback.format_exception(type(ex), value=ex, tb=None, limit=0))
            print(error_message, file=sys.stderr)
        else:
            ap.print_usage()
    return ret_code


def main_gui() -> int:
    ap: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Yet another implementation of JPL and CDMS spectroscopy catalogs offline search.\n"
        f"Find more at https://github.com/{__author__}/{__original_name__}."
    )
    ap.add_argument("catalog", type=str, help="the catalog location to load", nargs=argparse.ZERO_OR_MORE)

    try:
        from . import gui
    except Exception as ex:
        error_message: str
        if isinstance(ex, SyntaxError):
            error_message = "Python %s is not supported.\nGet a newer Python!" % platform.python_version()
        elif isinstance(ex, ImportError):
            if ex.name is not None:
                error_message = (
                    "Module %s is either missing from the system or cannot be loaded for another reason.\n"
                    "Try to install or reinstall it." % repr(ex.name)
                )
            else:
                error_message = str(ex)
        else:
            import traceback

            error_message = "".join(traceback.format_exception(type(ex), value=ex, tb=None))

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
        return 1
    else:
        try:
            return gui.run()
        except Exception as ex:
            setattr(main_gui, "exception", ex)
            return 1


def download() -> None:
    from . import downloader

    downloader.download()


def async_download() -> None:
    from . import async_downloader

    async_downloader.download()
