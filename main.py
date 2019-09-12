# -*- coding: utf-8 -*-

from catalog import Catalog

c = Catalog('catalog.json.gz')
c.print(min_frequency=140141, max_frequency=140142)
