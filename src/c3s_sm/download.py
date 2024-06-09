# -*- coding: utf-8 -*-

"""
Download c3s soil moisture from the CDS
"""

import cdsapi
from datetime import datetime, timedelta
import warnings
import calendar
import os
from zipfile import ZipFile
import argparse
import sys
import logging

dotrc = os.environ.get('CDSAPI_RC', os.path.expanduser('~/.cdsapirc'))

if not os.path.isfile(dotrc):
    url = os.environ.get('CDSAPI_URL')
    key = os.environ.get('CDSAPI_KEY')
    if url is None or key is None:
        warnings.warn('CDS API URL or KEY not found, download will not work! '
                      'Please set CDSAPI_URL and CDSAPI_KEY  or set up a .cdsapirc '
                      'file as described here: '
                      'https://cds.climate.copernicus.eu/api-how-to')
        api_ready = False
    else:
        api_ready = True
else:
    api_ready = True

variable_lut = {'combined': {'variable' : 'volumetric_surface_soil_moisture',
                             'type_of_sensor' : 'combined_passive_and_active'},
                'passive': {'variable' : 'volumetric_surface_soil_moisture',
                            'type_of_sensor': 'passive'},
                'active': {'variable': 'soil_moisture_saturation',
                           'type_of_sensor': 'active'}}

aggregation_lut = {'daily': 'day_average',
                   'dekadal': '10_day_average',
                   'monthly': 'month_average'}

