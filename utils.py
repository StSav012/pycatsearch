# -*- coding: utf-8 -*-

import math

M_LOG10E = math.log10(math.e)

T0 = 300.00
k = 1.380649e-23
h = 6.62607015e-34
c = 299792458.


def mhz2_ghz(frequency_mhz: float) -> float:
    return frequency_mhz * 1e-3


def mhz2rev_cm(frequency_mhz: float) -> float:
    return frequency_mhz * 1e4 / c


def mhz2nm(frequency_mhz: float) -> float:
    return c / frequency_mhz * 1e3


def ghz2_mhz(frequency_ghz: float) -> float:
    return frequency_ghz * 1e3


def ghz2rev_cm(frequency_ghz: float) -> float:
    return frequency_ghz * 1e7 / c


def ghz2nm(frequency_ghz: float) -> float:
    return c / frequency_ghz


def rev_cm2mhz(frequency_rev_cm: float) -> float:
    return frequency_rev_cm * 1e-4 * c


def rev_cm2ghz(frequency_rev_cm: float) -> float:
    return frequency_rev_cm * 1e-7 * c


def rev_cm2nm(frequency_rev_cm: float) -> float:
    return 1e7 / frequency_rev_cm


def nm2_mhz(frequency_nm: float) -> float:
    return c / frequency_nm * 1e-3


def nm2_ghz(frequency_nm: float) -> float:
    return c / frequency_nm


def nm2rev_cm(frequency_nm: float) -> float:
    return 1e7 / frequency_nm


def sq_nm_mhz2cm_per_molecule(intensity_sq_nm_mhz: float) -> float:
    return -10. + intensity_sq_nm_mhz - math.log(c) / M_LOG10E


def cm_per_molecule2sq_nm_mhz(intensity_cm_per_molecule: float) -> float:
    return intensity_cm_per_molecule + 10. + math.log(c) / M_LOG10E
