# -*- coding: utf-8 -*-

"""
Test downloading c3s sm from cds via cds api
"""

from c3s_sm.download import main, api_ready
import tempfile
import os
import pytest

@pytest.mark.skipif(not api_ready, reason="Missing CDS API URL or KEY, create env vars or set up .cdsapirc")
def test_download_c3s_combined_monthly():
    path = tempfile.mkdtemp()
    args = [path, '-s', '2016-11-12', '-e', '2017-03-31', '--aggregation',
            'monthly', '-sp', 'combined', '-vers', 'v201706.0.0']
    main(args)

    assert len(os.listdir(os.path.join(path, '2016'))) == 2
    assert len(os.listdir(os.path.join(path, '2017'))) == 3


@pytest.mark.skipif(not api_ready, reason="Missing CDS API URL or KEY, create env vars or set up .cdsapirc")
def test_download_c3s_passive_daily():
    path = tempfile.mkdtemp()
    args = [path, '-s', '2017-06-28', '-e', '2017-07-02', '--aggregation',
            'daily', '-sp', 'passive', '-vers', 'v201706.0.0']
    main(args)

    assert len(os.listdir(os.path.join(path, '2017'))) == 5