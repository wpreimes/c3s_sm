# -*- coding: utf-8 -*-

import os
import glob
from tempfile import TemporaryDirectory
import numpy as np
import numpy.testing as nptest

from c3s_sm.reshuffle import main, parse_filename
from c3s_sm.interface import C3STs
import pandas as pd

def test_parse_filename():
    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "c3s_sm-test-data", "img2ts", "ICDR", "combined")

    file_args, file_vars = parse_filename(inpath)

    assert file_args['unit'] == 'V'
    assert file_args['prod'] == 'COMBINED'
    assert file_args['temp'] == 'MONTHLY'
    assert file_args['cdr'] == 'ICDR'
    assert file_args['vers'] == 'v201706'
    assert file_args['subvers'] == '0.0'

    assert file_vars == [u'lat', u'lon', u'time', u'nobs', u'sensor', u'freqbandID', u'sm']

def test_reshuffle_TCDR_daily_multiple_params():
    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "c3s_sm-test-data", "img2ts", "TCDR", "active")
    startdate = "1991-08-05"
    enddate = "1991-08-08"
    parameters = ['--parameters', 'sm', 'sm_uncertainty']
    land_points = 'True'
    bbox = ['--bbox', '70', '10', '80', '20']

    with TemporaryDirectory() as ts_path:
        args = [inpath, ts_path, startdate, enddate]  + \
               parameters + ['--land_points', land_points] + bbox
        main(args)

        assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 5

        ds = C3STs(ts_path, remove_nans=True, parameters=['sm', 'sm_uncertainty'],
                   ioclass_kws={'read_bulk': True, 'read_dates': False})
        ts = ds.read(75.625, 14.625)

        assert not any(ts['sm'] == 0)
        assert isinstance(ts.index, pd.DatetimeIndex)
        ts_sm_values_should = np.array([66.0677, np.nan, 80.7060, 70.5648], dtype=np.float32)
        nptest.assert_allclose(ts['sm'].values, ts_sm_values_should, rtol=1e-5)

        ts_uncert_values_should = np.array([np.nan, np.nan, np.nan, np.nan],
                                           dtype=np.float32)
        nptest.assert_allclose(ts['sm_uncertainty'].values, ts_uncert_values_should,rtol=1e-5)

        nptest.assert_almost_equal(ts['sm'].values, ds.read(602942)['sm'].values)

        ds.close()

def test_reshuffle_ICDR_monthly_single_param():
    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "c3s_sm-test-data", "img2ts", "ICDR", "combined")
    startdate = "2018-05-01"
    enddate = "2018-08-01"
    bbox = ['--bbox', '-170','50','-150','70']

    land_points = 'False'
    with TemporaryDirectory() as ts_path:
        args = [inpath, ts_path, startdate, enddate] \
               + ['--land_points', land_points] + bbox
        main(args)

        assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 17

        ds = C3STs(ts_path, remove_nans=True, parameters=None, ioclass_kws={'read_bulk': True, 'read_dates': False})
        ts = ds.read(-159.625, 65.875)
        assert isinstance(ts.index, pd.DatetimeIndex)
        ts_sm_values_should = np.array([0.23628984, 0.33424062, np.nan, 0.26261818], dtype=np.float32)

        nptest.assert_allclose(ts['sm'].values, ts_sm_values_should, rtol=1e-5)

        ts_sensor_values_should = np.array([768, 768, 768, 768 ], dtype=np.float32)
        nptest.assert_allclose(ts['sensor'].values, ts_sensor_values_should,rtol=1e-5)

        ds.close()
