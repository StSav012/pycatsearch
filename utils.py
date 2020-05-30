# -*- coding: utf-8 -*-
import math
from typing import Tuple, Union, Type

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item
    Final = _Final()


__all__ = ['M_LOG10E',
           'T0', 'c', 'h', 'k',
           'CATALOG', 'LINES', 'FREQUENCY', 'INTENSITY', 'STRUCTURAL_FORMULA', 'STOICHIOMETRIC_FORMULA',
           'MOLECULE_SYMBOL', 'SPECIES_TAG', 'NAME', 'TRIVIAL_NAME', 'ISOTOPOLOG', 'STATE', 'STATE_HTML',
           'INCHI_KEY', 'DEGREES_OF_FREEDOM', 'LOWER_STATE_ENERGY',
           'cm_per_molecule_to_sq_nm_mhz',
           'ghz_to_mhz', 'ghz_to_nm', 'ghz_to_rev_cm',
           'mhz_to_ghz', 'mhz_to_nm', 'mhz_to_rev_cm',
           'nm_to_ghz', 'nm_to_mhz', 'nm_to_rev_cm',
           'rev_cm_to_ghz', 'rev_cm_to_mhz', 'rev_cm_to_nm',
           'sq_nm_mhz_to_cm_per_molecule',
           'within']

M_LOG10E: Final[float] = math.log10(math.e)

T0: Final[float] = 300.00
k: Final[float] = 1.38064900e-23  # https://physics.nist.gov/cgi-bin/cuu/Value?k
h: Final[float] = 6.62607015e-34  # https://physics.nist.gov/cgi-bin/cuu/Value?h
c: Final[float] = 299792458.0000  # https://physics.nist.gov/cgi-bin/cuu/Value?c

CATALOG: Final[str] = 'catalog'
LINES: Final[str] = 'lines'
FREQUENCY: Final[str] = 'frequency'
INTENSITY: Final[str] = 'intensity'
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
DEGREES_OF_FREEDOM: Final[str] = 'degreesoffreedom'
LOWER_STATE_ENERGY: Final[str] = 'lowerstateenergy'


def within(x: float, limits: Union[Tuple[float, float], Tuple[Tuple[float, float], ...]]) -> bool:
    if len(limits) < 2:
        raise ValueError('Invalid limits')
    if isinstance(limits[0], float):
        return min(limits) <= x <= max(limits)
    elif isinstance(limits[0], tuple):
        return any(min(limit) <= x <= max(limit) for limit in limits)
    else:
        raise TypeError('Invalid limits type')


def mhz_to_ghz(frequency_mhz: float) -> float:
    return frequency_mhz * 1e-3


def mhz_to_rev_cm(frequency_mhz: float) -> float:
    return frequency_mhz * 1e4 / c


def mhz_to_nm(frequency_mhz: float) -> float:
    return c / frequency_mhz * 1e3


def ghz_to_mhz(frequency_ghz: float) -> float:
    return frequency_ghz * 1e3


def ghz_to_rev_cm(frequency_ghz: float) -> float:
    return frequency_ghz * 1e7 / c


def ghz_to_nm(frequency_ghz: float) -> float:
    return c / frequency_ghz


def rev_cm_to_mhz(frequency_rev_cm: float) -> float:
    return frequency_rev_cm * 1e-4 * c


def rev_cm_to_ghz(frequency_rev_cm: float) -> float:
    return frequency_rev_cm * 1e-7 * c


def rev_cm_to_nm(frequency_rev_cm: float) -> float:
    return 1e7 / frequency_rev_cm


def nm_to_mhz(frequency_nm: float) -> float:
    return c / frequency_nm * 1e-3


def nm_to_ghz(frequency_nm: float) -> float:
    return c / frequency_nm


def nm_to_rev_cm(frequency_nm: float) -> float:
    return 1e7 / frequency_nm


def sq_nm_mhz_to_cm_per_molecule(intensity_sq_nm_mhz: float) -> float:
    return -10. + intensity_sq_nm_mhz - math.log(c) / M_LOG10E


def cm_per_molecule_to_sq_nm_mhz(intensity_cm_per_molecule: float) -> float:
    return intensity_cm_per_molecule + 10. + math.log(c) / M_LOG10E
