import os
import sys
from math import e as _e, inf, log10, nan, pow
from numbers import Real
from typing import Any, Callable, Final, Iterable, Literal, Protocol, Sequence, TypeVar, TypedDict, overload

__all__ = [
    "M_LOG10E",
    "T0",
    "c",
    "h",
    "k",
    "e",
    "CATALOG",
    "SPECIES",
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
    "LineType",
    "LinesType",
    "CatalogEntryType",
    "CatalogType",
    "SpeciesJSONEntryType",
    "CatalogJSONEntryType",
    "CatalogJSONType",
    "OldCatalogJSONType",
]

M_LOG10E: Final[float] = log10(_e)

T0: Final[float] = 300.00  # [K], see https://spec.jpl.nasa.gov/ftp/pub/catalog/doc/catdoc.pdf
k: Final[float] = 1.380649000e-23  # [J/K],  see https://physics.nist.gov/cgi-bin/cuu/Value?k
h: Final[float] = 6.626070150e-34  # [J/Hz], see https://physics.nist.gov/cgi-bin/cuu/Value?h
e: Final[float] = 1.602176634e-19  # [C],    see https://physics.nist.gov/cgi-bin/cuu/Value?e
c: Final[float] = 299_792_458.000  # [m/s],  see https://physics.nist.gov/cgi-bin/cuu/Value?c

CATALOG: Literal["catalog"] = "catalog"
SPECIES: Literal["species"] = "species"
BUILD_TIME: Literal["build_time"] = "build_time"
LINES: Literal["lines"] = "lines"
FREQUENCY: Literal["frequency"] = "frequency"
INTENSITY: Literal["intensity"] = "intensity"
ID: Literal["id"] = "id"
MOLECULE: Literal["molecule"] = "molecule"
STRUCTURAL_FORMULA: Literal["structuralformula"] = "structuralformula"
STOICHIOMETRIC_FORMULA: Literal["stoichiometricformula"] = "stoichiometricformula"
MOLECULE_SYMBOL: Literal["moleculesymbol"] = "moleculesymbol"
SPECIES_TAG: Literal["speciestag"] = "speciestag"
NAME: Literal["name"] = "name"
TRIVIAL_NAME: Literal["trivialname"] = "trivialname"
ISOTOPOLOG: Literal["isotopolog"] = "isotopolog"
STATE: Literal["state"] = "state"
STATE_HTML: Literal["state_html"] = "state_html"
INCHI_KEY: Literal["inchikey"] = "inchikey"
CONTRIBUTOR: Literal["contributor"] = "contributor"
VERSION: Literal["version"] = "version"
DATE_OF_ENTRY: Literal["dateofentry"] = "dateofentry"
DEGREES_OF_FREEDOM: Literal["degreesoffreedom"] = "degreesoffreedom"
LOWER_STATE_ENERGY: Literal["lowerstateenergy"] = "lowerstateenergy"

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


class LineType:
    __slots__ = [FREQUENCY, INTENSITY, LOWER_STATE_ENERGY]

    def __init__(
        self,
        frequency: float = nan,
        intensity: float = nan,
        lowerstateenergy: float = nan,
    ) -> None:
        self.frequency: float = frequency
        self.intensity: float = intensity
        self.lowerstateenergy: float = lowerstateenergy


LinesType = list[LineType]


# noinspection PyShadowingBuiltins
class CatalogEntryType:
    __slots__ = [
        ID,
        MOLECULE,
        STRUCTURAL_FORMULA,
        STOICHIOMETRIC_FORMULA,
        MOLECULE_SYMBOL,
        SPECIES_TAG,
        NAME,
        TRIVIAL_NAME,
        ISOTOPOLOG,
        STATE,
        STATE_HTML,
        INCHI_KEY,
        CONTRIBUTOR,
        VERSION,
        DATE_OF_ENTRY,
        DEGREES_OF_FREEDOM,
        LINES,
    ]

    def __init__(
        self,
        id: int = 0,
        molecule: int = 0,
        structuralformula: str = "",
        stoichiometricformula: str = "",
        moleculesymbol: str = "",
        speciestag: int = 0,
        name: str = "",
        trivialname: str = "",
        isotopolog: str = "",
        state: str = "",
        state_html: str = "",
        inchikey: str = "",
        contributor: str = "",
        version: str = "",
        dateofentry: str = "",
        degreesoffreedom: int = -1,
        lines: Iterable[dict[str, float]] = (),
    ) -> None:
        self.id: int = id
        self.molecule: int = molecule
        self.structuralformula: str = structuralformula
        self.stoichiometricformula: str = stoichiometricformula
        self.moleculesymbol: str = moleculesymbol
        self.speciestag: int = speciestag
        self.name: str = name
        self.trivialname: str = trivialname
        self.isotopolog: str = isotopolog
        self.state: str = state
        self.state_html: str = state_html
        self.inchikey: str = inchikey
        self.contributor: str = contributor
        self.version: str = version
        self.dateofentry: str = dateofentry
        self.degreesoffreedom: int = degreesoffreedom
        self.lines: LinesType = [LineType(**line) for line in lines]


class LineJSONType(TypedDict, total=False):
    frequency: float
    intensity: float
    lowerstateenergy: float


class SpeciesJSONEntryType(TypedDict, total=False):
    id: int
    molecule: int
    structuralformula: str
    stoichiometricformula: str
    moleculesymbol: str
    speciestag: int
    name: str
    trivialname: str
    isotopolog: str
    state: str
    state_html: str
    inchikey: str
    contributor: str
    version: str
    dateofentry: str
    degreesoffreedom: int


class CatalogJSONEntryType(SpeciesJSONEntryType, total=False):
    lines: Iterable[LineJSONType]


CatalogType = dict[int, CatalogEntryType]
CatalogJSONType = dict[str, CatalogJSONEntryType]
OldCatalogJSONType = list[CatalogJSONEntryType]


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
    from operator import le, lt

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


def save_catalog_to_file(
    filename: str | os.PathLike[str],
    catalog: CatalogType,
    frequency_limits: tuple[float, float],
) -> bool:
    from .catalog import Catalog

    if not catalog:
        return False
    Catalog.from_data(catalog_data=catalog, frequency_limits=frequency_limits).save(filename=filename)
    return True


if sys.version_info < (3, 10, 0):
    import builtins

    # noinspection PyShadowingBuiltins,PyUnusedLocal
    def zip(*iterables: Iterable[Any], strict: bool = False) -> builtins.zip:
        """Intentionally override `builtins.zip` to ignore `strict` parameter in Python < 3.10"""
        return builtins.zip(*iterables)

    __all__.append("zip")
