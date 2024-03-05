# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import html.entities
import itertools
import os
import sys
from math import e as _e, inf, log10, nan, pow
from numbers import Real
from typing import Any, Callable, Final, Iterable, Protocol, Sequence, TypeVar, cast, overload

__all__ = [
    "M_LOG10E",
    "T0",
    "c",
    "h",
    "k",
    "e",
    "CATALOG",
    "BUILD_TIME",
    "LINES",
    "FREQUENCY",
    "INTENSITY",
    "ID",
    "STRUCTURAL_FORMULA",
    "STOICHIOMETRIC_FORMULA",
    "MOLECULE",
    "MOLECULE_SYMBOL",
    "SPECIES_TAG",
    "NAME",
    "TRIVIAL_NAME",
    "ISOTOPOLOG",
    "STATE",
    "STATE_HTML",
    "INCHI_KEY",
    "DEGREES_OF_FREEDOM",
    "LOWER_STATE_ENERGY",
    "CONTRIBUTOR",
    "VERSION",
    "DATE_OF_ENTRY",
    "HUMAN_READABLE",
    "ghz_to_mhz",
    "ghz_to_nm",
    "ghz_to_rec_cm",
    "mhz_to_ghz",
    "mhz_to_nm",
    "mhz_to_rec_cm",
    "nm_to_ghz",
    "nm_to_mhz",
    "nm_to_rec_cm",
    "rec_cm_to_ghz",
    "rec_cm_to_mhz",
    "rec_cm_to_nm",
    "rec_cm_to_meV",
    "rec_cm_to_j",
    "meV_to_rec_cm",
    "j_to_rec_cm",
    "log10_sq_nm_mhz_to_sq_nm_mhz",
    "log10_sq_nm_mhz_to_log10_cm_per_molecule",
    "log10_sq_nm_mhz_to_cm_per_molecule",
    "sq_nm_mhz_to_log10_sq_nm_mhz",
    "log10_cm_per_molecule_to_log10_sq_nm_mhz",
    "cm_per_molecule_to_log10_sq_nm_mhz",
    "sort_unique",
    "merge_sorted",
    "search_sorted",
    "within",
    "chem_html",
    "best_name",
    "remove_html",
    "wrap_in_html",
    "ensure_prefix",
    "save_catalog_to_file",
    "ReleaseInfo",
    "latest_release",
    "update_with_pip",
    "tag",
    "p_tag",
    "a_tag",
]

M_LOG10E: Final[float] = log10(_e)

T0: Final[float] = 300.00  # [K], see https://spec.jpl.nasa.gov/ftp/pub/catalog/doc/catdoc.pdf
k: Final[float] = 1.380649000e-23  # [J/K],  see https://physics.nist.gov/cgi-bin/cuu/Value?k
h: Final[float] = 6.626070150e-34  # [J/Hz], see https://physics.nist.gov/cgi-bin/cuu/Value?h
e: Final[float] = 1.602176634e-19  # [C],    see https://physics.nist.gov/cgi-bin/cuu/Value?e
c: Final[float] = 299_792_458.000  # [m/s],  see https://physics.nist.gov/cgi-bin/cuu/Value?c

CATALOG: Final[str] = "catalog"
BUILD_TIME: Final[str] = "build_time"
LINES: Final[str] = "lines"
FREQUENCY: Final[str] = "frequency"
INTENSITY: Final[str] = "intensity"
ID: Final[str] = "id"
MOLECULE: Final[str] = "molecule"
STRUCTURAL_FORMULA: Final[str] = "structuralformula"
STOICHIOMETRIC_FORMULA: Final[str] = "stoichiometricformula"
MOLECULE_SYMBOL: Final[str] = "moleculesymbol"
SPECIES_TAG: Final[str] = "speciestag"
NAME: Final[str] = "name"
TRIVIAL_NAME: Final[str] = "trivialname"
ISOTOPOLOG: Final[str] = "isotopolog"
STATE: Final[str] = "state"
STATE_HTML: Final[str] = "state_html"
INCHI_KEY: Final[str] = "inchikey"
CONTRIBUTOR: Final[str] = "contributor"
VERSION: Final[str] = "version"
DATE_OF_ENTRY: Final[str] = "dateofentry"
DEGREES_OF_FREEDOM: Final[str] = "degreesoffreedom"
LOWER_STATE_ENERGY: Final[str] = "lowerstateenergy"

