#!/usr/bin/env python3
from collections.abc import Iterable


def test_download(args: Iterable[str] = ()):
    import sys

    from pycatsearch import download

    sys.argv.extend(args)

    download()


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, path.pardir))})

    test_download(["-V"])
    test_download("-fmin 110000 -fmax 184000 test_download_catalog.tar.gz".split())
