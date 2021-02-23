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

import warnings
from netCDF4 import Dataset
from pynetcf.time_series import GriddedNcOrthoMultiTs
from datetime import datetime
from parse import parse

try:
    import xarray as xr
    xr_supported = True
except ImportError:
    xr_supported = False

fntempl = "C3S-SOILMOISTURE-L3S-SSM{unit}-{prod}-{temp}-{datetime}-{cdr}-{vers}.{subvers}.nc"


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
                 fillval=np.nan):
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
        fillval : flot or dict, optional (default: np.nan)
            Fill Value for masked pixels, if a dict is passed, this can be
            set for each parameter individually, otherwise it applies to all.
            Note that choosing np.nan can lead to a change in dtype for some
            (int) parameters.
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

        if isinstance(fillval, dict):
            self.fillval = fillval
            for p in self.parameters:
                if p not in self.fillval:
                    self.fillval[p] = None
        else:
            self.fillval ={p: fillval for p in self.parameters}

    def __read_empty_flat_image(self) -> (dict, dict):
        """
        Create an empty image for filling missing dates, this is necessary
        for reshuffling as img2ts cannot handle missing days.
        """
        self.image_missing = True

        return_img = {}
        return_metadata = {}

        yres, xres = self.grid.shape

        for param in self.parameters:
            if param in self.fillval.keys():
                fill_val = self.fillval[param]
            else:
                warnings.warn(f"No fill value defined, fill {param} with np.nan")
                fill_val = np.nan
            return_img[param] = np.full((yres, xres), fill_val).flatten()
            return_metadata[param] = {'image_missing': 1}

        return return_img, return_metadata

    def __read_flat_img(self) -> (dict, dict, dict, datetime):
        """
        Reads a single C3S image.
        """
        with Dataset(self.filename, mode='r') as ds:
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

                if (param in self.fillval) and (self.fillval[param] is not None):
                    try:
                        data = data.filled(fill_value=self.fillval[param])
                    except TypeError: # trying to fill with incompatible type, change type
                        dtype = type(self.fillval[param])
                        data = data.astype(dtype).filled(self.fillval[param])
                else:
                    data = data.filled()

                data = np.flipud(data).flatten()

                metadata['image_missing'] = 0

                param_img[parameter] = data
                param_meta[parameter] = metadata

            global_attrs = ds.__dict__
            global_attrs['timestamp'] = str(timestamp)

        return param_img, param_meta, global_attrs, timestamp

    def __mask_and_reshape(self,
                           data: dict,
                           shape_2d:tuple,
                           crop_2d=True) -> dict:
        """
        Takes the grid and drops points that are not active.
        for flattened arrays that means that only the active gpis are kept.
        for 2 arrays inactive gpis are set to nan.

        Parameters
        ----------
        data: dict
            Variable names and flattened image data.
        shape_2d : tuple
            2d shape of the original image.
        crop_2d : bool, optional (default: True)
            If the data is not flattened, crop the 2d images to the area where
            actual data is, i.e. remove the as many nans around the data.

        Returns
        -------
        dat : dict
            Masked, reshaped and potentially cropped data.
        """

        # check if flatten. if flatten, dont crop and dont reshape
        # if not flatten, reshape based on grid shape.

        # select active gpis
        for param, dat in data.items():
            if self.flatten:
                dat = dat[self.grid.activegpis]
            else:
                dat[~self.grid.activegpis] = self.fillval[param]
                dat.reshape(self.grid.shape)

        if not self.flatten:

        if crop_2d:
            firstcol = nancols.argmin()  # 5, the first index where not NAN
            firstrow = nanrows.argmin()  # 7


    def read(self, timestamp=None):
        """
        Read a single SMOS image, if it exists, otherwise fill an empty image
        """
        try:
            data, var_meta, glob_meta, img_timestamp = self.__read_flat_img()
        except IOError:
            warnings.warn(f'Error loading image for {os.path.join(self.path, self.fname)}. '
                          'Generating empty image instead')
            data, var_meta = self.__read_empty_flat_image()
            global_meta, img_timestamp = {}, None

        if timestamp is not None:
            if img_timestamp is None:
                img_timestamp = timestamp
            assert img_timestamp == timestamp, "Time stamps do not match"

        data = self.__mask_and_reshape(data, crop_2d=True)

        if self.flatten:
            return Image(self.grid.activearrlon,
                         np.flipud(self.grid.activearrlat),
                         data,
                         var_meta,
                         timestamp)
        else:
            if len(self.grid.shape) != 2:
                raise ValueError(
                    "Reading 2d image needs grid with 2d shape"
                    "You can either use the global grid without subsets,"
                    "or make sure that you create a subgrid from bbox in"
                    "an area where no gpis are missing.")
            else:
                rows, cols = self.grid.shape

            for key in data:
                data[key] = data[key].reshape(rows, cols)

            return Image(self.grid.activearrlon.reshape(rows, cols),
                         self.grid.activearrlat.reshape(rows, cols),
                         data,
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

    def __init__(self,
                 data_path,
                 parameters='sm',
                 grid=SMECV_Grid_v052(None),
                 flatten=False,
                 solve_ambiguity='sort_last',
                 subpath_templ=('%Y',),
                 float_fillval=np.nan):
        """
        Parameters
        ----------
        data_path : str
            Path to directory where C3S images are stored
        parameters : list or str,  optional (default: 'sm')
            Variables to read from the image files.
        grid : pygeogrids.CellGrid, optional (default: SMECV_Grid_v052(None)
            Subset of the image to read
        array_1D : bool, optional (default: False)
            Flatten the read image to a 1D array instead of a 2D array
        solve_ambiguity : str, optional (default: 'latest')
            Method to solve ambiguous time stamps, e.g. if a reprocessing
            was performed.
                - error: raises error in case of ambiguity
                - sort_last (default): uses the last file when sorted by file
                    name, in case that multiple files are found.
                - sort_first: uses the first file when sorted by file name
                    in case that multiple files are found.
        subpath_templ : list, optional (default: ['%Y'])
            List of subdirectory names to build file paths.
        float_fillval : float or None, optional (default: np.nan)
            Fill Value for masked pixels, this is only applied to float variables.
            Therefore e.g. mask variables are never filled but use the fill value
            as in the data.
        """

        self.data_path = data_path
        ioclass_kwargs = {'parameters': parameters,
                          'grid' : grid,
                          'flatten': flatten,
                          'float_fillval': float_fillval}

        self.fname_args = self._parse_filename(fntempl)
        self.solve_ambiguity = solve_ambiguity
        fn_args = self.fname_args.copy()
        fn_args['subvers'] = '*'
        fn_args['cdr'] = '*'
        filename_templ = fntempl.format(**fn_args)

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
                              f' Sort and use last: {filename[-1]}, skipped {filename[:-1]}')
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

    def read_cell(self, cell, var='sm') -> pd.DataFrame:
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

    def read_cell_cube(self, cell:int, dt_index:pd.Index, params:list,
                       param_fill_val: dict = None, param_scalf: dict = None,
                       jd0_unit='datetime', to_replace=None,
                       bit_valid_range=None, bit_rainforest=None,
                       as_xr=False):
        """
        Read a regular subcube of cell data. I.e. missing GPIs (and cells)
        are filled with the passed fill values. Returned data is always of
        shape (dt_index.size, 20, 20) for 5DEG cells.

        Parameters
        ----------
        cell : int
            Number of the cell (file) to read.
        dt_index : pd.Index
            DateTime index that is used in case a point has no data.
        params : list
            List of parameter names to read from file
        param_fill_val : dict, optional (default: None)
            Parameter names and fill values to use in the loaded time series
        param_scalf : dict, optional (default: None)
            Parameter names and scale factors, i.e. values that a parameter
            time series is multiplied with after reading.
        jd0_unit : str, optional (default: None)
            Unit to convert jd to.
            None to use the orignal values, datetime to convert to datetime
            or a string that is given as unit to date2num
        to_replace : dict, optional (default: None)
            See read_agg_cell_data fuction
        bit_valid_range : int, optional (default: None)
            SM values > 100 and < 0 are replaced with fill values for ALL 3 products.
            If a bit is passed here (e.g. bit_out_of_range, e.g. 4), the bit is
            added to the flag column value.
        bit_rainforest : int, optional (default: None)
            bit flag that defines rainforest points (dense vegetation, e.g. 2).
            If None is passed the original flag values are kept.
            Replace sm/sm_uncertainty values with NaN for all points that
            are marked as rainforest in grid. Add dense veg bit to flag.
        as_xr : bool, optional (default: False)
            Return data as xarray dataset (instead of a dictionary)

        Returns
        -------
        data : xr.Dataset or dict
        coords : dict, optional (only when as_xr is false)
            Coordinates of the pixels

        """
        if not xr_supported:
            print("xarray is not installed.")
            return

        file_path = os.path.join(self.path, '{}.nc'.format("%04d" % (cell,)))
        ds = xr.open_dataset(file_path)

    def iter_ts(self, **kwargs):
        pass

    def write_ts(self, *args, **kwargs):
        pass

if __name__ == '__main__':
    img = C3S_Nc_Img_Stack(r"C:\Temp\delete_me\c3s_sm\img",
                           parameters=['sm', 'flag'])
    img.read(datetime(2002,1,1))