HUMAN_READABLE: Final[dict[str, str]] = {
    CATALOG: "Catalog",
    LINES: "Lines",
    FREQUENCY: "Frequency",
    INTENSITY: "Intensity",
    ID: "ID",
    MOLECULE: "Molecule",
    STRUCTURAL_FORMULA: "Structural formula",
    STOICHIOMETRIC_FORMULA: "Stoichiometric formula",
    MOLECULE_SYMBOL: "Molecule symbol",
    SPECIES_TAG: "Species tag",
    NAME: "Name",
    TRIVIAL_NAME: "Trivial name",
    ISOTOPOLOG: "Isotopolog",
    STATE: "State (TeX)",
    STATE_HTML: "State (HTML)",
    INCHI_KEY: "InChI key",
    CONTRIBUTOR: "Contributor",
    VERSION: "Version",
    DATE_OF_ENTRY: "Date of entry",
    DEGREES_OF_FREEDOM: "Degrees of freedom",
    LOWER_STATE_ENERGY: "Lower state energy",
}


def within(x: float, limits: tuple[float, float] | tuple[tuple[float, float], ...]) -> bool:
    if len(limits) < 2:
        raise ValueError("Invalid limits")
    if all(isinstance(limit, Real) for limit in limits):
        return min(limits) <= x <= max(limits)
    elif all(isinstance(limit, tuple) for limit in limits):
        return any(min(limit) <= x <= max(limit) for limit in limits)
    else:
        raise TypeError("Invalid limits type")


_AnyType = TypeVar("_AnyType")


class SupportsLessAndEqual(Protocol[_AnyType]):
    def __eq__(self, other: _AnyType) -> bool:
        pass

    def __lt__(self, other: _AnyType) -> bool:
        pass

    def __le__(self, other: _AnyType) -> bool:
        pass


@overload
def sort_unique(
    items: Sequence[_AnyType], *, key: Callable[[_AnyType], SupportsLessAndEqual], reverse: bool = False
) -> list[_AnyType]:
    pass


@overload
def sort_unique(
    items: Sequence[SupportsLessAndEqual],
    *,
    key: Callable[[SupportsLessAndEqual], SupportsLessAndEqual] | None = None,
    reverse: bool = False,
) -> list[SupportsLessAndEqual]:
    pass


def sort_unique(
    items: Sequence[SupportsLessAndEqual] | Sequence[_AnyType],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual] | None = None,
    reverse: bool = False,
) -> list[SupportsLessAndEqual]:
    sorted_items: list[SupportsLessAndEqual] = sorted(items, key=key, reverse=reverse)
    i: int = 0
    while i < len(sorted_items) - 1:
        while i < len(sorted_items) - 1 and sorted_items[i] == sorted_items[i + 1]:
            del sorted_items[i + 1]
        i += 1
    return sorted_items


@overload
def merge_sorted(
    items_1: Sequence[_AnyType], items_2: Sequence[_AnyType], *, key: Callable[[_AnyType], SupportsLessAndEqual]
) -> list[_AnyType]:
    pass


@overload
def merge_sorted(
    items_1: Sequence[SupportsLessAndEqual],
    items_2: Sequence[SupportsLessAndEqual],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual] | None = None,
) -> list[SupportsLessAndEqual]:
    pass


