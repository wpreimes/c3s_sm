# The MIT License (MIT)
#
# Copyright (c) 2018, TU Wien
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Readers for the C3S soil moisture products daily, dekadal (10-daily) and monthly
images as well as for timeseries generated using this module
'''

import pandas as pd
import os
import netCDF4 as nc
import numpy as np
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from netCDF4 import num2date

from smecv_grid.grid import SMECV_Grid_v052
from pygeobase.object_base import Image
from pygeobase.io_base import ImageBase
from pygeobase.io_base import MultiTemporalImageBase
from pygeogrids.netcdf import load_grid
from pygeogrids.grids import CellGrid

import warnings
from netCDF4 import Dataset
from pynetcf.time_series import GriddedNcOrthoMultiTs
from datetime import datetime
from parse import parse
import glob
from typing import Union

fntempl = "C3S-SOILMOISTURE-L3S-SSM{unit}-{prod}-{temp}-{datetime}-{cdr}-{vers}.{subvers}.nc"

try:
    import xarray as xr
    import dask
    from dask.diagnostics import ProgressBar
    xr_supported = True
except ImportError:
    xr_supported = False


class C3STs(GriddedNcOrthoMultiTs):
    """
    Module for reading C3S time series in netcdf format.
    """

    def __init__(self, ts_path, grid_path=None, remove_nans=False, drop_tz=True,
                 **kwargs):

        """
        Class for reading C3S SM time series after reshuffling.

        Parameters
        ----------
        ts_path : str
            Directory where the netcdf time series files are stored
        grid_path : str, optional (default: None)
            Path to grid file, that is used to organize the location of time
            series to read. If None is passed, grid.nc is searched for in the
            ts_path.
        remove_nans : bool, optional (default: False)
            Replace -9999 with np.nan in time series
        trop_tz: bool, optional (default: True)
            Drop time zone information from time series

        Optional keyword arguments that are passed to the Gridded Base:
        ------------------------------------------------------------------------
            parameters : list, optional (default: None)
                Specific variable names to read, if None are selected, all are read.
            offsets : dict, optional (default:None)
                Offsets (values) that are added to the parameters (keys)
            scale_factors : dict, optional (default:None)
                Offset (value) that the parameters (key) is multiplied with
            ioclass_kws: dict
                Optional keyword arguments to pass to OrthoMultiTs class:
                ----------------------------------------------------------------
                    read_bulk : boolean, optional (default:False)
                        if set to True the data of all locations is read into memory,
                        and subsequent calls to read_ts read from the cache and not from disk
                        this makes reading complete files faster#
                    read_dates : boolean, optional (default:False)
                        if false dates will not be read automatically but only on specific
                        request useable for bulk reading because currently the netCDF
                        num2date routine is very slow for big datasets
        """

        self.remove_nans = remove_nans

        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")

        grid = load_grid(grid_path)

        self.drop_tz = drop_tz
        super(C3STs, self).__init__(ts_path, grid=grid, **kwargs)

    def _read_gp(self, gpi, **kwargs):
        """Read a single point from passed gpi or from passed lon, lat """
        # override the _read_gp function from parent class, to add dropna functionality

        ts = super(C3STs, self)._read_gp(gpi, **kwargs)
        if ts is None:
            return None

        if self.remove_nans:
            ts = ts.replace(-9999.0000, np.nan)

        if not self.drop_tz:
            ts.index = ts.index.tz_localize('UTC')
        else:
            if (hasattr(ts.index, 'tz') and (ts.index.tz is not None)):
                ts.index = ts.index.tz_convert(None)

        return ts

    def read_cell(self, cell, var='sm'):
        """
        Read all time series for a single variable in the selected cell.

        Parameters
        -------
        cell: int
            Cell number as in the c3s grid
        var : str, optional (default: 'sm')
            Name of the variable to read.
        """

        file_path = os.path.join(self.path, '{}.nc'.format("%04d" % (cell,)))
        with nc.Dataset(file_path) as ncfile:
            loc_id = ncfile.variables['location_id'][:]
            time = ncfile.variables['time'][:]
            unit_time = ncfile.variables['time'].units
            delta = lambda t: timedelta(t)
            vfunc = np.vectorize(delta)
            since = pd.Timestamp(unit_time.split('since ')[1])
            time = since + vfunc(time)

            variable = ncfile.variables[var][:]
            variable = np.transpose(variable)
            data = pd.DataFrame(variable, columns=loc_id, index=time)
            if self.remove_nans:
                data = data.replace(-9999.0000, np.nan)
            return data


class C3SImg(ImageBase):
    """
    Class to read a single C3S image (for one time stamp)
    """
    def __init__(self,
                 filename,
                 parameters=None,
                 mode='r',
                 grid=SMECV_Grid_v052(None),
                 flatten=False,
                 float_fillval=np.nan):
        """
        Parameters
        ----------
        filename : str
            Path to the file to read
        parameters : str or Iterable, optional (default: 'sm')
            Names of parameters in the file to read.
            If None are passed, all are read.
        mode : str, optional (default: 'r')
            Netcdf file mode, choosing something different to r may delete data.
        grid : pygeogrids.CellGrid, optional (default: SMECV_Grid_v052(None))
            Subgrid of point to read the data for, to read 2d arrays, this
            must have a 2d shape assigned.
        flatten: bool, optional (default: False)
            If set then the data is read into 1D arrays. This is used to e.g
            reshuffle the data for a subset of points.
        float_fillval : float or None, optional (default: np.nan)
            Fill Value for masked pixels, this is only applied to float variables.
            Therefore e.g. mask variables are never filled but use the fill value
            as in the data.
        """
        self.path = os.path.dirname(filename)
        self.fname = os.path.basename(filename)

        super(C3SImg, self).__init__(os.path.join(self.path, self.fname), mode=mode)

        if parameters is None:
            parameters = []
        if type(parameters) != list:
            parameters = [parameters]

        self.parameters = parameters
        self.grid = grid
        self.flatten = flatten

        self.grid = grid

        self.image_missing = False
        self.img = None  # to be loaded
        self.glob_attrs = None

        self.float_fillval = float_fillval

    def __read_empty(self) -> (dict, dict):
        """
        Create an empty image for filling missing dates, this is necessary
        for reshuffling as img2ts cannot handle missing days.
        """
        self.image_missing = True

        return_img = {}
        return_metadata = {}

        yres, xres = self.grid.shape

        for param in self.parameters:
            data = np.full((yres, xres), np.nan)
            return_img[param] = data.flatten()
            return_metadata[param] = {'image_missing': 1}

        return return_img, return_metadata

    def __read_img(self) -> (dict, dict, dict, datetime):
        """
        Reads a single C3S image.
        """
        ds = Dataset(self.filename, mode='r')
        timestamp = num2date(ds['time'], ds['time'].units,
                             only_use_cftime_datetimes=True,
                             only_use_python_datetimes=False)

        assert len(timestamp) == 1, "Found more than 1 time stamps in image"
        timestamp = timestamp[0]

        param_img = {}
        param_meta = {}

        if len(self.parameters) == 0:
            # all data vars, exclude coord vars
            self.parameters = [k for k in ds.variables.keys()
                               if k not in ds.dimensions.keys()]

        parameters = list(self.parameters)

        for parameter in parameters:
            metadata = {}
            param = ds.variables[parameter]
            data = param[:]

            # read long name, FillValue and unit
            for attr in param.ncattrs():
                metadata[attr] = param.getncattr(attr)

            if self.float_fillval is not None:
                if issubclass(data.dtype.type, np.floating):
                    data = data.filled(fill_value=self.float_fillval)
            else:
                data = data.filled()

            metadata['image_missing'] = 0

            param_img[parameter] = data
            param_meta[parameter] = metadata

        global_attrs = ds.__dict__
        global_attrs['timestamp'] = str(timestamp)
        ds.close()

        return param_img, param_meta, global_attrs, timestamp

    def read(self):
        """
        Read a single SMOS image, if it exists, otherwise fill an empty image
        """
        try:
            dat, var_meta, glob_meta, timestamp  = self.__read_img()
        except IOError:
            warnings.warn(f'Error loading image for {os.path.join(self.path, self.fname)}. '
                          'Generating empty image instead')
            dat, var_meta = self.__read_empty()
            global_meta, timestamp = {}, None

        if self.flatten:
            return Image(self.grid.activearrlon,
                         self.grid.activearrlat, # flip?
                         dat, # flip?
                         var_meta,
                         timestamp)
        else:
            yres, xres = self.grid.shape
            for key in dat:
                dat[key] = dat[key].reshape(xres, yres)

            return Image(self.grid.activearrlon.reshape(xres, yres),
                         self.grid.activearrlat.reshape(xres, yres), # flip?
                         dat, # flip?
                         var_meta,
                         timestamp)


    def write(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass

class C3S_Nc_Img_Stack(MultiTemporalImageBase):
    """
    Class for reading multiple images and iterate over them.
    """

    def __init__(self, data_path, parameters='sm', subgrid=SMECV_Grid_v052(None),
                 array_1D=False, solve_ambiguity='sort_last', float_fillval=np.nan):
        """
        Parameters
        ----------
        data_path : str
            Path to directory where C3S images are stored
        parameters : list or str,  optional (default: 'sm')
            Variables to read from the image files.
        subgrid : pygeogrids.CellGrid, optional (default: SMECV_Grid_v052(None)
            Subset of the image to read
        array_1D : bool, optional (default: False)
            Flatten the read image to a 1D array instead of a 2D array
        solve_ambiguity : str, optional (default: 'latest')
            Method to solve ambiguous time stamps, e.g. if a reprocessing
            was performed.
                error: raises error in case of ambiguity
                sort_last: uses the last file when sorted by file name,
                sort_first: uses the first file when sorted by file name,
        """

        self.data_path = data_path
        ioclass_kwargs = {'parameters': parameters,
                          'subgrid' : subgrid,
                          'array_1D': array_1D}

        self.fname_args = self._parse_filename(fntempl)
        self.solve_ambiguity = solve_ambiguity
        fn_args = self.fname_args.copy()
        fn_args['subvers'] = '*'
        fn_args['cdr'] = '*'
        filename_templ = fntempl.format(**fn_args)

        subpath_templ = ['%Y']

        super(C3S_Nc_Img_Stack, self).__init__(path=data_path, ioclass=C3SImg,
                                               fname_templ=filename_templ ,
                                               datetime_format="%Y%m%d%H%M%S",
                                               subpath_templ=subpath_templ,
                                               exact_templ=False,
                                               ioclass_kws=ioclass_kwargs)

    def _build_filename(self, timestamp:datetime, custom_templ:str=None,
                        str_param:dict=None):
        """
        This function uses _search_files to find the correct
        filename and checks if the search was unambiguous.

        Parameters
        ----------
        timestamp: datetime
            datetime for given filename
        custom_tmpl : string, optional
            If given the fname_templ is not used but the custom_templ. This
            is convenient for some datasets where not all file names follow
            the same convention and where the read_image function can choose
            between templates based on some condition.
        str_param : dict, optional
            If given then this dict will be applied to the fname_templ using
            the fname_templ.format(**str_param) notation before the resulting
            string is put into datetime.strftime.
        """
        filename = self._search_files(timestamp, custom_templ=custom_templ,
                                      str_param=str_param)
        if len(filename) == 0:
            raise IOError("No file found for {:}".format(timestamp.ctime()))
        if len(filename) > 1:
            if self.solve_ambiguity == 'sort_last':
                warnings.warn(f'Ambiguous file for {str(timestamp)} found.'
                              f' Sort and use last: {filename[-1]}')
                filename = [filename[-1]]
            elif self.solve_ambiguity == 'sort_first':
                warnings.warn(f'Ambiguous file for {str(timestamp)} found.'
                              f' Sort and use first: {filename[0]}')
                filename = [filename[0]]
            else:
                raise IOError(
                    "File search is ambiguous {:}".format(filename))

        return filename[0]

    def _parse_filename(self, template):
        """
        Search a file in the passed directory and use the filename template to
        to read settings.

        Parameters
        -------
        template : str
            Template for all files in the passed directory.

        Returns
        -------
        parse_result : parse.Result
            Parsed content of filename string from filename template.
        """

        for curr, subdirs, files in os.walk(self.data_path):
            for f in files:
                file_args = parse(template, f)
                if file_args is None:
                    continue
                else:
                    file_args = file_args.named
                    file_args['datetime'] = '{datetime}'
                    return file_args

        raise IOError('No file name in passed directory fits to template')


    def tstamps_for_daterange(self, start_date, end_date):
        """
        Return dates in the passed period, with respect to the temp resolution
        of the images in the path.

        Parameters
        ----------
        start_date: datetime
            start of date range
        end_date: datetime
            end of date range

        Returns
        -------
        timestamps : list
            list of datetime objects of each available image between
            start_date and end_date
        """

        if self.fname_args['temp'] == 'MONTHLY':
            next = lambda date : date + relativedelta(months=1)
        elif self.fname_args['temp'] == 'DAILY':
            next = lambda date : date + relativedelta(days=1)
        elif self.fname_args['temp'] == 'DEKADAL':
            next = lambda date : date + relativedelta(days=10)
        else:
            raise NotImplementedError

        timestamps = [start_date]
        while next(timestamps[-1]) <= end_date:
            timestamps.append(next(timestamps[-1]))

        return timestamps

class C3S_DataCube:
    """
    TODO
    """
    def __init__(self,
                 data_root,
                 grid=None, # todo: should use data from files.
                 parameters='sm',
                 clip_dates=None,
                 chunks: Union[str, dict]='space',
                 parallel=True,
                 **kwargs):
        """
        TODO
        """
        if isinstance(chunks, str):
            if chunks.lower() == 'space':
                chunks = dict(lon=100, lat=100, time=None)  # time series optimised
            elif chunks.lower() == 'time':
                chunks = dict(time=500)
            else:
                raise ValueError("Pass 'space' or 'time'")

        self.parameters = list(np.atleast_1d(parameters))
        if grid is None:
            self.grid = SMECV_Grid_v052(None)
        else:
            self.grid = load_grid(grid)

        self.root_path = data_root

        if clip_dates is not None:
            start_date = pd.to_datetime(clip_dates[0])
            end_date = pd.to_datetime(clip_dates[1])
        else:
            start_date = end_date = None

        files = self._filter_files(start_date, end_date)

        drop_vars = []
        with Dataset(files[0]) as ds0:
            for var in ds0.variables.keys():
                if var not in ds0.dimensions.keys() and var not in self.parameters:
                    drop_vars.append(var)

        with ProgressBar():
            self.ds = xr.open_mfdataset(files,
                                        data_vars='minimal',
                                        concat_dim='time',
                                        parallel=parallel,
                                        engine='netcdf4',
                                        chunks=chunks,
                                        drop_variables=drop_vars,
                                        **kwargs)

    def _filter_files(self, start_date:datetime=None, end_date:datetime=None) -> list:
        if start_date is None:
            start_date = datetime(1978, 1, 1)
        if end_date is None:
            end_date = datetime(2100,1,1)

        files = []
        allfiles = glob.glob(os.path.join(self.root_path, '**', '**.nc'))

        for fname in allfiles:
            fn_comps = parse(fntempl, os.path.basename(fname))
            dt = pd.to_datetime(fn_comps['datetime'])
            if dt >= start_date and dt <= end_date:
                files.append(fname)

        return files

    def _read_gp(self,
                 gpi: int) -> pd.DataFrame:

        # todo :load a chunk here to make ts extraction faster and keep it stored for subsequent calls.
        row, col = self.grid.gpi2rowcol(gpi)
        ts_data = self.ds.isel({'lat': row, 'lon': col})
        ts_data = ts_data.drop_vars(('lat', 'lon')).to_dataframe()
        return ts_data

    def read_img(self,
                 time: Union[str, datetime]) -> Image:
        time = pd.to_datetime(time)
        data = self.ds.sel({'time': time})

        vars = [d for d in list(data.variables.keys()) if d not in list(data.coords.keys())]

        return Image(lon=data['lon'].values,
                     lat=data['lat'].values,
                     data={v: data[v].values for v in vars},
                     metadata={v: data[v].attrs for v in vars},
                     timestamp=time,
                     timekey='time')

    def read_ts(self,
                *args,
                max_dist=np.inf):

        if len(args) == 1:
            data = self._read_gp(args[0])
        elif len(args) == 2:
            gpi, dist = self.grid.find_nearest_gpi(args[0], args[1], max_dist=max_dist)
            if hasattr(gpi, '__len__') and (len(gpi) == 0):
                data = None
            else:
                data = self._read_gp(gpi)
        else:
            raise ValueError("Wrong number of arguments passed, either pass 1 gpi"
                             " or two coordinates (lon, lat)")

        return data

    def write_stack(self, out_file, **kwargs):
        vars = [v for v in list(self.ds.variables.keys()) if v not in self.ds.coords.keys()]

        encoding = {v : {'zlib': True, 'complevel': 6} for v in vars}

        with ProgressBar():
            self.ds.to_netcdf(out_file, encoding=encoding, **kwargs)

if __name__ == '__main__':
    ds = C3S_DataCube("/home/wolfgang/data-read/temp/c3s",
                      chunks=None, clip_dates=('2020-01-01', '2020-12-31'))
    #ts = ds.read_ts(45,15)
    for gpi in ds.grid.grid_points_for_cell(2244)[0]:
        ts = ds.read_ts(gpi)
        print(ts)

    for t in ['2020-05-01', '2020-05-02', '2020-05-03']:
        img = ds.read_img(t)
        print(img)
