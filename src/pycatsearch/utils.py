# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import html
import html.entities
import json
import math
import os
from numbers import Real
from pathlib import Path
from types import ModuleType
from typing import BinaryIO, Final, cast

__all__ = ['M_LOG10E',
           'T0', 'c', 'h', 'k', 'e',
           'CATALOG', 'BUILD_TIME', 'LINES', 'FREQUENCY', 'INTENSITY', 'ID', 'STRUCTURAL_FORMULA',
           'STOICHIOMETRIC_FORMULA', 'MOLECULE', 'MOLECULE_SYMBOL', 'SPECIES_TAG', 'NAME', 'TRIVIAL_NAME', 'ISOTOPOLOG',
           'STATE', 'STATE_HTML', 'INCHI_KEY', 'DEGREES_OF_FREEDOM', 'LOWER_STATE_ENERGY', 'CONTRIBUTOR', 'VERSION',
           'DATE_OF_ENTRY', 'HUMAN_READABLE',
           'ghz_to_mhz', 'ghz_to_nm', 'ghz_to_rec_cm',
           'mhz_to_ghz', 'mhz_to_nm', 'mhz_to_rec_cm',
           'nm_to_ghz', 'nm_to_mhz', 'nm_to_rec_cm',
           'rec_cm_to_ghz', 'rec_cm_to_mhz', 'rec_cm_to_nm', 'rec_cm_to_meV', 'rec_cm_to_j',
           'meV_to_rec_cm', 'j_to_rec_cm',
           'log10_sq_nm_mhz_to_sq_nm_mhz',
           'log10_sq_nm_mhz_to_log10_cm_per_molecule',
           'log10_sq_nm_mhz_to_cm_per_molecule',
           'sq_nm_mhz_to_log10_sq_nm_mhz',
           'log10_cm_per_molecule_to_log10_sq_nm_mhz',
           'cm_per_molecule_to_log10_sq_nm_mhz',
           'within', 'chem_html', 'best_name', 'remove_html', 'wrap_in_html',
           'find_qt_core',
           'save_catalog_to_file']

M_LOG10E: Final[float] = math.log10(math.e)

T0: Final[float] = 300.00
k: Final[float] = 1.380649000e-23  # https://physics.nist.gov/cgi-bin/cuu/Value?k
h: Final[float] = 6.626070150e-34  # https://physics.nist.gov/cgi-bin/cuu/Value?h
e: Final[float] = 1.602176634e-19  # https://physics.nist.gov/cgi-bin/cuu/Value?e
c: Final[float] = 299792458.00000  # https://physics.nist.gov/cgi-bin/cuu/Value?c

CATALOG: Final[str] = 'catalog'
BUILD_TIME: Final[str] = 'build_time'
LINES: Final[str] = 'lines'
FREQUENCY: Final[str] = 'frequency'
INTENSITY: Final[str] = 'intensity'
ID: Final[str] = 'id'
MOLECULE: Final[str] = 'molecule'
STRUCTURAL_FORMULA: Final[str] = 'structuralformula'
STOICHIOMETRIC_FORMULA: Final[str] = 'stoichiometricformula'
MOLECULE_SYMBOL: Final[str] = 'moleculesymbol'
SPECIES_TAG: Final[str] = 'speciestag'
NAME: Final[str] = 'name'
TRIVIAL_NAME: Final[str] = 'trivialname'
ISOTOPOLOG: Final[str] = 'isotopolog'
STATE: Final[str] = 'state'
STATE_HTML: Final[str] = 'state_html'
INCHI_KEY: Final[str] = 'inchikey'
CONTRIBUTOR: Final[str] = 'contributor'
VERSION: Final[str] = 'version'
DATE_OF_ENTRY: Final[str] = 'dateofentry'
DEGREES_OF_FREEDOM: Final[str] = 'degreesoffreedom'
LOWER_STATE_ENERGY: Final[str] = 'lowerstateenergy'

