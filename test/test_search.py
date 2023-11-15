#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def test_search():
    from pycatsearch.catalog import Catalog

    c = Catalog("catalog.json.gz")
    c.print(min_frequency=140141, max_frequency=140142)


if __name__ == "__main__":
    test_search()
