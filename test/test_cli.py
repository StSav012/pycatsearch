#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


def test_cli():
    from pycatsearch import main_cli as main

    return main()


if __name__ == "__main__":
    exit(test_cli())
