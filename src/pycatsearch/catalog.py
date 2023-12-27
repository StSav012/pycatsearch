# -*- coding: utf-8 -*-
from __future__ import annotations

import bz2
import gzip
import lzma
import math
from contextlib import contextmanager
from datetime import datetime, timezone
from os import PathLike, fsync
from pathlib import Path
from typing import AnyStr, BinaryIO, Callable, Dict, Iterable, List, NamedTuple, TextIO, Union, cast

try:
    import orjson as json
except ImportError:
    import json

from .utils import (
    M_LOG10E,
    T0,
    c,
    h,
    k,
    CATALOG,
    BUILD_TIME,
    LINES,
    FREQUENCY,
    INTENSITY,
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
    DEGREES_OF_FREEDOM,
    LOWER_STATE_ENERGY,
    merge_sorted,
    search_sorted,
)

__all__ = ["Catalog", "CatalogSourceInfo", "LineType", "LinesType", "CatalogEntryType", "CatalogType"]

LineType = Dict[str, float]
LinesType = List[LineType]
CatalogEntryType = Dict[str, Union[int, str, LinesType]]
CatalogType = Dict[int, CatalogEntryType]
CatalogJSONType = Dict[str, CatalogEntryType]
OldCatalogJSONType = List[CatalogEntryType]


def filter_by_frequency_and_intensity(
    catalog_entry: CatalogEntryType,
    *,
    min_frequency: float = 0.0,
    max_frequency: float = math.inf,
    min_intensity: float = -math.inf,
    max_intensity: float = math.inf,
    temperature: float = -math.inf,
) -> CatalogEntryType:
    def intensity(_line: LineType) -> float:
        if catalog_entry[DEGREES_OF_FREEDOM] >= 0 and temperature > 0.0 and temperature != T0:
            return (
                _line[INTENSITY]
                + (
                    (0.5 * catalog_entry[DEGREES_OF_FREEDOM] + 1.0) * math.log(T0 / temperature)
                    - ((1 / temperature - 1 / T0) * _line[LOWER_STATE_ENERGY] * 100.0 * h * c / k)
                )
                / M_LOG10E
            )
        else:
            return _line[INTENSITY]

    new_catalog_entry: CatalogEntryType = catalog_entry.copy()
    if LINES in new_catalog_entry and new_catalog_entry[LINES]:
        min_frequency_index: int = (
            search_sorted(min_frequency, new_catalog_entry[LINES], key=lambda line: line[FREQUENCY]) + 1
        )
        max_frequency_index: int = search_sorted(
            max_frequency, new_catalog_entry[LINES], key=lambda line: line[FREQUENCY], maybe_equal=True
        )
        new_catalog_entry[LINES] = [
            line
            for line in new_catalog_entry[LINES][min_frequency_index : (max_frequency_index + 1)]
            if min_intensity <= intensity(line) <= max_intensity
        ]
    else:
        new_catalog_entry[LINES] = []
    return new_catalog_entry


class CatalogSourceInfo(NamedTuple):
    filename: Path
    build_datetime: datetime | None = None


class CatalogData:
    def __init__(self) -> None:
        self.catalog: CatalogType = dict()
        self.frequency_limits: tuple[tuple[float, float], ...] = ()

    def append(self, new_catalog: CatalogJSONType | OldCatalogJSONType, frequency_limits: tuple[float, float]) -> None:
        catalog: CatalogType
        if isinstance(new_catalog, list):
            catalog = dict((entry[SPECIES_TAG], entry) for entry in new_catalog)
        elif isinstance(new_catalog, dict):
            catalog = dict((int(species_tag_str), new_catalog[species_tag_str]) for species_tag_str in new_catalog)
        else:
            raise TypeError("Unsupported data type")

        def squash_same_species_tag_entries() -> None:
            self.catalog[species_tag][LINES] = cast(
                LinesType,
                merge_sorted(
                    self.catalog[species_tag][LINES],
                    catalog[species_tag][LINES],
                    key=lambda line: (line[FREQUENCY], line[INTENSITY], line[LOWER_STATE_ENERGY]),
                ),
            )

        def merge_frequency_tuples(*args: tuple[float, float] | list[float]) -> tuple[tuple[float, float], ...]:
            if not args:
                return tuple()
            ranges: tuple[tuple[float, float], ...] = tuple()
            skip: int = 0
            for i in range(len(args)):
                if skip > 0:
                    skip -= 1
                    continue
                current_range: tuple[float, float] = (float(args[i][0]), float(args[i][-1]))
                current_min: float = min(current_range)
                current_max: float = max(current_range)
                for r in args[1 + i :]:
                    if current_min <= min(r) <= current_max:
                        current_max = max(current_max, *r)
                        skip += 1
                ranges += ((current_min, current_max),)
            return ranges

        if not self.catalog:
            self.catalog = catalog.copy()
        else:
            species_tag: int
            for species_tag in catalog:
                if species_tag not in self.catalog:
                    self.catalog[species_tag] = catalog[species_tag]
                else:
                    squash_same_species_tag_entries()
        self.frequency_limits = merge_frequency_tuples(*self.frequency_limits, frequency_limits)