def merge_sorted(
    items_1: Sequence[SupportsLessAndEqual] | Sequence[_AnyType],
    items_2: Sequence[SupportsLessAndEqual] | Sequence[_AnyType],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual] | None = None,
) -> list[SupportsLessAndEqual]:
    sorted_items_1: list[SupportsLessAndEqual] = sort_unique(items_1, key=key, reverse=False)
    sorted_items_2: list[SupportsLessAndEqual] = sort_unique(items_2, key=key, reverse=False)
    merged_items: list[SupportsLessAndEqual] = []

    last_i_1: int
    last_i_2: int
    i_1: int = 0
    i_2: int = 0

    if key is None:

        def key(value: _AnyType) -> SupportsLessAndEqual:
            return value

    while i_1 < len(sorted_items_1) and i_2 < len(sorted_items_2):
        last_i_1 = i_1
        while (
            i_1 < len(sorted_items_1)
            and i_2 < len(sorted_items_2)
            and key(sorted_items_1[i_1]) <= key(sorted_items_2[i_2])
        ):
            i_1 += 1
        if last_i_1 < i_1:
            merged_items.extend(sorted_items_1[last_i_1:i_1])

        last_i_2 = i_2
        while (
            i_1 < len(sorted_items_1)
            and i_2 < len(sorted_items_2)
            and key(sorted_items_2[i_2]) <= key(sorted_items_1[i_1])
        ):
            i_2 += 1
        if last_i_2 < i_2:
            merged_items.extend(sorted_items_2[last_i_2:i_2])

    while i_1 < len(sorted_items_1) and key(merged_items[-1]) == key(sorted_items_1[i_1]):
        i_1 += 1
    if i_1 < len(sorted_items_1) and i_2 >= len(sorted_items_2):
        merged_items.extend(sorted_items_1[i_1:])
    while i_2 < len(sorted_items_2) and key(merged_items[-1]) == key(sorted_items_2[i_2]):
        i_2 += 1
    if i_2 < len(sorted_items_2) and i_1 >= len(sorted_items_1):
        merged_items.extend(sorted_items_2[i_2:])
    return merged_items


@overload
def search_sorted(
    threshold: SupportsLessAndEqual,
    items: Sequence[_AnyType],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual],
    maybe_equal: bool = False,
) -> int:
    pass


@overload
def search_sorted(
    threshold: SupportsLessAndEqual,
    items: Sequence[SupportsLessAndEqual],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual] | None = None,
    maybe_equal: bool = False,
) -> int:
    pass


def search_sorted(
    threshold: SupportsLessAndEqual,
    items: Sequence[_AnyType] | Sequence[SupportsLessAndEqual],
    *,
    key: Callable[[_AnyType], SupportsLessAndEqual] | None = None,
    maybe_equal: bool = False,
) -> int:
    from operator import lt, le

    if not items:
        raise ValueError("Empty sequence provided")
    if key is None:

        def key(value: _AnyType) -> SupportsLessAndEqual:
            return value

    less: Callable[[SupportsLessAndEqual, SupportsLessAndEqual], bool] = le if maybe_equal else lt
    if not less(key(items[0]), threshold):
        return -1
    if less(key(items[-1]), threshold):
        return len(items)
    i: int = 0
    j: int = len(items) - 1
    n: int
    while j - i > 1:
        n = (i + j) // 2
        if less(key(items[n]), threshold):
            i = n
        else:
            j = n
    if i != j and not less(key(items[j]), threshold):
        return i
    return j


def mhz_to_ghz(frequency_mhz: float) -> float:
    return frequency_mhz * 1e-3


def mhz_to_rec_cm(frequency_mhz: float) -> float:
    return frequency_mhz * 1e4 / c


def mhz_to_nm(frequency_mhz: float) -> float:
    return c / frequency_mhz * 1e3


def ghz_to_mhz(frequency_ghz: float) -> float:
    return frequency_ghz * 1e3


def ghz_to_rec_cm(frequency_ghz: float) -> float:
    return frequency_ghz * 1e7 / c


def ghz_to_nm(frequency_ghz: float) -> float:
    return c / frequency_ghz


