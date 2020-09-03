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
from c3s_sm.interface import C3SDs, c3s_filename_template
from c3s_sm.grid import C3SCellGrid
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
              imgbuffer=50, **ds_kwargs):
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
    if 'grid' not in ds_kwargs.keys():
        ds_kwargs['grid'] = None
    if 'parameters' not in ds_kwargs.keys():
        ds_kwargs['parameters'] = None

    input_dataset = C3SDs(data_path=input_root, array_1D=True, **ds_kwargs)

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
                              "If None are passed, all variables from the first image "
                              "file in dataset_root are used."))

    parser.add_argument("--land_points", type=str2bool, default='False',
                        help=("Set True to convert only land points as defined"
                              " in the C3s land mask (faster and less/smaller files)"))

    parser.add_argument("--bbox", type=float, default=None, nargs=4,
                        help=("min_lon min_lat max_lon max_lat. "
                              "Bounding Box (lower left and upper right corner) "
                              "of subset area of global images to reshuffle (WGS84). "
                              "Default: None"))

    parser.add_argument("--imgbuffer", type=int, default=50,
                        help=("How many images to read at once. Bigger "
                              "numbers make the conversion faster but "
                              "consume more memory."))

    args = parser.parse_args(args)
    # set defaults that can not be handled by argparse

    print(f"Converting C3S SM data from {args.dataset_root} between "
          f"{args.start.isoformat()} and {args.end.isoformat()} "
          f"into folder {args.timeseries_root}. ")
    if args.land_points is True:
        print(f"Only land points are reshuffled.")
    if args.bbox is not None:
        print(f"Bounding Box used: {str(args.bbox)}")

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

    subset_flag = 'land' if args.landpoints is True else None
    grid = C3SCellGrid(subset_flag=subset_flag)
    if args.bbox is not None:
        grid = grid.subgrid_from_bbox(*args.bbox)

    ds_kwargs = {'grid': grid,
                 'parameters': args.parameters}

    reshuffle(args.dataset_root,
              args.timeseries_root,
              args.start,
              args.end,
              imgbuffer=args.imgbuffer,
              **ds_kwargs)



def run():
    main(sys.argv[1:])