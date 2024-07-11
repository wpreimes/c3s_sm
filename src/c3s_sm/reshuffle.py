# -*- coding: utf-8 -*-
"""
Module for a command line interface to convert the C3S data into a
time series format using the repurpose package
"""

import os
import shutil
import warnings
from datetime import datetime
import pandas as pd
from smecv_grid.grid import SMECV_Grid_v052
from parse import parse
from netCDF4 import Dataset
import numpy as np

from repurpose.img2ts import Img2Ts
from repurpose.process import ImageBaseConnection
from c3s_sm.interface import C3S_Nc_Img_Stack
from c3s_sm.const import fntempl as _default_template
import c3s_sm.metadata as metadata
from c3s_sm.metadata import C3S_daily_tsatt_nc, C3S_dekmon_tsatt_nc
from c3s_sm.misc import update_ts_summary

def parse_filename(data_dir, fntempl=_default_template):
    """
    Take the first file in the passed directory and use its file name to
    retrieve the product type, version number and variables in the file.

    Parameters
    ----------
    inroot : str
        Input root directory
    fntempl: str, optional (default: :const:`c3s_sm.const.fntempl`)
        Filename template

    Returns
    -------
    file_args : dict
        Parsed arguments from file name
    file_vars : list
        Names of parameters in the first detected file
    """

    for curr, subdirs, files in os.walk(data_dir):
        for f in sorted(files):
            file_args = parse(fntempl, f)
            if file_args is None:
                continue
            else:
                file_args = file_args.named
                file_args['datetime'] = '{datetime}'
                file_vars = Dataset(os.path.join(curr,f)).variables.keys()
                return file_args, list(file_vars)

    raise IOError('No file name in passed directory fits to template')


def reshuffle(*args, **kwargs):
    warnings.warn("`c3s_sm.reshuffle.reshuffle` is deprecated, "
                  "use `c3s_sm.reshuffle.img2ts`",
                  category=DeprecationWarning)
    return img2ts(*args, **kwargs)

def img2ts(input_root, outputpath, startdate, enddate,
           parameters=None, land_points=True, bbox=None,
           ignore_meta=False, fntempl=_default_template,
           replace_existing=False, imgbuffer=250,
           n_proc=1):
    """
    Reshuffle method applied to C3S data.

    Parameters
    ----------
    input_root: str
        input path where c3s images were downloaded.
    outputpath : str, optional (default: None)
        Output path.
    startdate : datetime or str
        Start date. If None is passed, then we will try to detect the date of
        the first available image file
    enddate : datetime or str
        End date. If None is passed, then we will try to detect the date of
        the last available image file
    parameters: list, optional (default: None)
        parameters to read and convert to time series. If None is passed, then
        we use all available parameters from the input files.
    land_points : bool, optional (default: True)
        Use the land grid to calculate time series on.
        Leads to faster processing and smaller files.
    bbox : tuple, optional (default: None)
        Min lon, min lat, max lon, max lat
        BBox to read data for. Data outside the bbox is ignored in the
        conversion step.
    ignore_meta : bool, optional (default: False)
        Ignore metadata and reshuffle only the values. Can be used e.g. if a
        version is not yet supported.
    fntempl: str, optional (default: see :const:`c3s_sm.const.fntempl`)
        Template that image files follow, must contain a section {datetime}
        where the date is parsed from.
    replace_existing: bool, optional (default: False)
        If this option is activated, then any existing files on the output
        directory will be deleted before the conversion takes place.
        Otherwise the program will try to append new data to existing files.
    imgbuffer: int, optional (default: 250)
        How many images to read at once before writing time series.
    n_proc: int, optional (default: 1)
        Number of parallel processes to read and write data.
    """

    if land_points:
        grid = SMECV_Grid_v052('land')
    else:
        grid = SMECV_Grid_v052(None)

    if bbox:
        grid = grid.subgrid_from_bbox(*bbox)


    if parameters is None:
        file_args, file_vars = parse_filename(input_root, fntempl=fntempl)
        parameters = [p for p in file_vars if p not in ['lat', 'lon', 'time']]

    startdate = pd.to_datetime(startdate).to_pydatetime()
    enddate = pd.to_datetime(enddate).to_pydatetime()

    subpath_templ = ('%Y',) if os.path.isdir(os.path.join(input_root, str(startdate.year))) else None
    input_dataset = C3S_Nc_Img_Stack(data_path=input_root,
                                     parameters=parameters,
                                     subgrid=grid,
                                     flatten=True,
                                     fillval={'sm': np.nan, 'flag': 2**8},
                                     fntempl=fntempl,
                                     subpath_templ=subpath_templ)

    if not ignore_meta:
        prod_args = input_dataset.fname_args

        kwargs = {
            'sensor_type': prod_args['product'].lower(),
            'cdr_type': prod_args['record'],
            'freq':  prod_args['freq'],
            'cls': getattr(metadata, f"C3S_SM_TS_Attrs_{prod_args['version']}")
        }

        if prod_args['freq'].upper() == 'DAILY':
            kwargs.pop('freq')
            attrs = C3S_daily_tsatt_nc(**kwargs)
        else:
            attrs = C3S_dekmon_tsatt_nc(**kwargs)

        ts_attributes = {}
        global_attributes = attrs.global_attr

        for var in parameters:
            ts_attributes[var] = attrs.ts_attributes[var]
    else:
        global_attributes = None
        ts_attributes = None

    if replace_existing:
        if os.path.exists(outputpath):
            shutil.rmtree(outputpath)

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    # switch to circumvent imagebase connection (to speed up tests)
    if os.environ.get("C3S_SM_NO_IMAGE_BASE_CONNECTION", "0") == "1":
        pass
    else:
        input_dataset = ImageBaseConnection(input_dataset)

    reshuffler = Img2Ts(input_dataset=input_dataset, outputpath=outputpath,
                        startdate=startdate, enddate=enddate, input_grid=grid,
                        imgbuffer=imgbuffer, cellsize_lat=5.0,
                        cellsize_lon=5.0, global_attr=global_attributes,
                        zlib=True, unlim_chunksize=1000,
                        ts_attributes=ts_attributes, n_proc=n_proc)

    reshuffler.calc()

    update_ts_summary(outputpath, os.path.join(outputpath, '000_overview.yml'))
