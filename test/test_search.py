import sys
from os import path


def test_search():
    from pycatsearch.catalog import Catalog

    c = Catalog("test catalog.json")
    assert c, c.sources

    assert len(c.filter(min_frequency=140141, max_frequency=140142)[17004].lines) == 1
    assert not c.filter(any_name_or_formula="oxygen")
    assert len(c.filter_by_species_tags(species_tags=[18003])[18003].lines) == 2


if __name__ == "__main__":
    sys.path = list(set(sys.path) | {path.abspath(path.join(__file__, path.pardir, "src"))})

    test_search()
