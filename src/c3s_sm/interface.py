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
Readers for the C3S soil moisture proudct daily, dekadal (10-daily) and monthly images as well
as for timeseries generated using this module
'''

import pandas as pd
import os
import netCDF4 as nc
import numpy as np
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from pygeobase.object_base import Image
from pygeobase.io_base import ImageBase
from pygeobase.io_base import MultiTemporalImageBase
from pygeogrids.netcdf import load_grid

from netCDF4 import Dataset
from pynetcf.time_series import GriddedNcOrthoMultiTs
from datetime import datetime
from parse import parse
from c3s_sm.grid import C3SCellGrid, C3SLandGrid
from collections import OrderedDict

c3s_filename_template = \
           '{datetime}000000-{sub_prod}-{version}.{sub_version}.nc'

class C3STs(GriddedNcOrthoMultiTs):
    """
    Module for reading C3S time series in netcdf format.
    """
    _t0_ref = ('t0', datetime(1970,1,1,0,0,0))

    def __init__(self, ts_path, grid_path=None, index_add_time=False, drop_tz=True,
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
        index_add_time : bool, optional (default: False)
            Add time stamps to the time series index. Needs the variable t0
            from the netcdf files.
        drop_tz : bool, optional (default: True)
            Remove any time zone information from the data frame

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

        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")

        grid = load_grid(grid_path)

        super(C3STs, self).__init__(ts_path, grid=grid, **kwargs)

        self.index_add_time = index_add_time
        self.drop_tz = drop_tz


    def _read_gp(self, gpi, **kwargs):
        """Read a single point from passed gpi or from passed lon, lat """
        # override the _read_gp function from parent class, to add dropna functionality

        ts = super(C3STs, self)._read_gp(gpi, **kwargs)
        if ts is None:
            return None

        if not self.drop_tz:
            ts.index = ts.index.tz_localize('UTC')
        else:
            if (hasattr(ts.index, 'tz') and (ts.index.tz is not None)):
                ts.index = ts.index.tz_convert(None)
        
        ts = ts.replace(-9999.0000, np.nan)

        return ts

    def read_cell_file(self, cell, var='sm'):
        """
        Read all data for a single variable from a file, fastest option but
        does not consider any flags etc but simply extracts the passed variable.

        Parameters
        ----------
        cell : int
            Cell / filename to read.
        var : str
            Name of the variable to extract from the cellfile.

        Returns
        -------
        data : np.array
            Data for var in cell
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
            data = data.replace(-9999.0000, np.nan)
            return data

    def read_cells(self, cells):
        """
        Iterate over all points in a cell and retrieve multiple variables.

        Parameters
        ----------
        cells: list
            List of cells. All points in the cell are read, each point
            is a dataframe.

        Returns
        -------
        points_in_cell_data : OrderedDict
            Dict where each key is a gpi and each value a data frame of all
            selected variables.
        """

        cell_data = OrderedDict()
        gpis, lons, lats = self.grid.grid_points_for_cell(list(cells))
        for gpi, lon, lat in zip(gpis, lons, lats):
            df = self.read(lon, lat)
            cell_data[gpi] = df
        return cell_data

    def _add_time(self, df:pd.DataFrame) -> pd.DataFrame:
        """ Add time stamps to time series index """
        t0 = self._t0_ref[0]
        if t0 in df.columns:
            dt = pd.to_timedelta(df[t0], unit='d')
            df['_datetime'] = pd.Series(index=df.index, data=self._t0_ref[1]) + dt
            df['_date'] = df.index
            df = df.set_index('_datetime')
            df = df[df.index.notnull()]
        else:
            raise ValueError('Variable t0 was not found, cannot add time stamps')

        return df

    def read(self, *args, **kwargs):
        """
         Read time series by grid point index, or by lonlat. Convert columns to
         ints if possible (if there are no Nans in it).
         Parameters
         ----------
         lon: float
             Location longitude
         lat : float
             Location latitude
         .. OR
         gpi : int
             Grid point Index
         Returns
         -------
         df : pd.DataFrame
             Time Series data at the selected location
         """
        ts = super(C3STs, self).read(*args, **kwargs)
        if self.index_add_time:
            ts = self._add_time(ts)
        return ts

class C3SImg(ImageBase):
    """
    Class to read a single C3S image (for one time stamp)
    """
    def __init__(self, filename, parameters='sm', mode='r',
                 grid=C3SCellGrid(None), array_1D=False):
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
        grid : pygeogrids.CellGrid, optional (default: C3SCellGrid)
            Grid that the image data is organised on, by default the global SMECV
            grid is used.
        array_1D : bool, optional (default: False)
            Read image as one dimensional array, instead of a 2D array
            Use this when using a subgrid.
        """

        super(C3SImg, self).__init__(filename, mode=mode)

        if not isinstance(parameters, list):
            parameters = [parameters]

        self.parameters = parameters
        self.grid = grid
        self.array_1D = array_1D

    def read(self, timestamp=None):
        """
        Reads a single C3S image.

        Parameters
        -------
        timestamp: datetime, optional (default: None)
            Timestamp for file to read. Pass None if file contains only 1 timestamp

        Returns
        -------
        image : Image
            Image object from netcdf content
        """

        ds = Dataset(self.filename, mode='r')

        param_img = {}
        img_meta = {'global': {}}

        if self.parameters[0] is None:
            parameters = ds.variables.keys()
        else:
            parameters = self.parameters

        for param in parameters:
            if param in ['lat', 'lon', 'time']: continue
            param_metadata = {}

            variable = ds.variables[param]

            for attr in variable.ncattrs():
                param_metadata.update({str(attr): getattr(variable, attr)})

            param_data = np.flipud(variable[0][:].filled()).flatten()

            param_img[str(param)] = param_data[self.grid.activegpis]
            img_meta[param] = param_metadata

        # add global attributes
        for attr in ds.ncattrs():
            img_meta['global'][attr] = ds.getncattr(attr)

        ds.close()

        if self.array_1D:
            return Image(self.grid.activearrlon, self.grid.activearrlat,
                         param_img, img_meta, timestamp)
        else:
            yres, xres = self.grid.shape
            for key in param_img:
                param_img[key] = param_img[key].reshape(xres, yres)

            return Image(self.grid.activearrlon.reshape(xres, yres),
                         self.grid.activearrlat.reshape(xres, yres),
                         param_img,
                         img_meta,
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

    def __init__(self, data_path, parameters='sm', subgrid=None, array_1D=False):
        """
        Parameters
        ----------
        data_path : str
            Path to directory where C3S images are stored
        parameters : list or str,  optional (default: 'sm')
            Variables to read from the image files.
        subgrid : grid, optional (default: None)
            Subset of the image to read
        array_1D : bool, optional (default: False)
            Flatten the read image to a 1D array instead of a 2D array
        """

        self.data_path = data_path
        ioclass_kwargs = {'parameters': parameters,
                          'subgrid' : subgrid,
                          'array_1D': array_1D}

        template = c3s_filename_template
        self.fname_args = self._parse_filename(template)
        filename_templ = template.format(**self.fname_args)

        subpath_templ = ['%Y']

        super(C3S_Nc_Img_Stack, self).__init__(path=data_path, ioclass=C3SImg,
                                               fname_templ=filename_templ ,
                                               datetime_format="%Y%m%d",
                                               subpath_templ=subpath_templ,
                                               exact_templ=True,
                                               ioclass_kws=ioclass_kwargs)

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

    @staticmethod
    def next_dekade(date:datetime) -> datetime:
        next = date + relativedelta(days=10)
        if next.month != date.month or next.day == 31:
            return date + relativedelta(day=1, months=1)
        else:
            return next

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

        if self.fname_args['temp_res'] == 'MONTHLY':
            next = lambda date : date + relativedelta(months=1)
        elif self.fname_args['temp_res'] == 'DAILY':
            next = lambda date : date + relativedelta(days=1)
        elif self.fname_args['temp_res'] == 'DEKADAL':
            if start_date.day not in [1,11,21]:
                raise ValueError(f'Invalid day for C3S dekadal product: {start_date.day}')
            next = self.next_dekade
        else:
            raise NotImplementedError

        timestamps = [start_date]
        while next(timestamps[-1]) <= end_date:
            timestamps.append(next(timestamps[-1]))

        return timestamps



if __name__ == '__main__':
    C3SImg()