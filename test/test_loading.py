import os.path
from datetime import datetime, timezone
from pathlib import PurePath


def test_loading(fn: str | PurePath):
    from src.pycatsearch.catalog import Catalog

    start: datetime = datetime.now(tz=timezone.utc)
    c = Catalog(fn)
    stop: datetime = datetime.now(tz=timezone.utc)
    assert bool(c) == os.path.exists(fn), c.sources
    print(fn, c.entries_count, c.min_frequency, c.max_frequency, stop - start)
    return c


if __name__ == "__main__":
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
