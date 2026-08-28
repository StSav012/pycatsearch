import sys
from collections.abc import Iterable


def test_download(args: Iterable[str] = ()):
    from src.pycatsearch import download

    orig_args: list[str] = sys.argv.copy()
    sys.argv.extend(args)

    download()

    sys.argv = orig_args


if __name__ == "__main__":
    test_download(["-V"])
    test_download(["-fmin", "110000", "-fmax", "184000", "test_download_catalog.tar.gz"])