def rec_cm_to_mhz(frequency_rec_cm: float) -> float:
    return frequency_rec_cm * 1e-4 * c


def rec_cm_to_ghz(frequency_rec_cm: float) -> float:
    return frequency_rec_cm * 1e-7 * c


def rec_cm_to_nm(frequency_rec_cm: float) -> float:
    return 1e7 / frequency_rec_cm


def rec_cm_to_meV(energy_rec_cm: float) -> float:
    return 1e5 * h * c / e * energy_rec_cm


def rec_cm_to_j(energy_rec_cm: float) -> float:
    return 1e2 * h * c * energy_rec_cm


def nm_to_mhz(frequency_nm: float) -> float:
    return c / frequency_nm * 1e-3


def nm_to_ghz(frequency_nm: float) -> float:
    return c / frequency_nm


def nm_to_rec_cm(frequency_nm: float) -> float:
    return 1e7 / frequency_nm


def meV_to_rec_cm(energy_mev: float) -> float:
    return 1e-5 * e / h / c * energy_mev


def j_to_rec_cm(energy_j: float) -> float:
    return 1e-2 / h / c * energy_j


def log10_sq_nm_mhz_to_sq_nm_mhz(intensity_log10_sq_nm_mhz: float) -> float:
    return pow(10.0, intensity_log10_sq_nm_mhz)


def log10_sq_nm_mhz_to_log10_cm_per_molecule(intensity_log10_sq_nm_mhz: float) -> float:
    return -10.0 + intensity_log10_sq_nm_mhz - log10(c)


def log10_sq_nm_mhz_to_cm_per_molecule(intensity_log10_sq_nm_mhz: float) -> float:
    return pow(10.0, log10_sq_nm_mhz_to_log10_cm_per_molecule(intensity_log10_sq_nm_mhz))


def sq_nm_mhz_to_log10_sq_nm_mhz(intensity_sq_nm_mhz: float) -> float:
    if intensity_sq_nm_mhz == 0.0:
        return -inf
    if intensity_sq_nm_mhz < 0.0:
        return nan
    return log10(intensity_sq_nm_mhz)


def log10_cm_per_molecule_to_log10_sq_nm_mhz(intensity_log10_cm_per_molecule: float) -> float:
    return intensity_log10_cm_per_molecule + 10.0 + log10(c)


def cm_per_molecule_to_log10_sq_nm_mhz(intensity_cm_per_molecule: float) -> float:
    if intensity_cm_per_molecule == 0.0:
        return -inf
    if intensity_cm_per_molecule < 0.0:
        return nan
    return log10_cm_per_molecule_to_log10_sq_nm_mhz(log10(intensity_cm_per_molecule))


def tex_to_html_entity(s: str) -> str:
    r"""
    Change LaTeX entities syntax to HTML one.
    Get ‘\alpha’ to be ‘&alpha;’ and so on.
    Unknown LaTeX entities do not get replaced.

    :param s: A line to convert
    :return: a line with all LaTeX entities renamed
    """
    word_start: int = -1
    word_started: bool = False
    backslash_found: bool = False
    _i: int = 0
    fixes: dict[str, str] = {
        "neq": "#8800",
    }
    while _i < len(s):
        _c: str = s[_i]
        if word_started and not _c.isalpha():
            word_started = False
            if s[word_start:_i] + ";" in html.entities.entitydefs:
                s = s[: word_start - 1] + "&" + s[word_start:_i] + ";" + s[_i:]
                _i += 2
            elif s[word_start:_i] in fixes:
                s = s[: word_start - 1] + "&" + fixes[s[word_start:_i]] + ";" + s[_i:]
                _i += 2
        if backslash_found and _c.isalpha() and not word_started:
            word_start = _i
            word_started = True
        backslash_found = _c == "\\"
        _i += 1
    if word_started:
        if s[word_start:_i] + ";" in html.entities.entitydefs:
            s = s[: word_start - 1] + "&" + s[word_start:_i] + ";" + s[_i:]
            _i += 2
        elif s[word_start:_i] in fixes:
            s = s[: word_start - 1] + "&" + fixes[s[word_start:_i]] + ";" + s[_i:]
            _i += 2
    return s


