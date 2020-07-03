# -*- coding: utf-8 -*-
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

import os

src_path = os.path.join(os.path.dirname(__file__), '..')

tests_path = os.path.join(src_path, '..', 'tests')
if not os.path.exists(tests_path):
    tests_path = 'unknown'

testdata_path = os.path.join(src_path, '..', 'tests', 'c3s_sm-test-data')
if not os.path.exists(testdata_path):
    testdata_path = 'unknown'
