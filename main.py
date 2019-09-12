# -*- coding: utf-8 -*-
import sys

from catalog import Catalog

if sys.version_info < (3, 6):
    print('Get a newer Python!')
    exit(1)

# sample call
c = Catalog('catalog.json.gz')
c.print(min_frequency=140141, max_frequency=140142)
