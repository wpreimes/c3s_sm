# -*- coding: utf-8 -*-
"""
Module for a command line interface to convert the C3S data into a
time series format using the repurpose package
"""

import os
import sys
import argparse
from datetime import datetime

from repurpose.img2ts import Img2Ts
from c3s_sm.interface import C3S_Nc_Img_Stack, c3s_filename_template
from c3s_sm.grid import C3SLandGrid, C3SCellGrid
import c3s_sm.metadata as metadata
from c3s_sm.metadata import C3S_daily_tsatt_nc, C3S_dekmon_tsatt_nc
from pygeogrids.grids import BasicGrid

import numpy as np

from parse import parse

from netCDF4 import Dataset


def mkdate(datestring):
    """
    Create date string.

    Parameters
    ----------
    datestring : str
        Date string.
    Returns
    -------
    datestr : datetime
        Date string as datetime.
    """
    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')

def str2bool(val):
    if val in ['True', 'true', 't', 'T', '1']:
        return True
    else:
        return False


def parse_filename(data_dir):
    '''
    Take the first file in the passed directory and use its file name to
    retrieve the product type, version number and variables in the file.

    Parameters
    ----------
    inroot : str
        Input root directory

    Returns
    -------
    file_args : dict
        Parsed arguments from file name
    file_vars : list
        Names of parameters in the first detected file
    '''
    template = c3s_filename_template()

    for curr, subdirs, files in os.walk(data_dir):
        for f in files:
            file_args = parse(template, f)
            if file_args is None:
                continue
            else:
                file_args = file_args.named
                file_args['datetime'] = '{datetime}'
                file_vars = Dataset(os.path.join(curr,f)).variables.keys()
                return file_args, list(file_vars)

    raise IOError('No file name in passed directory fits to template')


def reshuffle(input_root, outputpath, startdate, enddate,
              parameters, land_points=True,
              imgbuffer=50):
    """
    Reshuffle method applied to C3S data.
    Parameters
    ----------
    input_root: string
        input path where c3s images were downloaded.
    outputpath : string
        Output path.
    startdate : datetime
        Start date.
    enddate : datetime
        End date.
    parameters: list
        parameters to read and convert
    land_points : bool, optional (default: True)
        Use the land grid to calculate time series on.
        Leads to faster processing and smaller files.
    imgbuffer: int, optional (default: 50)
        How many images to read at once before writing time series.
    """

    if land_points:
        grid = C3SLandGrid()
    else:
        grid = C3SCellGrid()

    gpis, lons, lats, cells = grid.get_grid_points()
    grid_vars = {'gpis': gpis, 'lons':lons, 'lats':lats}
    # repurpose cannot handle masked arrays
    for k, v in grid_vars.items(): # type v: np.ma.MaskedArray
        if isinstance(v, np.ma.MaskedArray):
            grid_vars[k] = v.filled()

    grid = BasicGrid(lon=grid_vars['lons'], lat=grid_vars['lats'], gpis=grid_vars['gpis']).to_cell_grid(5.)

    if parameters is None:
        file_args, file_vars = parse_filename(input_root)
        parameters = [p for p in file_vars if p not in ['lat', 'lon', 'time']]

    input_dataset = C3S_Nc_Img_Stack(data_path=input_root, parameters=parameters,
                                     subgrid=grid, array_1D=True)

    prod_args = input_dataset.fname_args


    kwargs = {'product_sensor_type' : prod_args['sensor_type'].lower(),
              'sub_version' : '.' + prod_args['sub_version'],
              'product_sub_type': prod_args['sub_prod']}

    class_str = "C3S_SM_TS_Attrs_%s" % (prod_args['version'])
    subattr = getattr(metadata, class_str)

    if prod_args['temp_res'] == 'DAILY':
        attrs = C3S_daily_tsatt_nc(subattr, **kwargs)
    else:
        attrs = C3S_dekmon_tsatt_nc(subattr, **kwargs)

    ts_attributes = {}
    global_attributes = attrs.global_attr

    # todo: attrs for all vars or only for the ones that TS were created for.
    for var in parameters:
        ts_attributes.update(attrs.ts_attributes[var])


    if not os.path.exists(outputpath):
        os.makedirs(outputpath)


    reshuffler = Img2Ts(input_dataset=input_dataset, outputpath=outputpath,
                        startdate=startdate, enddate=enddate, input_grid=grid,
                        imgbuffer=imgbuffer, cellsize_lat=5.0,
                        cellsize_lon=5.0, global_attr=global_attributes, zlib=True,
                        unlim_chunksize=1000, ts_attributes=ts_attributes)
    reshuffler.calc()


def parse_args(args):
    """
    Parse command line parameters for C3S reshuffling.

    Parameters
    ----------
    args : list of str
        Command line parameters as list of strings.

    Returns
    -------
    args : argparse.Namespace
        Command line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Convert C3s image data to time series format.")
    parser.add_argument("dataset_root",
                        help='Root of local filesystem where the '
                             'data is stored.')

    parser.add_argument("timeseries_root",
                        help='Root of local filesystem where the timeseries '
                             'should be stored.')

    parser.add_argument("start", type=mkdate,
                        help=("Startdate. In format YYYY-MM-DD"))

    parser.add_argument("end", type=mkdate,
                        help=("Enddate. In format YYYY-MM-DD"))

    parser.add_argument("--parameters", metavar="parameters", default=None,
                        nargs="+",
                        help=("Parameters to reshuffle into time series format. "
                              "E.g. sm for creating soil moisture time series."
                              "If None are passed, all variables from the first image file in the path are used."))

    parser.add_argument("--land_points", type=str2bool, default='False',
                        help=("Set True to convert only land points as defined"
                              " in the C3s land mask (faster and less/smaller files)"))

    parser.add_argument("--imgbuffer", type=int, default=50,
                        help=("How many images to read at once. Bigger "
                              "numbers make the conversion faster but "
                              "consume more memory."))

    args = parser.parse_args(args)
    # set defaults that can not be handled by argparse

    print("Converting data from {} to"
          " {} into folder {}.".format(args.start.isoformat(),
                                      args.end.isoformat(),
                                      args.timeseries_root))

    return args


def main(args):
    """
    Main routine used for command line interface.
    Parameters
    ----------
    args : list of str
        Command line arguments.
    """
    args = parse_args(args)

    reshuffle(args.dataset_root,
              args.timeseries_root,
              args.start,
              args.end,
              args.parameters,
              land_points=args.land_points,
              imgbuffer=args.imgbuffer)



def run():
    main(sys.argv[1:])

if __name__ == '__main__':


    cmd = [r'C:\Temp\tcdr\active_daily', r'C:\Temp\tcdr\ts',
           '1991-08-05', '1991-08-10', '--land_points', 'True']
    main(cmd)

    from interface import C3STs

    ds = C3STs(r'C:\Temp\tcdr\ts')
    ds.read(47.875, 7.875)
    run()