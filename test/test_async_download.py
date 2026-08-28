import sys
from collections.abc import Iterable
from os import path


def test_async_download(args: Iterable[str] = ()):
    from pycatsearch import async_download

    orig_args: list[str] = sys.argv.copy()
    sys.argv.extend(args)

    async_download()

    sys.argv = orig_args


if __name__ == "__main__":
    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, "src"))})

    test_async_download(["-V"])
    test_async_download(["-fmin", "110000", "-fmax", "184000", "test_download_catalog.json.gz"])
