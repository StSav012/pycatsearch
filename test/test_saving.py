from pathlib import PurePath


def test_saving():
    from pycatsearch.catalog import Catalog

    c = Catalog("test catalog.json")
    assert c, c.sources

    test_dir: PurePath = PurePath(__file__).parent

    c.save(filename=test_dir / "catalog.json")
    c.save(filename=test_dir / "catalog.json.gz")
    c.save(filename=test_dir / "catalog.tar.gz")
    c.save(filename=test_dir / "catalog.hdf5")
    c.save(filename=test_dir / "catalog.pickle")
    c.save(filename=test_dir / "catalog.pickle.gz")


if __name__ == "__main__":
    import sys
    from os import path

    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, "src"))})

    test_saving()
