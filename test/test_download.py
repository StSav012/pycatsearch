import sys
from collections.abc import Iterable
from os import path


def test_download(args: Iterable[str] = ()):
    from pycatsearch import download

    orig_args: list[str] = sys.argv.copy()
    sys.argv.extend(args)

    download()

    sys.argv = orig_args


if __name__ == "__main__":
    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, "src"))})

    test_download(["-V"])
    test_download(["-fmin", "110000", "-fmax", "184000", "test_download_catalog.tar.gz"])
