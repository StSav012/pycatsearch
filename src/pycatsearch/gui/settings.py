# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import contextmanager, suppress
from os import PathLike, linesep
from pathlib import Path
from typing import Any, Callable, Final, Hashable, Iterable, NamedTuple, Sequence

from qtpy.QtCore import QByteArray, QObject, QSettings

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

    class PathCallbackOnly(NamedTuple):
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
        dict[str, (CallbackOnly | PathCallbackOnly | SpinboxAndCallback | ComboboxAndCallback)],
    ]:
        return {
            (self.tr("When the program starts"), ("mdi6.rocket-launch",)): {
                self.tr("Load catalogs"): Settings.CallbackOnly(Settings.load_last_catalogs.fset.__name__),
                self.tr("Check for update"): Settings.CallbackOnly(Settings.check_updates.fset.__name__),
            },
            (self.tr("Display"), ("mdi6.binoculars",)): {
                self.tr("Allow rich text in formulas"): Settings.CallbackOnly(
                    Settings.rich_text_in_formulas.fset.__name__
                ),
            },
            (self.tr("Units"), ("mdi6.pencil-ruler",)): {
                self.tr("Frequency:"): Settings.ComboboxAndCallback(
                    self.FREQUENCY_UNITS, Settings.frequency_unit.fset.__name__
                ),
                self.tr("Intensity:"): Settings.ComboboxAndCallback(
                    self.INTENSITY_UNITS, Settings.intensity_unit.fset.__name__
                ),
                self.tr("Energy:"): Settings.ComboboxAndCallback(self.ENERGY_UNITS, Settings.energy_unit.fset.__name__),
                self.tr("Temperature:"): Settings.ComboboxAndCallback(
                    self.TEMPERATURE_UNITS, Settings.temperature_unit.fset.__name__
                ),
            },
            (self.tr("Export"), ("mdi6.file-export",)): {
                self.tr("With units"): Settings.CallbackOnly(Settings.with_units.fset.__name__),
                self.tr("Line ending:"): Settings.ComboboxAndCallback(self.LINE_ENDS, Settings.line_end.fset.__name__),
                self.tr("CSV separator:"): Settings.ComboboxAndCallback(
                    self.CSV_SEPARATORS, Settings.csv_separator.fset.__name__
                ),
            },
            (
                self.tr("Info"),
                ("mdi6.flask-empty-outline", "mdi6.information-variant"),
                (("options", ((), (("scale_factor", 0.5),))),),
            ): {
                self.tr("InChI key search URL:"): Settings.EditableComboboxAndCallback(
                    self.INCHI_KEY_SEARCH_PROVIDERS, Settings.inchi_key_search_url_template.fset.__name__
                ),
            },
        }

    @contextmanager
    def section(self, section: str) -> None:
        try:
            self.beginGroup(section)
            yield None
        finally:
            self.endGroup()

    @property
    def frequency_unit(self) -> int:
        with self.section("frequency"):
            return self.value("unit", 0, int)

    @frequency_unit.setter
    def frequency_unit(self, new_value: int | str) -> None:
        if isinstance(new_value, str):
            new_value = self.FREQUENCY_UNITS.index(new_value)
        with self.section("frequency"):
            self.setValue("unit", new_value)

    @property
    def frequency_unit_str(self) -> str:
        with self.section("frequency"):
            return self.FREQUENCY_UNITS[self.value("unit", 0, int)]

    @property
    def to_mhz(self) -> Callable[[float], float]:
        with self.section("frequency"):
            return self.TO_MHZ[self.value("unit", 0, int)]

    @property
    def from_mhz(self) -> Callable[[float], float]:
        with self.section("frequency"):
            return self.FROM_MHZ[self.value("unit", 0, int)]

    @property
    def intensity_unit(self) -> int:
        with self.section("intensity"):
            return self.value("unit", 0, int)

    @intensity_unit.setter
    def intensity_unit(self, new_value: int | str) -> None:
        if isinstance(new_value, str):
            new_value = self.INTENSITY_UNITS.index(new_value)
        with self.section("intensity"):
            self.setValue("unit", new_value)

    @property
    def intensity_unit_str(self) -> str:
        with self.section("intensity"):
            return self.INTENSITY_UNITS[self.value("unit", 0, int)]

    @property
    def to_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        with self.section("intensity"):
            return self.TO_LOG10_SQ_NM_MHZ[self.value("unit", 0, int)]

    @property
    def from_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        with self.section("intensity"):
            return self.FROM_LOG10_SQ_NM_MHZ[self.value("unit", 0, int)]

    @property
    def energy_unit(self) -> int:
        with self.section("energy"):
            return self.value("unit", 0, int)

    @energy_unit.setter
    def energy_unit(self, new_value: int | str) -> None:
        if isinstance(new_value, str):
            new_value = self.ENERGY_UNITS.index(new_value)
        with self.section("energy"):
            self.setValue("unit", new_value)

    @property
    def energy_unit_str(self) -> str:
        with self.section("energy"):
            return self.ENERGY_UNITS[self.value("unit", 0, int)]

    @property
    def to_rec_cm(self) -> Callable[[float], float]:
        with self.section("energy"):
            return self.TO_REC_CM[self.value("unit", 0, int)]

    @property
    def from_rec_cm(self) -> Callable[[float], float]:
        with self.section("energy"):
            return self.FROM_REC_CM[self.value("unit", 0, int)]

    @property
    def temperature_unit(self) -> int:
        with self.section("temperature"):
            return self.value("unit", 0, int)

    @temperature_unit.setter
    def temperature_unit(self, new_value: int | str) -> None:
        if isinstance(new_value, str):
            new_value = self.TEMPERATURE_UNITS.index(new_value)
        with self.section("temperature"):
            self.setValue("unit", new_value)

    @property
    def temperature_unit_str(self) -> str:
        with self.section("temperature"):
            return self.TEMPERATURE_UNITS[self.value("unit", 0, int)]

    @property
    def to_k(self) -> Callable[[float], float]:
        with self.section("temperature"):
            return self.TO_K[self.value("unit", 0, int)]

    @property
    def from_k(self) -> Callable[[float], float]:
        with self.section("temperature"):
            return self.FROM_K[self.value("unit", 0, int)]

    @property
    def load_last_catalogs(self) -> bool:
        with self.section("start"):
            return self.value("loadLastCatalogs", True, bool)

    @load_last_catalogs.setter
    def load_last_catalogs(self, new_value: bool) -> None:
        with self.section("start"):
            self.setValue("loadLastCatalogs", new_value)

    @property
    def check_updates(self) -> bool:
        with self.section("start"):
            return self.value("checkUpdates", True, bool)

    @check_updates.setter
    def check_updates(self, new_value: bool) -> None:
        with self.section("start"):
            self.setValue("checkUpdates", new_value)

    @property
    def rich_text_in_formulas(self) -> bool:
        with self.section("display"):
            return self.value("richTextInFormulas", True, bool)

    @rich_text_in_formulas.setter
    def rich_text_in_formulas(self, new_value: bool) -> None:
        with self.section("display"):
            self.setValue("richTextInFormulas", new_value)

    @property
    def line_end(self) -> str:
        with self.section("export"):
            return list(self.LINE_ENDS.keys())[self.value("lineEnd", list(self.LINE_ENDS.keys()).index(linesep), int)]

    @line_end.setter
    def line_end(self, new_value: str) -> None:
        with self.section("export"):
            self.setValue("lineEnd", list(self.LINE_ENDS.keys()).index(new_value))

    @property
    def csv_separator(self) -> str:
        with self.section("export"):
            return list(self.CSV_SEPARATORS.keys())[
                self.value("csvSeparator", list(self.CSV_SEPARATORS.keys()).index("\t"), int)
            ]

    @csv_separator.setter
    def csv_separator(self, new_value: str) -> None:
        with self.section("export"):
            self.setValue("csvSeparator", list(self.CSV_SEPARATORS.keys()).index(new_value))

    @property
    def with_units(self) -> bool:
        with self.section("export"):
            return self.value("withUnits", True, bool)

    @with_units.setter
    def with_units(self, new_value: bool) -> None:
        with self.section("export"):
            self.setValue("withUnits", new_value)

    @property
    def ignored_version(self) -> str:
        with self.section("update"):
            return self.value("ignoredVersion", "", str)

    @ignored_version.setter
    def ignored_version(self, new_value: str) -> None:
        with self.section("update"):
            self.setValue("ignoredVersion", new_value)

    @property
    def inchi_key_search_url_template(self) -> str:
        with self.section("info"):
            return self.value("InChIKeySearchURLTemplate", "https://pubchem.ncbi.nlm.nih.gov/#query={InChIKey}", str)

    @inchi_key_search_url_template.setter
    def inchi_key_search_url_template(self, new_value: str) -> None:
        with self.section("info"):
            self.setValue("InChIKeySearchURLTemplate", new_value)

    @property
    def catalog_file_names(self) -> list[str | PathLike[str]]:
        catalog_file_names: list[str] = []
        with self.section("search"):
            for i in range(self.beginReadArray("catalogFiles")):
                self.setArrayIndex(i)
                path: str = self.value("path", "", str)
                if path:
                    catalog_file_names.append(path)
            self.endArray()
        return catalog_file_names or ["catalog.json.gz", "catalog.json"]

    @catalog_file_names.setter
    def catalog_file_names(self, filenames: Iterable[str | PathLike[str]]) -> None:
        with self.section("search"):
            self.beginWriteArray("catalogFiles")
            for i, s in enumerate(filenames):
                self.setArrayIndex(i)
                self.setValue("path", str(s))
            self.endArray()

    @property
    def translation_path(self) -> Path | None:
        with self.section("translation"):
            v: str = self.value("filePath", "", str)
        return Path(v) if v else None

    @translation_path.setter
    def translation_path(self, new_value: str | PathLike[str] | None) -> None:
        with self.section("translation"):
            self.setValue("filePath", str(new_value or ""))

    @property
    def opened_file_name(self) -> Path | None:
        with self.section("location"):
            v: str = self.value("open", "", str)
        return Path(v) if v else None

    @opened_file_name.setter
    def opened_file_name(self, filename: str | PathLike[str] | None) -> None:
        with self.section("location"):
            self.setValue("open", str(filename or ""))

    @property
    def saved_file_name(self) -> Path | None:
        with self.section("location"):
            v: str = self.value("save", "", str)
        return Path(v) if v else None

    @saved_file_name.setter
    def saved_file_name(self, filename: str | PathLike[str] | None) -> None:
        with self.section("location"):
            self.setValue("save", str(filename or ""))

    def save(self, o: QObject) -> None:
        name: str = o.objectName()
        if not name:
            raise AttributeError(f"No name given for {o}")
        with suppress(AttributeError), self.section("state"):
            # noinspection PyUnresolvedReferences
            self.setValue(name, o.saveState())
        with suppress(AttributeError), self.section("geometry"):
            # noinspection PyUnresolvedReferences
            self.setValue(name, o.saveGeometry())

    def restore(self, o: QObject) -> None:
        name: str = o.objectName()
        if not name:
            raise AttributeError(f"No name given for {o}")
        with suppress(AttributeError), self.section("state"):
            # noinspection PyUnresolvedReferences
            o.restoreState(self.value(name, QByteArray()))
        with suppress(AttributeError), self.section("geometry"):
            # noinspection PyUnresolvedReferences
            o.restoreGeometry(self.value(name, QByteArray()))