class Catalog:
    DEFAULT_SUFFIX: str = ".json.gz"

    class Opener:
        OPENERS_BY_SUFFIX: dict[str, Callable] = {
            ".json": open,
            ".json.gz": gzip.open,
            ".json.bz2": bz2.open,
            ".json.xz": lzma.open,
            ".json.lzma": lzma.open,
        }

        OPENERS_BY_SIGNATURE: dict[str, Callable] = {
            b"{": open,
            b"\x1F\x8B": gzip.open,
            b"BZh": bz2.open,
            b"\xFD\x37\x7A\x58\x5A\x00": lzma.open,
        }

        def __init__(self, path: str | PathLike[str]) -> None:
            self._path: Path = Path(path)
            self._opener: Callable
            suffix: str = ""
            s: str
            for s in reversed(self._path.suffixes):
                suffix = s + suffix
                if suffix in Catalog.Opener.OPENERS_BY_SUFFIX:
                    self._opener = Catalog.Opener.OPENERS_BY_SUFFIX[suffix]
                    return
            if self._path.exists():
                max_signature_length: int = max(map(len, Catalog.Opener.OPENERS_BY_SIGNATURE.keys()))
                f: BinaryIO
                with self._path.open("rb") as f:
                    init_bytes: bytes = f.read(max_signature_length)
                key: bytes
                value: Callable
                for key, value in Catalog.Opener.OPENERS_BY_SIGNATURE.items():
                    if init_bytes.startswith(key):
                        self._opener = value
                        return

            raise ValueError(f"Unknown file: {path}")

        @contextmanager
        def open(
            self, mode: str, encoding: str | None = None, errors: str | None = None, newline: str | None = None
        ) -> TextIO | BinaryIO:
            """
            Open a file in a safe way. Create a temporary file when writing.

            See https://stackoverflow.com/a/29491523/8554611, https://stackoverflow.com/a/2333979/8554611
            """
            writing: bool = "w" in mode.casefold()
            if encoding is None and "b" not in mode.casefold():
                encoding = "utf-8"
            tmp_path: Path = self._path.with_name(self._path.name + ".part")
            file: TextIO | BinaryIO
            with self._opener(
                tmp_path if writing else self._path, mode=mode, encoding=encoding, errors=errors, newline=newline
            ) as file:
                try:
                    yield file
                finally:
                    if writing:
                        file.flush()
                        fsync(file.fileno())
                        tmp_path.replace(self._path)

    def __init__(self, *catalog_file_names: str | PathLike[str]) -> None:
        self._data: CatalogData = CatalogData()
        self._sources: list[CatalogSourceInfo] = []

        filename: Path
        for filename in map(Path, catalog_file_names):
            if filename.exists() and filename.is_file():
                f_in: BinaryIO
                with Catalog.Opener(filename).open("rb") as f_in:
                    content: bytes = f_in.read()
                    try:
                        json_data: dict[str, list[float | None] | CatalogJSONType | OldCatalogJSONType] = json.loads(
                            content
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                    else:
                        self._data.append(
                            new_catalog=json_data[CATALOG],
                            frequency_limits=(
                                json_data[FREQUENCY][0],
                                (math.inf if json_data[FREQUENCY][1] is None else json_data[FREQUENCY][1]),
                            ),
                        )
                        build_datetime: datetime | None = None
                        if BUILD_TIME in json_data:
                            build_datetime = datetime.fromisoformat(cast(str, json_data[BUILD_TIME]))
                        self._sources.append(CatalogSourceInfo(filename=filename, build_datetime=build_datetime))

    def __bool__(self) -> bool:
        return bool(self._data.catalog)

    @property
    def is_empty(self) -> bool:
        return not bool(self)

    @property
    def sources(self) -> list[Path]:
        return [source.filename for source in self._sources]

    @property
    def sources_info(self) -> list[CatalogSourceInfo]:
        return self._sources.copy()

    @property
    def catalog(self) -> CatalogType:
        return self._data.catalog

    @property
    def entries_count(self) -> int:
        return len(self._data.catalog)

    @property
    def frequency_limits(self) -> tuple[tuple[float, float], ...]:
        return self._data.frequency_limits if self._data.catalog else (0.0, math.inf)

    @property
    def min_frequency(self) -> float:
        return min(min(f) for f in self._data.frequency_limits) if self._data.frequency_limits else 0.0

    @property
    def max_frequency(self) -> float:
        return max(max(f) for f in self._data.frequency_limits) if self._data.frequency_limits else math.inf

    def filter(
        self,
        *,
        min_frequency: float = 0.0,
        max_frequency: float = math.inf,
        min_intensity: float = -math.inf,
        max_intensity: float = math.inf,
        temperature: float = -math.inf,
        any_name: str = "",
        any_formula: str = "",
        any_name_or_formula: str = "",
        anything: str = "",
        species_tag: int = 0,
        inchi_key: str = "",
        trivial_name: str = "",
        structural_formula: str = "",
        name: str = "",
        stoichiometric_formula: str = "",
        isotopolog: str = "",
        state: str = "",
        degrees_of_freedom: int | None = None,
    ) -> CatalogType:
        """
        Extract only the entries that match all the specified conditions

        :param float min_frequency: The lower frequency [MHz] to take.
        :param float max_frequency: The upper frequency [MHz] to take.
        :param float min_intensity: The minimal intensity [log10(nm²×MHz)] to take.
        :param float max_intensity: The maximal intensity [log10(nm²×MHz)] to take, use to avoid meta-stable substances.
        :param float temperature: The temperature to calculate the line intensity at,
                                  use the catalog intensity if not set.
        :param str any_name: A string to match the “trivialname” or the “name” field.
        :param str any_formula: A string to match the “structuralformula,” “moleculesymbol,”
                                “stoichiometricformula,” or “isotopolog” field.
        :param str any_name_or_formula: A string to match any field used by :param:any_name and :param:any_formula.
        :param str anything: A string to match any field.
        :param int species_tag: A number to match the “speciestag” field.
        :param str inchi_key: A string to match the “inchikey” field.
                              See https://iupac.org/who-we-are/divisions/division-details/inchi/ for more.
        :param str trivial_name: A string to match the “trivialname” field.
        :param str structural_formula: A string to match the “structuralformula” field.
        :param str name: A string to match the “name” field.
        :param str stoichiometric_formula: A string to match the “stoichiometricformula” field.
        :param str isotopolog: A string to match the “isotopolog” field.
        :param str state: A string to match the “state” or the “state_html” field.
        :param int degrees_of_freedom: 0 for atoms, 2 for linear molecules, and 3 for nonlinear molecules.
        :return: A dict of substances with non-empty lists of absorption lines that match all the conditions.
        """

        if self.is_empty:
            return dict()

        if min_frequency > max_frequency or min_frequency > self.max_frequency or max_frequency < self.min_frequency:
            return dict()

        def check_str(pattern: str, *text: str) -> bool:
            return not pattern or any(pattern == t for t in text)

        st: int
        selected_entries: CatalogType = dict()
        entry: CatalogEntryType
        filtered_entry: CatalogEntryType
        if any(
            (
                species_tag,
                inchi_key,
                trivial_name,
                structural_formula,
                name,
                stoichiometric_formula,
                isotopolog,
                state,
                degrees_of_freedom,
                any_name,
                any_formula,
                any_name_or_formula,
                anything,
            )
        ):
            trivial_name: str = trivial_name.casefold()
            name: str = name.casefold()
            any_name: str = any_name.casefold()
            any_name_or_formula_lowercase: str = any_name_or_formula.casefold()
            anything_lowercase: str = anything.casefold()
            for st in self._data.catalog if not species_tag else [species_tag]:
                entry = self._data.catalog.get(st, dict())
                if not entry:
                    continue
                if all(
                    (
                        check_str(inchi_key, entry.get(INCHI_KEY, "")),
                        check_str(trivial_name, entry.get(TRIVIAL_NAME, "").casefold()),
                        check_str(structural_formula, entry.get(STRUCTURAL_FORMULA, "")),
                        check_str(name, entry.get(NAME, "").casefold()),
                        check_str(stoichiometric_formula, entry.get(STOICHIOMETRIC_FORMULA, "")),
                        check_str(isotopolog, entry.get(ISOTOPOLOG, "")),
                        check_str(state, entry.get(STATE, ""), entry.get(STATE_HTML, "")),
                        (degrees_of_freedom is None or entry.get(DEGREES_OF_FREEDOM, -1) == degrees_of_freedom),
                        check_str(
                            any_name,
                            entry.get(TRIVIAL_NAME, "").casefold(),
                            entry.get(NAME, "").casefold(),
                        ),
                        check_str(
                            any_formula,
                            entry.get(STRUCTURAL_FORMULA, ""),
                            entry.get(MOLECULE_SYMBOL, ""),
                            entry.get(STOICHIOMETRIC_FORMULA, ""),
                            entry.get(ISOTOPOLOG, ""),
                        ),
                        (
                            not any_name_or_formula
                            or check_str(
                                any_name_or_formula_lowercase,
                                entry.get(TRIVIAL_NAME, "").casefold(),
                                entry.get(NAME, "").casefold(),
                            )
                            or check_str(
                                any_name_or_formula,
                                entry.get(STRUCTURAL_FORMULA, ""),
                                entry.get(MOLECULE_SYMBOL, ""),
                                entry.get(STOICHIOMETRIC_FORMULA, ""),
                                entry.get(ISOTOPOLOG, ""),
                            )
                        ),
                        (
                            not anything
                            or anything in (str(entry[key]) for key in entry if key != LINES)
                            or check_str(
                                anything_lowercase,
                                entry.get(TRIVIAL_NAME, "").casefold(),
                                entry.get(NAME, "").casefold(),
                            )
                        ),
                    )
                ):
                    filtered_entry = filter_by_frequency_and_intensity(
                        entry,
                        temperature=temperature,
                        min_frequency=min_frequency,
                        max_frequency=max_frequency,
                        min_intensity=min_intensity,
                        max_intensity=max_intensity,
                    )
                    if filtered_entry[LINES]:
                        selected_entries[st] = filtered_entry
        else:
            for st in self._data.catalog:
                entry = self.catalog.get(st, dict())
                if not entry:
                    continue
                filtered_entry = filter_by_frequency_and_intensity(
                    entry,
                    temperature=temperature,
                    min_frequency=min_frequency,
                    max_frequency=max_frequency,
                    min_intensity=min_intensity,
                    max_intensity=max_intensity,
                )
                if filtered_entry[LINES]:
                    selected_entries[st] = filtered_entry
        return selected_entries

    def filter_by_species_tags(
        self,
        *,
        species_tags: Iterable[int] | None = None,
        min_frequency: float = 0.0,
        max_frequency: float = math.inf,
        min_intensity: float = -math.inf,
        max_intensity: float = math.inf,
        temperature: float = -math.inf,
    ) -> CatalogType:
        """
        Extract only the entries that match the specified conditions

        :param Iterable[int] species_tags: Numbers to match the “speciestag” field.
        :param float min_frequency: The lower frequency [MHz] to take.
        :param float max_frequency: The upper frequency [MHz] to take.
        :param float min_intensity: The minimal intensity [log10(nm²×MHz)] to take.
        :param float max_intensity: The maximal intensity [log10(nm²×MHz)] to take, use to avoid meta-stable substances.
        :param float temperature: The temperature to calculate the line intensity at,
                                  use the catalog intensity if not set.
        :return: A dict of substances with non-empty lists of absorption lines that match all the conditions.
        """

        if self.is_empty:
            return dict()

        if min_frequency > max_frequency or min_frequency > self.max_frequency or max_frequency < self.min_frequency:
            return dict()

        species_tag: int
        selected_entries: CatalogType = dict()
        entry: CatalogEntryType
        filtered_entry: CatalogEntryType
        for species_tag in species_tags if species_tags is not None else self._data.catalog:
            entry = self.catalog.get(species_tag, dict())
            if not entry:
                continue
            filtered_entry = filter_by_frequency_and_intensity(
                entry,
                temperature=temperature,
                min_frequency=min_frequency,
                max_frequency=max_frequency,
                min_intensity=min_intensity,
                max_intensity=max_intensity,
            )
            if filtered_entry[LINES]:
                selected_entries[species_tag] = filtered_entry
        return selected_entries

    def print(self, **kwargs: None | int | float | str) -> None:
        """
        Print a table of the filtered catalog entries

        :param kwargs: All arguments that are valid for :func:`filter <catalog.Catalog.filter>`
        :return: nothing
        """
        entries: CatalogType = self.filter(**kwargs)
        if not entries:
            print("nothing found")
            return

        names: list[str] = []
        frequencies: list[float] = []
        intensities: list[float] = []
        entry: CatalogEntryType
        for species_tag in entries:
            entry = entries[species_tag]
            for line in cast(LinesType, entry[LINES]):
                names.append(entry[NAME])
                frequencies.append(line[FREQUENCY])
                intensities.append(line[INTENSITY])

        def max_width(items: list[str]) -> int:
            return max(len(item) for item in items)

        def max_precision(items: list[str]) -> int:
            return max((len(item) - item.find(".")) for item in items) - 1

        names_width: int = max_width(names)
        frequencies_str: list[str] = list(map(str, frequencies))
        intensities_str: list[str] = list(map(str, intensities))
        frequencies_width: int = max_width(frequencies_str)
        intensities_width: int = max_width(intensities_str)
        frequencies_precision: int = max_precision(frequencies_str)
        intensities_precision: int = max_precision(intensities_str)
        for j, (n, f, i) in enumerate(zip(names, frequencies, intensities)):
            print(
                " ".join(
                    (
                        f"{n:<{names_width}}",
                        f"{f:>{frequencies_width}.{frequencies_precision}f}",
                        f"{i:>{intensities_width}.{intensities_precision}f}",
                    )
                )
            )

    @classmethod
    def from_data(
        cls,
        catalog_data: CatalogType | CatalogJSONType,
        frequency_limits: tuple[float, float] = (0.0, math.inf),
    ) -> "Catalog":
        catalog: Catalog = Catalog()
        catalog._data.catalog = catalog_data
        catalog._data.frequency_limits = frequency_limits
        return catalog

    def save(self, filename: str | PathLike[str], build_time: datetime = datetime.now(tz=timezone.utc)) -> None:
        data_to_save: dict[str, CatalogJSONType | tuple[float, float] | str] = {
            CATALOG: dict((str(species_tag), self._data.catalog[species_tag]) for species_tag in self._data.catalog),
            FREQUENCY: list(self._data.frequency_limits),
            BUILD_TIME: build_time.isoformat(),
        }
        opener: Catalog.Opener
        try:
            opener = Catalog.Opener(filename)
        except ValueError:
            filename = Path(filename)
            opener = Catalog.Opener(filename.with_name(filename.name + Catalog.DEFAULT_SUFFIX))

        def ensure_bytes(data: AnyStr) -> bytes:
            if isinstance(data, str):
                return data.encode("utf-8")
            if isinstance(data, bytes):
                return data
            raise TypeError("Unknown conversion to bytes")

        f: BinaryIO
        with opener.open("wb") as f:
            f.write(ensure_bytes(json.dumps(data_to_save)))