def chem_html(formula: str) -> str:
    """converts plain text chemical formula into html markup"""
    if "<" in formula or ">" in formula:
        # we can not tell whether it's a tag or a mathematical sign
        return formula

    def sub_tag(s: str) -> str:
        return "<sub>" + s + "</sub>"

    def sup_tag(s: str) -> str:
        return "<sup>" + s + "</sup>"

    def i_tag(s: str) -> str:
        return "<i>" + s + "</i>"

    def subscript(s: str) -> str:
        number_start: int = -1
        number_started: bool = False
        cap_alpha_started: bool = False
        low_alpha_started: bool = False
        _i: int = 0
        while _i < len(s):
            _c: str = s[_i]
            if number_started and not _c.isdigit():
                number_started = False
                s = s[:number_start] + sub_tag(s[number_start:_i]) + s[_i:]
                _i += 1
            if (cap_alpha_started or low_alpha_started) and _c.isdigit() and not number_started:
                number_start = _i
                number_started = True
            if low_alpha_started:
                cap_alpha_started = False
                low_alpha_started = False
            if cap_alpha_started and _c.islower() or _c == ")":
                low_alpha_started = True
            cap_alpha_started = _c.isupper()
            _i += 1
        if number_started:
            s = s[:number_start] + sub_tag(s[number_start:])
        return s

    def prefix(s: str) -> str:
        no_digits: bool = False
        _i: int = len(s)
        while not no_digits:
            _i = s.rfind("-", 0, _i)
            if _i == -1:
                break
            if s[:_i].isalpha() and s[:_i].isupper():
                break
            no_digits = True
            _c: str
            unescaped_prefix: str = html.unescape(s[:_i])
            for _c in unescaped_prefix:
                if _c.isdigit() or _c == "<":
                    no_digits = False
                    break
            if no_digits and (unescaped_prefix[0].islower() or unescaped_prefix[0] == "("):
                return i_tag(s[:_i]) + s[_i:]
        return s

    def charge(s: str) -> str:
        if s[-1] in "+-":
            return s[:-1] + sup_tag(s[-1])
        return s

    def v(s: str) -> str:
        if "=" not in s:
            return s[0] + " = " + s[1:]
        ss: list[str] = list(map(str.strip, s.split("=")))
        for _i in range(len(ss)):
            if ss[_i].startswith("v"):
                ss[_i] = ss[_i][0] + sub_tag(ss[_i][1:])
        return " = ".join(ss)

    html_formula: str = html.escape(formula)
    html_formula_pieces: list[str] = list(map(str.strip, html_formula.split(",")))
    for i in range(len(html_formula_pieces)):
        if html_formula_pieces[i].startswith("v"):
            html_formula_pieces = html_formula_pieces[:i] + [", ".join(html_formula_pieces[i:])]
            break
    for i in range(len(html_formula_pieces)):
        if html_formula_pieces[i].startswith("v"):
            html_formula_pieces[i] = v(html_formula_pieces[i])
            break
        for function in (subscript, prefix, charge):
            html_formula_pieces[i] = function(html_formula_pieces[i])
    html_formula = ", ".join(html_formula_pieces)
    return html_formula


def is_good_html(text: str) -> bool:
    """Basic check that all tags are sound"""
    _1, _2, _3 = text.count("<"), text.count(">"), 2 * text.count("</")
    return _1 == _2 and _1 == _3