HUMAN_READABLE: Final[dict[str, str]] = {
    CATALOG: 'Catalog',
    LINES: 'Lines',
    FREQUENCY: 'Frequency',
    INTENSITY: 'Intensity',
    ID: 'ID',
    MOLECULE: 'Molecule',
    STRUCTURAL_FORMULA: 'Structural formula',
    STOICHIOMETRIC_FORMULA: 'Stoichiometric formula',
    MOLECULE_SYMBOL: 'Molecule symbol',
    SPECIES_TAG: 'Species tag',
    NAME: 'Name',
    TRIVIAL_NAME: 'Trivial name',
    ISOTOPOLOG: 'Isotopolog',
    STATE: 'State (TeX)',
    STATE_HTML: 'State (HTML)',
    INCHI_KEY: 'InChI key',
    CONTRIBUTOR: 'Contributor',
    VERSION: 'Version',
    DATE_OF_ENTRY: 'Date of entry',
    DEGREES_OF_FREEDOM: 'Degrees of freedom',
    LOWER_STATE_ENERGY: 'Lower state energy',
}


def within(x: float, limits: tuple[float, float] | tuple[tuple[float, float], ...]) -> bool:
    if len(limits) < 2:
        raise ValueError('Invalid limits')
    if all(isinstance(cast(float, limit), Real) for limit in limits):
        return min(limits) <= x <= max(limits)
    elif all(isinstance(limit, tuple) for limit in limits):
        return any(min(limit) <= x <= max(limit) for limit in limits)
    else:
        raise TypeError('Invalid limits type')


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
    return math.pow(10.0, intensity_log10_sq_nm_mhz)


def log10_sq_nm_mhz_to_log10_cm_per_molecule(intensity_log10_sq_nm_mhz: float) -> float:
    return -10. + intensity_log10_sq_nm_mhz - math.log10(c)


def log10_sq_nm_mhz_to_cm_per_molecule(intensity_log10_sq_nm_mhz: float) -> float:
    return math.pow(10.0, log10_sq_nm_mhz_to_log10_cm_per_molecule(intensity_log10_sq_nm_mhz))


def sq_nm_mhz_to_log10_sq_nm_mhz(intensity_sq_nm_mhz: float) -> float:
    if intensity_sq_nm_mhz == 0.0:
        return -math.inf
    if intensity_sq_nm_mhz < 0.0:
        return math.nan
    return math.log10(intensity_sq_nm_mhz)


def log10_cm_per_molecule_to_log10_sq_nm_mhz(intensity_log10_cm_per_molecule: float) -> float:
    return intensity_log10_cm_per_molecule + 10. + math.log10(c)


def cm_per_molecule_to_log10_sq_nm_mhz(intensity_cm_per_molecule: float) -> float:
    if intensity_cm_per_molecule == 0.0:
        return -math.inf
    if intensity_cm_per_molecule < 0.0:
        return math.nan
    return log10_cm_per_molecule_to_log10_sq_nm_mhz(math.log10(intensity_cm_per_molecule))


def tex_to_html_entity(s: str) -> str:
    r"""
    Change LaTeX entities syntax to HTML one.
    Get ‘\alpha’ to be ‘&alpha;’ and so on. Unknown LaTeX entities do not get replaced.

    :param s: a line to convert
    :return: a line with all LaTeX entities renamed
    """
    word_start: int = -1
    word_started: bool = False
    backslash_found: bool = False
    _i: int = 0
    fixes: dict[str, str] = {
        'neq': '#8800',
    }
    while _i < len(s):
        _c: str = s[_i]
        if word_started and not _c.isalpha():
            word_started = False
            if s[word_start:_i] + ';' in html.entities.entitydefs:
                s = s[:word_start - 1] + '&' + s[word_start:_i] + ';' + s[_i:]
                _i += 2
            elif s[word_start:_i] in fixes:
                s = s[:word_start - 1] + '&' + fixes[s[word_start:_i]] + ';' + s[_i:]
                _i += 2
        if backslash_found and _c.isalpha() and not word_started:
            word_start = _i
            word_started = True
        backslash_found = (_c == '\\')
        _i += 1
    if word_started:
        if s[word_start:_i] + ';' in html.entities.entitydefs:
            s = s[:word_start - 1] + '&' + s[word_start:_i] + ';' + s[_i:]
            _i += 2
        elif s[word_start:_i] in fixes:
            s = s[:word_start - 1] + '&' + fixes[s[word_start:_i]] + ';' + s[_i:]
            _i += 2
    return s


