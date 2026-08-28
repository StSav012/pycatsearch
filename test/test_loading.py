import sys
from datetime import datetime, timezone
from os import path
from pathlib import PurePath


def test_loading(fn: str | PurePath):
    from pycatsearch.catalog import Catalog

    start: datetime = datetime.now(tz=timezone.utc)
    c = Catalog(fn)
    stop: datetime = datetime.now(tz=timezone.utc)
    assert bool(c) == path.exists(fn), fn
    print(fn, c.entries_count, c.min_frequency, c.max_frequency, stop - start)
    return c


if __name__ == "__main__":
    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, "src"))})

    test_dir: PurePath = PurePath(__file__).parent

    for filename in (
        "catalog.json",
        "catalog.json.gz",
        "catalog.tar.gz",
        "catalog.hdf5",
        "catalog.pickle",
        "catalog.pickle.gz",
    ):
        test_loading(test_dir / filename)
