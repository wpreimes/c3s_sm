# -*- coding: utf-8 -*-
from c3s_sm.interface import C3S_Nc_Img_Stack
from datetime import datetime
import os
import numpy.testing as nptest
from pygeobase.object_base import  Image
import numpy as np
from smecv_grid.grid import SMECV_Grid_v052

def test_c3s_timestamp_for_daterange():
    parameters = ['sm', 'sm_noise']

    path = os.path.join(os.path.dirname(__file__),
                        'c3s_sm-test-data', 'img', 'TCDR', '060_dailyImages', 'combined')

    ds = C3S_Nc_Img_Stack(path, parameters, fillval={'sm': np.nan}, solve_ambiguity='error')


    tstamps = [t for t in ds.tstamps_for_daterange(datetime(2000, 1, 1),
                                                   datetime(2000, 1, 5))]
    assert len(list(tstamps)) == 5
    assert list(tstamps) == [datetime(2000, 1, 1),
                             datetime(2000, 1, 2),
                             datetime(2000, 1, 3),
                             datetime(2000, 1, 4),
                             datetime(2000, 1, 5)]

def test_c3s_img_stack_single_img_reading():
    parameters = ['sm']

    path = os.path.join(os.path.dirname(__file__),
                        'c3s_sm-test-data', 'img', 'TCDR', '060_dailyImages', 'combined')

    subgrid = SMECV_Grid_v052('land').subgrid_from_bbox(-30,30,30,70)
    ds = C3S_Nc_Img_Stack(path, parameters, fillval={'sm': -1}, subgrid=subgrid, subpath_templ=('%Y',))

    img = ds.read(datetime(2014,1,1)) # type: Image

    test_loc_lonlat = (16.375, 48.125)
    row, col = np.where((img.lon == test_loc_lonlat[0]) & (img.lat == test_loc_lonlat[1]))

    nptest.assert_almost_equal(img.data['sm'][row, col], 0.34659, 4)
    assert np.min(img.data['sm']) == -1

def test_c3s_img_stack_multiple_img_reading_TCDR():
    startdate, enddate = datetime(2016,4,1), datetime(2016,6,1)

    parameters = ['sm']

    path = os.path.join(os.path.dirname(__file__),
                        'c3s_sm-test-data', 'img', 'TCDR', '061_monthlyImages', 'combined')

    ds = C3S_Nc_Img_Stack(path, parameters)

    row, col = None, None
    for i, img in enumerate(ds.iter_images(startdate, enddate)):
        test_loc_lonlat = (16.375, 48.125)
        r, c = np.where((img.lon == test_loc_lonlat[0]) & (img.lat == test_loc_lonlat[1]))
        if row is None:
            row = r
        else:
            assert row == r
        if col is None:
            col = c
        else:
            assert col == c
        if i == 0:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.32004, 4)
        if i == 1:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.31229, 4)
        if i == 2:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.31059, 4)


def test_c3s_img_stack_multiple_img_reading_ICDR():
    startdate, enddate = datetime(2017,7,1), datetime(2017,12,1)

    parameters = ['sm']

    path = os.path.join(os.path.dirname(__file__),
                        'c3s_sm-test-data', 'img', 'ICDR', '061_monthlyImages', 'passive')

    subgrid = SMECV_Grid_v052('land').subgrid_from_bbox(-30,30,30,70)
    ds = C3S_Nc_Img_Stack(path, parameters, subgrid=subgrid, subpath_templ=None)

    row, col = None, None

    for i, img in enumerate(ds.iter_images(startdate, enddate)):
        test_loc_lonlat = (16.375, 48.125)
        r, c = np.where((img.lon == test_loc_lonlat[0]) & (img.lat == test_loc_lonlat[1]))
        if row is None:
            row = r
        else:
            assert row == r
        if col is None:
            col = c
        else:
            assert col == c
        if i == 0:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.23400, 4)
        if i == 1:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.22680, 4)
        if i == 2:
            nptest.assert_almost_equal(img.data['sm'][row, col], 0.29522, 4)



if __name__ == '__main__':

    test_c3s_timestamp_for_daterange()
    test_c3s_img_stack_multiple_img_reading_TCDR()
    test_c3s_img_stack_single_img_reading()
    test_c3s_img_stack_multiple_img_reading_ICDR()