def chem_html(formula: str) -> str:
    """ converts plain text chemical formula into html markup """
    if '<' in formula or '>' in formula:
        # we can not tell whether it's a tag or a mathematical sign
        return formula

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
                s = s[:number_start] + '<sub>' + s[number_start:_i] + '</sub>' + s[_i:]
                _i += 11
            if (cap_alpha_started or low_alpha_started) and _c.isdigit() and not number_started:
                number_start = _i
                number_started = True
            if low_alpha_started:
                cap_alpha_started = False
                low_alpha_started = False
            if cap_alpha_started and _c.islower() or _c == ')':
                low_alpha_started = True
            cap_alpha_started = _c.isupper()
            _i += 1
        if number_started:
            s = s[:number_start] + '<sub>' + s[number_start:] + '</sub>'
        return s

    def prefix(s: str) -> str:
        no_digits: bool = False
        _i: int = len(s)
        while not no_digits:
            _i = s.rfind('-', 0, _i)
            if _i == -1:
                break
            if s[:_i].isalpha() and s[:_i].isupper():
                break
            no_digits = True
            _c: str
            unescaped_prefix: str = html.unescape(s[:_i])
            for _c in unescaped_prefix:
                if _c.isdigit() or _c == '<':
                    no_digits = False
                    break
            if no_digits and (unescaped_prefix[0].islower() or unescaped_prefix[0] == '('):
                return '<i>' + s[:_i] + '</i>' + s[_i:]
        return s

    def charge(s: str) -> str:
        if s[-1] in '+-':
            return s[:-1] + '<sup>' + s[-1] + '</sup>'
        return s

    def v(s: str) -> str:
        if '=' not in s:
            return s[0] + ' = ' + s[1:]
        ss: list[str] = list(map(str.strip, s.split('=')))
        for _i in range(len(ss)):
            if ss[_i].startswith('v'):
                ss[_i] = ss[_i][0] + '<sub>' + ss[_i][1:] + '</sub>'
        return ' = '.join(ss)

    html_formula: str = html.escape(formula)
    html_formula_pieces: list[str] = list(map(str.strip, html_formula.split(',')))
    for i in range(len(html_formula_pieces)):
        if html_formula_pieces[i].startswith('v'):
            html_formula_pieces = html_formula_pieces[:i] + [', '.join(html_formula_pieces[i:])]
            break
    for i in range(len(html_formula_pieces)):
        if html_formula_pieces[i].startswith('v'):
            html_formula_pieces[i] = v(html_formula_pieces[i])
            break
        for function in (subscript, prefix, charge):
            html_formula_pieces[i] = function(html_formula_pieces[i])
    html_formula = ', '.join(html_formula_pieces)
    return html_formula


def is_good_html(text: str) -> bool:
    """ Basic check that all tags are sound """
    _1, _2, _3 = text.count('<'), text.count('>'), 2 * text.count('</')
    return _1 == _2 and _1 == _3


