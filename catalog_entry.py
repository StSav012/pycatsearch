# -*- coding: utf-8 -*-
import math

from utils import *


class CatalogEntry:
    def __init__(self, spcat_line: str = '', *, frequency: float = math.nan, intensity: float = math.nan,
                 degrees_of_freedom: int = -1, lower_state_energy: float = math.nan):
        self.FREQ: float  # frequency, MHz, mandatory
        self.INT: float  # intensity, log10(nm²×MHz), mandatory
        self.DR: int  # degrees of freedom: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
        self.ELO: float  # lower state energy relative to the ground state, 1/cm
        self.FREQ = frequency
        self.INT = intensity
        self.DR = degrees_of_freedom
        self.ELO = lower_state_energy
        if spcat_line:
            # FREQ         ERR     LGINT   DR ELO      GUP TAG   QNFMT QN'       QN"
            # F13     .4   F8 .4   F8 .4   I2F10  .4,  I3 I7     I4  6I2         6I2
            # FFFFFFFF.FFFFEEE.EEEE-II.IIIIDDEEEEE.EEEEGGG+TTTTTTQQQQ112233445566112233445566
            #      262.0870  0.0011-19.2529 2 5174.7303  4  180011335 1-132 2 2   1 132 2 3
            self.FREQ = float(spcat_line[:13])
            self.INT = float(spcat_line[21:29])
            self.DR = int(spcat_line[29:31])
            self.ELO = float(spcat_line[31:41])

    @property
    def frequency(self) -> float:
        return self.FREQ

    def intensity(self, temperature: float = -math.inf) -> float:
        if self.DR >= 0 and temperature > 0. and temperature != T0:
            return self.INT + (0.5 * self.DR + 1.0) * math.log10(T0 / temperature) + (
                    -(1 / temperature - 1 / T0) * self.ELO * 100. * h * c / k) * M_LOG10E
        else:
            return self.INT

    @property
    def degrees_of_freedom(self) -> int:
        return self.DR

    @property
    def lower_state_energy(self) -> float:
        return self.ELO

    def to_dict(self):
        return {'frequency': self.FREQ, 'intensity': self.INT, 'lowerstateenergy': self.ELO}

    def __repr__(self):
        return f'{self.FREQ} {self.INT} {self.ELO}'
