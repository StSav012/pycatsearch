#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def test_download():
    from pycatsearch import download

    download()


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_download()