def best_name(entry: dict[str, int | str | list[dict[str, float]]], allow_html: bool = True) -> str:
    species_tag: int = cast(int, entry.get(SPECIES_TAG, 0))
    last: str = best_name.__dict__.get("last", dict()).get(species_tag, dict()).get(allow_html, "")
    if last:
        return last

    def _best_name() -> str:
        if isotopolog := entry.get(ISOTOPOLOG, ""):
            if allow_html:
                if is_good_html(str(molecule_symbol := entry[MOLECULE_SYMBOL])) and (
                    entry.get(STRUCTURAL_FORMULA, "") == isotopolog
                    or entry.get(STOICHIOMETRIC_FORMULA, "") == isotopolog
                ):
                    if state_html := cast(str, entry.get(STATE_HTML, "")):
                        # span tags are needed when the molecule symbol is malformed
                        return f"<span>{molecule_symbol}</span>, " f"{chem_html(tex_to_html_entity(str(state_html)))}"
                    return str(molecule_symbol)
                else:
                    if state_html := cast(str, entry.get(STATE_HTML, "")):
                        return f"{chem_html(str(isotopolog))}, " f"{chem_html(tex_to_html_entity(str(state_html)))}"
                    return chem_html(str(isotopolog))
            else:
                if state_html := cast(str, entry.get(STATE_HTML, "")):
                    return f"{isotopolog}, {remove_html(tex_to_html_entity(state_html))}"
                if state := cast(str, entry.get(STATE, "")):
                    return f'{isotopolog}, {remove_html(tex_to_html_entity(state.strip("$")))}'
                return isotopolog

        for key in (NAME, STRUCTURAL_FORMULA, STOICHIOMETRIC_FORMULA):
            if candidate := entry.get(key, ""):
                return chem_html(str(candidate)) if allow_html else str(candidate)
        if trivial_name := entry.get(TRIVIAL_NAME, ""):
            return str(trivial_name)
        if species_tag:
            return str(species_tag)
        return "no name"

    res: str = _best_name()
    if not species_tag:
        return res
    if "last" not in best_name.__dict__:
        best_name.__dict__["last"] = dict()
    if species_tag not in best_name.__dict__["last"]:
        best_name.__dict__["last"][species_tag] = dict()
    best_name.__dict__["last"][species_tag][allow_html] = res
    return res


def remove_html(line: str) -> str:
    """removes HTML tags and decodes HTML entities"""
    if not is_good_html(line):
        return html.unescape(line)

    new_line: str = line
    tag_start: int = new_line.find("<")
    tag_end: int = new_line.find(">", tag_start)
    while tag_start != -1 and tag_end != -1:
        new_line = new_line[:tag_start] + new_line[tag_end + 1 :]
        tag_start = new_line.find("<")
        tag_end = new_line.find(">", tag_start)
    return html.unescape(new_line).lstrip()


def wrap_in_html(text: str, line_end: str = os.linesep) -> str:
    """Make a full HTML document out of a piece of the markup"""
    new_text: list[str] = [
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">',
        '<html lang="en" xml:lang="en">',
        "<head>",
        '<meta http-equiv="content-type" content="text/html; charset=utf-8">',
        "</head>",
        "<body>",
        text,
        "</body>",
        "</html>",
    ]

    return line_end.join(new_text)


def ensure_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text
    else:
        return prefix + text


def save_catalog_to_file(
    filename: str | os.PathLike[str],
    catalog: dict[int, dict[str, int | str | list[dict[str, float]]]],
    frequency_limits: tuple[float, float],
) -> bool:
    from .catalog import Catalog

    if not catalog:
        return False
    Catalog.from_data(catalog_data=catalog, frequency_limits=frequency_limits).save(filename=filename)
    return True


