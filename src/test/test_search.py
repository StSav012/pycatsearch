#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def test_search():
    from tempfile import NamedTemporaryFile

    from pycatsearch.catalog import Catalog

    with NamedTemporaryFile("wb", suffix=".json") as f:
        f.write(
            b"""\
{
    "catalog": [
        {
            "id": 31,
            "molecule": 29,
            "structuralformula": "NH3",
            "stoichiometricformula": "H3N",
            "moleculesymbol": "NH<sub>3</sub>",
            "speciestag": 17004,
            "name": "NH3-v2",
            "trivialname": "Ammonia",
            "isotopolog": "NH3",
            "state": "$v2=1$",
            "state_html": "v2=1",
            "inchikey": "QGZKDVFQNNGYKY-UHFFFAOYSA-N",
            "contributor": "Shanshan Yu",
            "version": "5",
            "dateofentry": "2010-09-01",
            "degreesoffreedom": 3,
            "lines": [
                {
                    "frequency": 140141.8067,
                    "intensity": -5.0383,
                    "lowerstateenergy": 983.3773
                },
                {
                    "frequency": 140142.0001,
                    "intensity": -5.0383,
                    "lowerstateenergy": 983.3773
                }
            ]
        }
    ],
    "frequency": [
        110000.0,
        170000.0
    ],
    "build_time": "2023-05-05T10:07:28.690146+00:00"
}
"""
        )
        f.flush()
        c = Catalog(f.name)
    assert c, c.sources

    assert len(c.filter(min_frequency=140141, max_frequency=140142)[17004]["lines"]) == 1
    assert not c.filter(any_name_or_formula="oxygen")
    assert len(c.filter_by_species_tags(species_tags=[17004])[17004]["lines"]) == 2


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_search()
