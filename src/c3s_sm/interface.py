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

"""
Readers for the C3S soil moisture proudct daily, dekadal (10-daily) and monthly
images as well as for timeseries generated using this package.
"""

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

from netCDF4 import Dataset, date2num
from pynetcf.time_series import GriddedNcOrthoMultiTs
from datetime import datetime
from parse import parse
from c3s_sm.grid import C3SCellGrid
from collections import OrderedDict

from c3s_sm import dist_name, __version__

import warnings

c3s_filename_template = \
    '{product}-SOILMOISTURE-L3S-{data_type}-{sensor_type}-{temp_res}-' \
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

    def write_gp(self, gp, data, **kwargs):
        """
        Write gpi data into the correct file at the GPI location

        Parameters
        ----------
        gp : int
            GPI number
        data : pd.DataFrame
            DataFrame that contains the time series to write as columns
        """

        if 'time' in data.keys():
            data = data.drop('time', axis=1)
        data.index = data.index.tz_localize(None)
        if self.mode == 'r':
            raise IOError("Cannot write as file is in 'read' mode")

        self._open(gp)
        lon, lat = self.grid.gpi2lonlat(gp)
        ds = data.to_dict('list')
        for key in ds:
            ds[key] = np.array(ds[key])

        self.fid.write_ts(gp, ds, data.index.to_pydatetime(),
                          lon=lon, lat=lat, **kwargs)

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
        _df : pd.DataFrame
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

    def __init__(self, filename, parameters=None, mode='r',
                 grid=None, array_1D=False, float_fillval=np.nan):
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
        grid : pygeogrids.CellGrid, optional (default: None)
            Grid that the image data is organised on, if None is passed, the grid
            is generate from lat/lons in the netcdf file.
        array_1D : bool, optional (default: False)
            Read image as one dimensional array, instead of a 2D array
            Use this when using a subgrid.
        float_fillval : float or None, optional (default: np.nan)
            Fill Value for masked pixels, this is only applied to float variables.
            Therefore e.g. flag variables are never filled but use the fill value
            as in the metadata data.
        """

        super(C3SImg, self).__init__(filename, mode=mode)

        if not isinstance(parameters, list):
            parameters = [parameters]

        self.parameters = parameters
        self.grid = grid
        self.array_1D = bool(array_1D)

        self.float_fillval = float_fillval
        self.glob_attrs = None
        self.img = None

    def get_global_attrs(self, exclude=('history', 'NCO', 'netcdf_version_id',
        'contact', 'institution', 'creation_time')) -> dict :
        # read global attributes from netcdf image file
        return {k: v for k, v in self.glob_attrs.items() if k not in exclude}

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
        self.glob_attrs = ds.__dict__

        ds.set_auto_mask(True)
        ds.set_auto_scale(True)

        param_img = {}
        img_meta = {}

        if self.parameters[0] is None:
            parameters = ds.variables.keys()
        else:
            parameters = self.parameters

        for param in parameters:
            param_metadata = {}

            variable = ds.variables[param]

            if len(variable.dimensions) == 1: # for lon, lat, time
                continue

            for attr in variable.ncattrs():
                param_metadata.update({str(attr): getattr(variable, attr)})

            data = np.flipud(variable[0][:])

            fill_val = None
            if (self.float_fillval is not None):
                if issubclass(data.dtype.type, np.floating):
                    fill_val = self.float_fillval

            param_data = data.filled(fill_val).flatten()

            param_img[str(param)] = param_data[self.grid.activegpis]
            img_meta[param] = param_metadata

        ds.close()

        lats = np.flipud(self.grid.activearrlat)

        if self.array_1D:
            self.img = Image(self.grid.activearrlon, lats,
                             param_img, img_meta, timestamp)
        else:
            n_y, n_x = self.grid.shape
            for key in param_img:
                param_img[key] = np.flipud(param_img[key].reshape(n_y, n_x))

            self.img = Image(self.grid.activearrlon.reshape(n_y, n_x),
                             lats.reshape(n_y, n_x),
                             param_img,
                             img_meta,
                             timestamp)

        return self.img

    def write(self, image, **kwargs):
        """
        Write the image to a separate output path. E.g. after reading only
        a subset of the parameters, or when reading a spatial subset (with a
        subgrid). If there is already a file, the new image is appended along
        the time dimension.

        Parameters
        ----------
        image : str
            Path to netcdf file to create.
        kwargs
            Additional kwargs are given to netcdf4.Dataset
        """

        if self.img is None:
            raise IOError("No data found for current image, load data first")

        if self.img.timestamp is None:
            raise IOError("No time stamp found for current image.")

        lons = np.unique(self.img.lon.flatten())
        lats = np.flipud(np.unique(self.img.lat.flatten()))

        mode = 'w' if not os.path.isfile(image) else 'a'
        ds = Dataset(image, mode=mode, **kwargs)

        ds.set_auto_scale(True)
        ds.set_auto_mask(True)

        units = 'Days since 1970-01-01 00:00:00 UTC'

        if mode == 'w':
            ds.createDimension('timestamp', None)  # stack dim
            ds.createDimension('lat', len(lats))
            ds.createDimension('lon', len(lons))

            # this is not the obs time, but an image time stamp
            ds.createVariable('timestamp', datatype=np.double, dimensions=('timestamp',),
                              zlib=True, chunksizes=None)
            ds.createVariable('lat', datatype='float64', dimensions=('lat',), zlib=True)
            ds.createVariable('lon', datatype='float64', dimensions=('lon',), zlib=True)

            ds.variables['timestamp'].setncatts({'long_name': 'timestamp',
                                                'units': units})
            ds.variables['lat'].setncatts({'long_name': 'latitude', 'units': 'Degrees_North',
                                           'valid_range': (-90, 90)})
            ds.variables['lon'].setncatts({'long_name': 'longitude', 'units': 'Degrees_East',
                                           'valid_range': (-180, 180)})

            ds.variables['lon'][:] = lons
            ds.variables['lat'][:] = lats
            ds.variables['timestamp'][:] = np.array([])

            this_global_attrs = \
                OrderedDict([('subset_img_creation_time', str(datetime.now())),
                             ('subset_img_bbox_corners_latlon', f"{np.min(self.img.lon)},"
                                                                f"{np.min(self.img.lat)},"
                                                                f"{np.max(self.img.lon)},"
                                                                f"{np.max(self.img.lat)}"),
                             ('subset_software', f"{dist_name} | {__version__}")])
            glob_attrs = self.get_global_attrs()
            glob_attrs.update(this_global_attrs)
            ds.setncatts(glob_attrs)

        idx = ds.variables['timestamp'].shape[0]
        ds.variables['timestamp'][idx] = date2num(self.img.timestamp, units=units)

        for var, vardata in self.img.data.items():

            if var not in ds.variables.keys():
                ds.createVariable(var, vardata.dtype, dimensions=('timestamp', 'lat', 'lon'),
                                  zlib=True, complevel=6)
                ds.variables[var].setncatts(self.img.metadata[var])

            ds.variables[var][-1] = vardata

        ds.close()

    def close(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass


class C3SDs(MultiTemporalImageBase):
    """
    Class for reading multiple images and iterate over them.
    """

    def __init__(self, data_path, parameters=None, grid=C3SCellGrid(None),
                 array_1D=False):
        """
        Read multiple C3S SM files. Files are stored in annual folders in data_path.
        We use the time stamp in the file name to read data for a certain date.
        All images between two dates are read by iterating over all time stamps.

        Parameters
        ----------
        data_path : str
            Path to directory where C3S images are stored
        parameters : {list,str,None},  optional (default: None)
            Variables to read from the image files. By default all parameters
            are taken from the image file.
        grid : CelLGrid, optional (default: None)
            Subset of the image to read
        array_1D : bool, optional (default: False)
            Flatten the read image to a 1D array instead of a 2D array
        """
        subpath_templ = ['%Y']

        self.data_path = data_path
        ioclass_kwargs = {'parameters': parameters,
                          'grid' : grid,
                          'array_1D': array_1D}

        template = c3s_filename_template
        self.fname_args = self._parse_filename(template)
        filename_templ = template.format(**self.fname_args)


        super(C3SDs, self).__init__(path=data_path, ioclass=C3SImg,
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

    def write_multiple(self, root_path, start_date, end_date, stackfile='stack.nc',
                       **kwargs):
        """
        Create multiple netcdf files or a netcdf stack in the passed directoy for
        a range of time stamps. Note that stacking gets slower when the stack gets larger.
        Empty images (if no original data can be loaded) are excluded here as
        well.

        Parameters
        ----------
        root : str
            Directory where the files / the stack are/is stored
        start_date : datetime
            Start date of images to write down
        end_date
            Last date of images to write down
        stackfile : str, optional (default: 'stack.nc')
            Name of the stack file to create in root_path. If no name is passed
            we create single images instead of a stack with the same name as
            the original images (faster).
        kwargs:
            kwargs that are passed to the image reading function
        """

        timestamps = self.tstamps_for_daterange(start_date, end_date)
        for t in timestamps:
            self.read(t, **kwargs)
            if stackfile is None:
                subdir = os.path.join(root_path, str(t.year))
                if not os.path.exists(subdir): os.makedirs(subdir)
                filepath = os.path.join(subdir, os.path.basename(self.fid.filename))
            else:
                filepath = os.path.join(root_path, stackfile)
            print(f"{'Write' if not stackfile else 'Stack'} image for {str(t)}...")
            self.fid.write(filepath)

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

class C3S_Nc_Img_Stack(C3SDs):
    """ Old class name, kept for compatibility"""
    def __init__(self, data_path, parameters='sm', subgrid=None, array_1D=False):
        warnings.warn(DeprecationWarning, "C3S_Nc_Img_Stack is deprecated, use C3SDs instead")
        super(C3S_Nc_Img_Stack, self).__init__(data_path, parameters,
                                               grid=subgrid, array_1D=array_1D)

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    bbox = (-11, 34, 43, 71)
    grid = C3SCellGrid(None).subgrid_from_bbox(*bbox)


    img_path = r"R:\Datapool\C3S\02_processed\v201912\TCDR\060_dailyImages\passive"
    ds = C3SDs(img_path, grid=grid, parameters=None, array_1D=False)
    data = ds.read(datetime(2016,7,1))

    ds.write_multiple(root_path=r"C:\Temp\c3s\img",
                      start_date=datetime(2016,7,1), end_date=datetime(2016,7,10),
                      stackfile='stack.nc')
