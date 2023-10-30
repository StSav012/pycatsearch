# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Callable, Final, Hashable, Iterable, NamedTuple, Sequence

from qtpy.QtCore import QObject, QSettings

from ..utils import (
    cm_per_molecule_to_log10_sq_nm_mhz,
    ghz_to_mhz,
    j_to_rec_cm,
    log10_cm_per_molecule_to_log10_sq_nm_mhz,
    log10_sq_nm_mhz_to_cm_per_molecule,
    log10_sq_nm_mhz_to_log10_cm_per_molecule,
    log10_sq_nm_mhz_to_sq_nm_mhz,
    meV_to_rec_cm,
    mhz_to_ghz,
    mhz_to_nm,
    mhz_to_rec_cm,
    nm_to_mhz,
    rec_cm_to_j,
    rec_cm_to_meV,
    rec_cm_to_mhz,
    sq_nm_mhz_to_log10_sq_nm_mhz,
)

__all__ = ["Settings"]


class Settings(QSettings):
    """convenient internal representation of the application settings"""

    class CallbackOnly(NamedTuple):
        callback: str

    class SpinboxAndCallback(NamedTuple):
        range: slice
        prefix_and_suffix: tuple[str, str]
        callback: str

    class ComboboxAndCallback(NamedTuple):
        combobox_data: Iterable[str] | dict[Hashable, str]
        callback: str

    class EditableComboboxAndCallback(NamedTuple):
        combobox_items: Sequence[str]
        callback: str

    TO_MHZ: Final[list[Callable[[float], float]]] = [lambda x: x, ghz_to_mhz, rec_cm_to_mhz, nm_to_mhz]
    FROM_MHZ: Final[list[Callable[[float], float]]] = [lambda x: x, mhz_to_ghz, mhz_to_rec_cm, mhz_to_nm]

    TO_LOG10_SQ_NM_MHZ: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        sq_nm_mhz_to_log10_sq_nm_mhz,
        log10_cm_per_molecule_to_log10_sq_nm_mhz,
        cm_per_molecule_to_log10_sq_nm_mhz,
    ]
    FROM_LOG10_SQ_NM_MHZ: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        log10_sq_nm_mhz_to_sq_nm_mhz,
        log10_sq_nm_mhz_to_log10_cm_per_molecule,
        log10_sq_nm_mhz_to_cm_per_molecule,
    ]

    TO_REC_CM: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        meV_to_rec_cm,
        j_to_rec_cm,
    ]
    FROM_REC_CM: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        rec_cm_to_meV,
        rec_cm_to_j,
    ]

    TO_K: Final[list[Callable[[float], float]]] = [lambda x: x, lambda x: x + 273.15]
    FROM_K: Final[list[Callable[[float], float]]] = [lambda x: x, lambda x: x - 273.15]

    INCHI_KEY_SEARCH_PROVIDERS: Final[list[str]] = [
        "https://pubchem.ncbi.nlm.nih.gov/#query={InChIKey}",
        "https://www.ebi.ac.uk/unichem/compoundsources?type=inchikey&compound={InChIKey}",
        "https://webbook.nist.gov/cgi/cbook.cgi?InChI={InChIKey}",
        "https://www.spectrabase.com/search?q={InChIKey}",
        "https://www.google.com/search?q={InChIKey}",
        "http://gmd.mpimp-golm.mpg.de/search.aspx?query={InChIKey}",
        "http://www.chemspider.com/InChIKey/{InChIKey}",
    ]

    def __init__(self, organization: str, application: str, parent: QObject | None = None) -> None:
        super().__init__(organization, application, parent)

        # for some reason, the dicts are not being translated when used as class variables
        self.LINE_ENDS: Final[dict[str, str]] = {
            "\n": self.tr(r"Line Feed (\n)"),
            "\r": self.tr(r"Carriage Return (\r)"),
            "\r\n": self.tr(r"CR+LF (\r\n)"),
            "\n\r": self.tr(r"LF+CR (\n\r)"),
        }
        self.CSV_SEPARATORS: Final[dict[str, str]] = {
            ",": self.tr(r"comma (,)"),
            "\t": self.tr(r"tab (\t)"),
            ";": self.tr(r"semicolon (;)"),
            " ": self.tr(r"space ( )"),
        }
        self.FREQUENCY_UNITS: Final[list[str]] = [self.tr("MHz"), self.tr("GHz"), self.tr("cm⁻¹"), self.tr("nm")]
        self.INTENSITY_UNITS: Final[list[str]] = [
            self.tr("lg(nm² × MHz)"),
            self.tr("nm² × MHz"),
            self.tr("lg(cm / molecule)"),
            self.tr("cm / molecule"),
        ]
        self.ENERGY_UNITS: Final[list[str]] = [self.tr("cm⁻¹"), self.tr("meV"), self.tr("J")]
        self.TEMPERATURE_UNITS: Final[list[str]] = [self.tr("K"), self.tr("°C")]

    @property
    def dialog(
        self,
    ) -> dict[
        (str | tuple[str, tuple[str, ...]] | tuple[str, tuple[str, ...], tuple[tuple[str, Any], ...]]),
        dict[str, (CallbackOnly | SpinboxAndCallback | ComboboxAndCallback)],
    ]:
        return {
            (self.tr("When the program starts"), ("mdi6.rocket-launch",)): {
                self.tr("Load catalogs"): Settings.CallbackOnly("load_last_catalogs"),
                self.tr("Check for update"): Settings.CallbackOnly("check_updates"),
            },
            (self.tr("Display"), ("mdi6.binoculars",)): {
                self.tr("Allow rich text in formulas"): Settings.CallbackOnly("rich_text_in_formulas"),
            },
            (self.tr("Units"), ("mdi6.pencil-ruler",)): {
                self.tr("Frequency:"): Settings.ComboboxAndCallback(self.FREQUENCY_UNITS, "frequency_unit"),
                self.tr("Intensity:"): Settings.ComboboxAndCallback(self.INTENSITY_UNITS, "intensity_unit"),
                self.tr("Energy:"): Settings.ComboboxAndCallback(self.ENERGY_UNITS, "energy_unit"),
                self.tr("Temperature:"): Settings.ComboboxAndCallback(self.TEMPERATURE_UNITS, "temperature_unit"),
            },
            (self.tr("Export"), ("mdi6.file-export",)): {
                self.tr("With units"): Settings.CallbackOnly("with_units"),
                self.tr("Line ending:"): Settings.ComboboxAndCallback(self.LINE_ENDS, "line_end"),
                self.tr("CSV separator:"): Settings.ComboboxAndCallback(self.CSV_SEPARATORS, "csv_separator"),
            },
            (
                self.tr("Info"),
                ("mdi6.flask-empty-outline", "mdi6.information-variant"),
                (("options", ((), (("scale_factor", 0.5),))),),
            ): {
                self.tr("InChI key search URL:"): Settings.EditableComboboxAndCallback(
                    self.INCHI_KEY_SEARCH_PROVIDERS, "inchi_key_search_url_template"
                ),
            },
        }

    @property
    def frequency_unit(self) -> int:
        self.beginGroup("frequency")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return v

    @frequency_unit.setter
    def frequency_unit(self, new_value: int | str) -> None:
        self.beginGroup("frequency")
        if isinstance(new_value, str):
            new_value = self.FREQUENCY_UNITS.index(new_value)
        self.setValue("unit", new_value)
        self.endGroup()

    @property
    def frequency_unit_str(self) -> str:
        self.beginGroup("frequency")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.FREQUENCY_UNITS[v]

    @property
    def to_mhz(self) -> Callable[[float], float]:
        self.beginGroup("frequency")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.TO_MHZ[v]

    @property
    def from_mhz(self) -> Callable[[float], float]:
        self.beginGroup("frequency")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.FROM_MHZ[v]

    @property
    def intensity_unit(self) -> int:
        self.beginGroup("intensity")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return v

    @intensity_unit.setter
    def intensity_unit(self, new_value: int | str) -> None:
        self.beginGroup("intensity")
        if isinstance(new_value, str):
            new_value = self.INTENSITY_UNITS.index(new_value)
        self.setValue("unit", new_value)
        self.endGroup()

    @property
    def intensity_unit_str(self) -> str:
        self.beginGroup("intensity")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.INTENSITY_UNITS[v]

    @property
    def to_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        self.beginGroup("intensity")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.TO_LOG10_SQ_NM_MHZ[v]

    @property
    def from_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        self.beginGroup("intensity")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.FROM_LOG10_SQ_NM_MHZ[v]

    @property
    def energy_unit(self) -> int:
        self.beginGroup("energy")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return v

    @energy_unit.setter
    def energy_unit(self, new_value: int | str) -> None:
        self.beginGroup("energy")
        if isinstance(new_value, str):
            new_value = self.ENERGY_UNITS.index(new_value)
        self.setValue("unit", new_value)
        self.endGroup()

    @property
    def energy_unit_str(self) -> str:
        self.beginGroup("energy")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.ENERGY_UNITS[v]

    @property
    def to_rec_cm(self) -> Callable[[float], float]:
        self.beginGroup("energy")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.TO_REC_CM[v]

    @property
    def from_rec_cm(self) -> Callable[[float], float]:
        self.beginGroup("energy")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.FROM_REC_CM[v]

    @property
    def temperature_unit(self) -> int:
        self.beginGroup("temperature")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return v

    @temperature_unit.setter
    def temperature_unit(self, new_value: int | str) -> None:
        self.beginGroup("temperature")
        if isinstance(new_value, str):
            new_value = self.TEMPERATURE_UNITS.index(new_value)
        self.setValue("unit", new_value)
        self.endGroup()

    @property
    def temperature_unit_str(self) -> str:
        self.beginGroup("temperature")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.TEMPERATURE_UNITS[v]

    @property
    def to_k(self) -> Callable[[float], float]:
        self.beginGroup("temperature")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.TO_K[v]

    @property
    def from_k(self) -> Callable[[float], float]:
        self.beginGroup("temperature")
        v: int = self.value("unit", 0, int)
        self.endGroup()
        return self.FROM_K[v]

    @property
    def load_last_catalogs(self) -> bool:
        self.beginGroup("start")
        v: bool = self.value("loadLastCatalogs", True, bool)
        self.endGroup()
        return v

    @load_last_catalogs.setter
    def load_last_catalogs(self, new_value: bool) -> None:
        self.beginGroup("start")
        self.setValue("loadLastCatalogs", new_value)
        self.endGroup()

    @property
    def check_updates(self) -> bool:
        self.beginGroup("start")
        v: bool = self.value("checkUpdates", True, bool)
        self.endGroup()
        return v

    @check_updates.setter
    def check_updates(self, new_value: bool) -> None:
        self.beginGroup("start")
        self.setValue("checkUpdates", new_value)
        self.endGroup()

    @property
    def rich_text_in_formulas(self) -> bool:
        self.beginGroup("display")
        v: bool = self.value("richTextInFormulas", True, bool)
        self.endGroup()
        return v

    @rich_text_in_formulas.setter
    def rich_text_in_formulas(self, new_value: bool) -> None:
        self.beginGroup("display")
        self.setValue("richTextInFormulas", new_value)
        self.endGroup()

    @property
    def line_end(self) -> str:
        self.beginGroup("export")
        v: int = self.value("lineEnd", list(self.LINE_ENDS.keys()).index(os.linesep), int)
        self.endGroup()
        return list(self.LINE_ENDS.keys())[v]

    @line_end.setter
    def line_end(self, new_value: str) -> None:
        self.beginGroup("export")
        self.setValue("lineEnd", list(self.LINE_ENDS.keys()).index(new_value))
        self.endGroup()

    @property
    def csv_separator(self) -> str:
        self.beginGroup("export")
        v: int = self.value("csvSeparator", list(self.CSV_SEPARATORS.keys()).index("\t"), int)
        self.endGroup()
        return list(self.CSV_SEPARATORS.keys())[v]

    @csv_separator.setter
    def csv_separator(self, new_value: str) -> None:
        self.beginGroup("export")
        self.setValue("csvSeparator", list(self.CSV_SEPARATORS.keys()).index(new_value))
        self.endGroup()

    @property
    def with_units(self) -> bool:
        self.beginGroup("export")
        v: bool = self.value("withUnits", True, bool)
        self.endGroup()
        return v

    @with_units.setter
    def with_units(self, new_value: bool) -> None:
        self.beginGroup("export")
        self.setValue("withUnits", new_value)
        self.endGroup()

    @property
    def ignored_version(self) -> str:
        self.beginGroup("update")
        v: str = self.value("ignoredVersion", "", str)
        self.endGroup()
        return v

    @ignored_version.setter
    def ignored_version(self, new_value: str) -> None:
        self.beginGroup("update")
        self.setValue("ignoredVersion", new_value)
        self.endGroup()

    @property
    def inchi_key_search_url_template(self) -> str:
        self.beginGroup("info")
        v: str = self.value("InChIKeySearchURLTemplate", "https://pubchem.ncbi.nlm.nih.gov/#query={InChIKey}", str)
        self.endGroup()
        return v

    @inchi_key_search_url_template.setter
    def inchi_key_search_url_template(self, new_value: str) -> None:
        self.beginGroup("info")
        self.setValue("InChIKeySearchURLTemplate", new_value)
        self.endGroup()
