# -*- coding: utf-8 -*-

import os
import glob
import tempfile
import numpy as np
import numpy.testing as nptest

from c3s_sm_reader.reshuffle import main
from c3s_sm_reader.interface import C3STs


def test_reshuffle():
    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test-data", "img2ts")
    startdate = "1991-08-05"
    enddate = "1991-08-10"
    parameters = ["sm", "sm_uncertainty"]
    iter_land_points = ['False', 'True']
    for land_points in iter_land_points:
        ts_path = tempfile.mkdtemp()
        args = [inpath, ts_path, startdate, enddate] + parameters + ['--land_points', land_points]
        main(args)

        if land_points == 'True':
            assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 969
        else:
            assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 2593

        ds = C3STs(ts_path, remove_nans=True)
        ts = ds.read(-159.625, 65.875)
        ts_sm_values_should = np.array([np.nan, 78.78714, np.nan, np.nan,
                                            87.600899, np.nan], dtype=np.float32)
        nptest.assert_allclose(ts['sm'].values, ts_sm_values_should, rtol=1e-5)

        ts_uncert_values_should = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], dtype=np.float32)
        nptest.assert_allclose(ts['sm_uncertainty'].values, ts_uncert_values_should,rtol=1e-5)


if __name__ == '__main__':
    test_reshuffle()