class ReleaseInfo:
    def __init__(self, version: str = "", pub_date: str = "") -> None:
        self.version: str = version
        self.pub_date: str = pub_date

    def __bool__(self) -> bool:
        return bool(self.version) and bool(self.pub_date)

    def __lt__(self, other: str | ReleaseInfo) -> bool:
        if isinstance(other, str):
            other = ReleaseInfo(version=other)
        i: str
        j: str
        for i, j in itertools.zip_longest(
            self.version.replace("-", ".").split("."), other.version.replace("-", ".").split("."), fillvalue=""
        ):
            if i == j:
                continue
            if i.isdigit() and j.isdigit():
                return int(i) < int(j)
            else:
                i_digits: str = "".join(itertools.takewhile(str.isdigit, i))
                j_digits: str = "".join(itertools.takewhile(str.isdigit, j))
                if i_digits != j_digits:
                    if i_digits and j_digits:
                        return int(i_digits) < int(j_digits)
                    else:
                        return i_digits < j_digits
                return i < j
        return False

    def __eq__(self, other: str | ReleaseInfo) -> bool:
        if not isinstance(other, (str, ReleaseInfo)):
            return NotImplemented
        if isinstance(other, str):
            other = ReleaseInfo(version=other)
        return self.version == other.version


def latest_release() -> ReleaseInfo:
    import urllib.request
    import xml.dom.minidom as dom
    from http.client import HTTPResponse
    from xml.dom.minicompat import NodeList
    from urllib.error import URLError

    from . import __original_name__

    try:
        r: HTTPResponse = urllib.request.urlopen(
            f"https://pypi.org/rss/project/{__original_name__}/releases.xml", timeout=1
        )
    except URLError:
        return ReleaseInfo()
    if r.getcode() != 200 or not r.readable():
        return ReleaseInfo()
    rss: dom.Node | None = dom.parseString(r.read().decode(encoding="ascii")).documentElement
    if not isinstance(rss, dom.Element) or rss.tagName != "rss":
        return ReleaseInfo()
    channels: NodeList = rss.getElementsByTagName("channel")
    if not channels or channels[0].nodeType != dom.Node.ELEMENT_NODE:
        return ReleaseInfo()
    channel: dom.Element = channels[0]
    items: NodeList = channel.getElementsByTagName("item")
    if not items or items[0].nodeType != dom.Node.ELEMENT_NODE:
        return ReleaseInfo()
    item: dom.Element = items[0]
    titles: NodeList = item.getElementsByTagName("title")
    if not titles or titles[0].nodeType != dom.Node.ELEMENT_NODE:
        return ReleaseInfo()
    title: dom.Element = titles[0]
    pub_dates: NodeList = item.getElementsByTagName("pubDate")
    if not pub_dates or pub_dates[0].nodeType != dom.Node.ELEMENT_NODE:
        return ReleaseInfo()
    pub_date: dom.Element = pub_dates[0]
    title_value: dom.Node = title.firstChild
    pub_date_value: dom.Node = pub_date.firstChild
    if not isinstance(title_value, dom.Text) or not isinstance(pub_date_value, dom.Text):
        return ReleaseInfo()

    return ReleaseInfo(title_value.data, pub_date_value.data)


def update_with_pip() -> None:
    import subprocess
    import sys

    from . import __original_name__

    subprocess.Popen(
        args=[
            sys.executable,
            "-c",
            f"""import sys, subprocess, time; time.sleep(2);\
        subprocess.run(args=[sys.executable, '-m', 'pip', 'install', '-U', {__original_name__!r}]);\
        subprocess.Popen(args=[sys.executable, '-m', {__original_name__!r}])""",
        ]
    )
    sys.exit(0)


def tag(name: str, text: str = "", **attrs: str) -> str:
    parts: list[str] = ["<", " ".join((name, *itertools.starmap(lambda a, v: f"{a}={str(v)!r}", attrs.items())))]
    if text:
        parts.extend([">", text, "</", name, ">"])
    else:
        parts.append("/>")
    return "".join(parts)


def p_tag(text: str) -> str:
    return tag("p", text)


def a_tag(text: str, url: str) -> str:
    return tag("a", text, href=url)


if sys.version_info < (3, 10):
    import builtins

    # noinspection PyShadowingBuiltins, PyUnusedLocal
    def zip(*iterables: Iterable[Any], strict: bool = False) -> builtins.zip:
        """Intentionally override `builtins.zip` to ignore `strict` parameter in Python < 3.10"""
        return builtins.zip(*iterables)

    __all__.append("zip")