def best_name(entry: dict[str, int | str | list[dict[str, float]]],
              allow_html: bool = True) -> str:
    if allow_html and ISOTOPOLOG in entry and entry[ISOTOPOLOG]:
        if allow_html:
            if (is_good_html(str(entry[MOLECULE_SYMBOL]))
                    and ((STRUCTURAL_FORMULA in entry and entry[STRUCTURAL_FORMULA] == entry[ISOTOPOLOG])
                         or (STOICHIOMETRIC_FORMULA in entry and entry[STOICHIOMETRIC_FORMULA] == entry[ISOTOPOLOG]))):
                if STATE_HTML in entry and entry[STATE_HTML]:
                    # span tags are needed when the molecule symbol is malformed
                    return f'<span>{entry[MOLECULE_SYMBOL]}</span>, ' \
                           f'{chem_html(tex_to_html_entity(str(entry[STATE_HTML])))}'
                return str(entry[MOLECULE_SYMBOL])
            else:
                if STATE_HTML in entry and entry[STATE_HTML]:
                    return f'{chem_html(str(entry[ISOTOPOLOG]))}, ' \
                           f'{chem_html(tex_to_html_entity(str(entry[STATE_HTML])))}'
                return chem_html(str(entry[ISOTOPOLOG]))
        else:
            if STATE_HTML in entry and entry[STATE_HTML]:
                return f'{entry[ISOTOPOLOG]}, {remove_html(tex_to_html_entity(entry[STATE_HTML]))}'
            if STATE in entry and entry[STATE]:
                return f'{entry[ISOTOPOLOG]}, {remove_html(tex_to_html_entity(entry[STATE].strip("$")))}'
            return entry[ISOTOPOLOG]

    for key in (NAME, STRUCTURAL_FORMULA, STOICHIOMETRIC_FORMULA):
        if key in entry and entry[key]:
            return chem_html(str(entry[key])) if allow_html else str(entry[key])
    if TRIVIAL_NAME in entry and entry[TRIVIAL_NAME]:
        return str(entry[TRIVIAL_NAME])
    if SPECIES_TAG in entry and entry[SPECIES_TAG]:
        return str(entry[SPECIES_TAG])
    return 'no name'


def remove_html(line: str) -> str:
    """ removes HTML tags and decodes HTML entities """
    if not is_good_html(line):
        return html.unescape(line)

    new_line: str = line
    tag_start: int = new_line.find('<')
    tag_end: int = new_line.find('>', tag_start)
    while tag_start != -1 and tag_end != -1:
        new_line = new_line[:tag_start] + new_line[tag_end + 1:]
        tag_start = new_line.find('<')
        tag_end = new_line.find('>', tag_start)
    return html.unescape(new_line).lstrip()


def wrap_in_html(text: str, line_end: str = os.linesep) -> str:
    """ Make a full HTML document out of a piece of the markup """
    new_text: list[str] = [
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">',
        '<html lang="en" xml:lang="en">',
        '<head>',
        '<meta http-equiv="content-type" content="text/html; charset=utf-8">',
        '</head>',
        '<body>',
        text,
        '</body>',
        '</html>'
    ]

    return line_end.join(new_text)


def find_qt_core() -> ModuleType | None:
    import importlib

    qt_core = None
    for qt in ('PySide6', 'PyQt6', 'PyQt5', 'PySide2'):
        try:
            qt_core = importlib.import_module(f'{qt}.QtCore')
        except (ImportError, ModuleNotFoundError):
            pass
        else:
            break
    return qt_core


def save_catalog_to_file(saving_path: str | Path,
                         catalog: list[dict[str, int | str | list[dict[str, float]]]],
                         frequency_limits: tuple[float, float]) -> bool:
    saving_path: Path = Path(saving_path)
    data: dict[str, list[dict[str, int | str | list[dict[str, float]]]] | list[float]] = {
        CATALOG: catalog,
        FREQUENCY: list(frequency_limits)
    }
    f: BinaryIO | gzip.GzipFile
    if saving_path.suffix.casefold() == '.json':
        with saving_path.open('wb') as f:
            f.write(json.dumps(data, indent=4).encode())
    elif saving_path.name.casefold().endswith('.json.gz'):
        with gzip.open(saving_path, 'wb') as f:
            f.write(json.dumps(data, indent=4).encode())
    elif saving_path.suffix.casefold() in ('.qb''json', '.qb''js'):
        qt_core: ModuleType | None = find_qt_core()
        if qt_core is None:
            return False
        with saving_path.open('wb') as f:
            f.write(qt_core.QJsonDocument(data).toBinaryData().data())
    elif saving_path.suffix == '.qb''jsz':
        qt_core: ModuleType | None = find_qt_core()
        if qt_core is None:
            return False
        with saving_path.open('wb') as f:
            f.write(qt_core.qCompress(qt_core.QJsonDocument(data).toBinaryData()).data())
    else:
        raise ValueError(f'Do not know what to save into {saving_path}')
    return True