def logger(fname, level=logging.DEBUG, verbose=False):

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(filename=fname, level=level,
                        format='%(levelname)s %(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    if verbose:
        logger.addHandler(logging.StreamHandler(sys.stdout))
    logging.captureWarnings(True)

    assert os.path.exists(fname)

    return logger

def download_c3ssm(c, sensor, years, months, days, version, target_dir, temp_filename,
                   aggregation='daily', keep_original=False, max_retries=5):
    """
    Download c3s sm data for single levels of a defined time span
    Parameters. We will always try to download the CDR and ICDR!

    ----------
    c : cdsapi.Client
        Client to pass the request to
    sensor : str
        active, passive or combined. The sensor product to download
    years : list
        Years for which data is downloaded ,e.g. [2017, 2018]
    months : list
        Months for which data is downloaded, e.g. [4, 8, 12]
    days : list
        Days for which data is downloaded (range(31)=All days) e.g. [10, 20, 31]
    version: str
        Version string of data to download, e.g. 'v201706.0.0'
    variables : list, optional (default: None)
        List of variables to pass to the client, if None are passed, the default
        variables will be downloaded.
    target_dir : str
        Directory where the data is downloaded into
    temp_filename : str
        filename of the zip archive that will be downloaded
    aggregation : str
        daily, dekadal or monthly. Which of the three aggregated products to
        download.

    Returns
    ---------
    success : bool
        Indicates whether the download was successful
    """

    if not os.path.exists(target_dir):
        raise IOError(f'Target path {target_dir} does not exist.')

    success = {'icdr': False, 'cdr': False}

    for record in ['cdr', 'icdr']:
        dl_file = os.path.join(target_dir, temp_filename)
        i = 0
        while not success[record] and i <= max_retries:
            try:
                c.retrieve(
                    'satellite-soil-moisture',
                    {
                        'variable': variable_lut[sensor]['variable'],
                        'type_of_sensor': variable_lut[sensor]['type_of_sensor'],
                        'time_aggregation': aggregation_lut[aggregation],
                        'format': 'zip',
                        'year': [str(y) for y in years],
                        'month': [str(m).zfill(2) for m in months],
                        'day': [str(d).zfill(2) for d in days],
                        'version': version,
                        'type_of_record': record
                    },
                    dl_file)

                success[record] = True
            except:
                # delete the partly downloaded data and retry
                if os.path.isfile(dl_file):
                    os.remove(dl_file)
                success[record] = False
            finally:
                i += 1

        if success[record]:
            with ZipFile(dl_file, 'r') as zip_file:
                zip_file.extractall(target_dir)

            if not keep_original:
                os.remove(dl_file)

    return success

def download_and_extract(target_path, startdate=datetime(1978,1,1),
                         enddate=datetime.now(), sensor='combined',
                         aggregation='daily', version='v201706.0.0',
                         keep_original=False):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 day increments between start and end date.
    The files are then extracted into separate grib files per parameter and stored
    in yearly folders under the target_path.
    Parameters
    ----------
    target_path : str
        Path where the files are stored to
    startdate: datetime, optional (default: datetime(1978,1,1))
        first day to download data for (if available)
    enddate: datetime, optional (default: datetime.now())
        last day to download data for (if available)
    sensor : str, optional (default: 'combined')
        Product (combined, active, passive) to download
    aggregation : str, optional (default: 'daily')
        'daily', 'dekadal' or 'monthly' averaged data to download.
    version : str, optional (default: 'v201706.0.0')
        Dataset version to download.
    keep_original: bool, optional (default: False)
        Keep the original downloaded data in zip format together with the unzipped
        files.
    """

    sensor = sensor.lower()
    if sensor not in variable_lut.keys():
        raise ValueError(f"{sensor} is not a supported product. "
                         f"Choose one of {list(variable_lut.keys())}")

    aggregation = aggregation.lower()
    if aggregation not in aggregation_lut.keys():
        raise ValueError(f"{aggregation} is not a supported aggregation. "
                         f"Choose one of {list(aggregation_lut.keys())}")

    dl_logger = logger(os.path.join(target_path,
        f"download_{'{:%Y%m%d%H%M%S.%f}'.format(datetime.now())}.log"))

    c = cdsapi.Client(quiet=True,
                      url=os.environ.get('CDSAPI_URL'),
                      key=os.environ.get('CDSAPI_KEY'),
                      error_callback=dl_logger)

    if aggregation == 'daily':
        curr_start = startdate
        # download monthly zip archives
        while curr_start <= enddate:
            sy, sm, sd = curr_start.year, curr_start.month, curr_start.day
            sm_days = calendar.monthrange(sy, sm)[1]  # days in the current month
            y, m = sy, sm

            if (enddate.year == y) and (enddate.month == m):
                d = enddate.day
            else:
                d = sm_days

            curr_end = datetime(y, m, d)

            fname = f"{curr_start.strftime('%Y%m%d')}_{curr_end.strftime('%Y%m%d')}.zip"

            target_dir_year = os.path.join(target_path, str(y))
            os.makedirs(target_dir_year, exist_ok=True)

            _ = download_c3ssm(c, sensor, years=[y], months=[m],
                               days=list(range(sd, d+1)), version=version,
                               aggregation=aggregation, max_retries=3,
                               target_dir=target_dir_year, temp_filename=fname,
                               keep_original=keep_original)

            curr_start = curr_end + timedelta(days=1)

    else:
        curr_year = startdate.year
        # download annual zip archives, this means that the day is ignored
        # when downloading monthly/dekadal data.
        if aggregation == 'monthly':
            ds = [1]
        else:
            ds = [1, 11, 21]

        while curr_year <= enddate.year:

            if curr_year == startdate.year:
                ms = [m for m in range(1,13) if m >= startdate.month]
            elif curr_year == enddate.year:
                ms = [m for m in range(1, 13) if m <= enddate.month]
            else:
                ms = list(range(1,13))

            curr_start = datetime(curr_year, ms[0],
                                  startdate.day if curr_year == startdate.year else ds[0])

            while curr_start.day not in ds:
                curr_start += timedelta(days=1)

            curr_end = datetime(curr_year, ms[-1], ds[-1])

            target_dir_year = os.path.join(target_path, str(curr_year))
            os.makedirs(target_dir_year, exist_ok=True)

            fname = f"{curr_start.strftime('%Y%m%d')}_{curr_end.strftime('%Y%m%d')}.zip"
            print(fname)

            _ = download_c3ssm(c, sensor, years=[curr_year], months=ms,
                               days=ds, version=version,
                               aggregation=aggregation, max_retries=3,
                               target_dir=target_dir_year, temp_filename=fname,
                               keep_original=keep_original)

            curr_year += 1

def mkdate(datestring:str) -> datetime:
    # datestring to datetime
    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')

def parse_args(args):
    """
    Parse command line parameters for recursive download
    Parameters
    ----------
    args : list
        Command line parameters as list of strings
    Returns
    ----------
    clparams : argparse.Namespace
        Parsed command line parameters
    """

    parser = argparse.ArgumentParser(
        description="Download C3S SM images between two dates. "
                    "Before this program can be used, you have to register at the CDS "
                    "and setup your .cdsapirc file as described here: "
                    "https://cds.climate.copernicus.eu/api-how-to")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the downloaded data will be stored.')
    parser.add_argument("-s", "--start", type=mkdate,
                        default='1979-01-01',
                        help=("Startdate in format YYYY-MM-DD. "
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate,
                        default=datetime.now().date().isoformat(),
                        help=("Enddate in format YYYY-MM-DD. "
                              "If not given then the current date is used."))
    parser.add_argument("-agg", "--aggregation", type=str, default='daily',
                        help=("The C3S SM sensor product aggregate to download. "
                              "Choose one of 'daily', 'dekadal', 'monthly'. "
                              "Default is 'daily'."))
    parser.add_argument("-sp", "--sensor", type=str, default='combined',
                        help=("The C3S SM sensor product to download. "
                              "Choose one of 'combined', 'active', 'passive'. "
                              "Default is 'combined'."))
    parser.add_argument("-vers", "--version", type=str, default='v201706.0.0',
                        help=("The C3S SM product version to download. "
                              "Choose one that is on the CDS, e.g. 'v201706.0.0', 'v201912.0.0', ..."
                              "Default is 'v201706.0.0'"))
    parser.add_argument("-keep", "--keep_original", type=bool, default=False,
                        help=("Also keep the originally, temporarily downloaded image stack instead of deleting it "
                              "after extracting single images. Default is False."))

    args = parser.parse_args(args)

    print(f"Downloading C3S CDR/ICDR SM {args.aggregation} {args.sensor} "
          f"from {args.start.isoformat()} to {args.end.isoformat()} into {args.localroot}")

    return args


def main(args):
    args = parse_args(args)
    download_and_extract(target_path=args.localroot,
                         startdate=args.start,
                         enddate=args.end,
                         sensor=args.sensor,
                         aggregation=args.aggregation,
                         version=args.version,
                         keep_original=args.keep_original)


def run():
    main(sys.argv[1:])