#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def test_async_download():
    from pycatsearch import async_download

    async_download()


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_async_download()
