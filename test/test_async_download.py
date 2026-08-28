import sys
from collections.abc import Iterable


def test_async_download(args: Iterable[str] = ()):
    from src.pycatsearch import async_download

    orig_args: list[str] = sys.argv.copy()
    sys.argv.extend(args)

    async_download()

    sys.argv = orig_args


if __name__ == "__main__":
    test_async_download(["-V"])
    test_async_download(["-fmin", "110000", "-fmax", "184000", "test_download_catalog.json.gz"])
