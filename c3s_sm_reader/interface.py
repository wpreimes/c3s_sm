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

import inspect
import pandas as pd
import os
import netCDF4 as nc
import numpy as np
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from pygeobase.object_base import Image
from pygeobase.io_base import ImageBase
from pygeobase.io_base import MultiTemporalImageBase

from smecv_grid.grid import SMECV_Grid_v042
from netCDF4 import Dataset, num2date
from smecv_grid.grid import SMECV_Grid_v042 as esa_cci_sm_grid_v04_2 # todo replace this with the c3s grid package
from pynetcf.time_series import OrthoMultiTs
from pynetcf.time_series import IndexedRaggedTs, GriddedNcTs
from pygeogrids.grids import CellGrid
from datetime import datetime
from datetime import time as dt_time
from collections import Iterable

# FIXME: dynamic class name: Dataset_TempRes_Name_Product_Version#
'''
# Class name determines product it is applicable to. Should be of format:
		{product}_{fileformat}_{product_time_period}_{product_sub_type}
	where product is the product that it is applicable, i.e. cci, fileformat is the type of file that are being read,
	for example, netcdf, product_time_period is the period of the product, for example "daily" or "monthly" and
	product_sub_type is an optional addition to cover where other subdivisions of the product are used, for example,
	ICDR or TCDR.
'''


# TCDR timeseries readers-----------------------------------------------------------------------------------------------
class C33Ts(GriddedNcTs):
    """
    Module for reading C3S time series in netcdf format.
    """

    def __init__(self, path, mode='r', grid=None,
                 fn_format='{:04d}', remove_nans=True):

        self.remove_nans = remove_nans

        if grid is None:
            grid = esa_cci_sm_grid_v04_2()  # todo replace this with the c3s grid package

        super(C33Ts, self).__init__(path, grid=grid,
                                    ioclass=OrthoMultiTs,
                                    ioclass_kws={'read_bulk': True},
                                    mode=mode,
                                    fn_format=fn_format)

    def _read_gp(self, gpi, **kwargs):
        """Read a single point from passed gpi or from passed lon, lat """
        # override the _read_gp function from parent class, to add dropna functionality

        ts = super(C33Ts, self)._read_gp(gpi, **kwargs)
        if ts is None:
            return None

        if self.remove_nans:
            ts = ts.replace(-9999.0000, np.nan)

        ts.index = ts.index.tz_localize('UTC')

        return ts

    def read_cell(self, cell, var=None):
        """
        Read all time series for the selected cell

        Parameters
        -------
        cell: int
            Cell number as in the c3s grid
        var : str
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

    def write_gp(self, gp, data, **kwargs):
        # todo this should keep the global attributes of the image files
        """
        Method writing data for given gpi.

        Parameters
        ----------
        gp : int
            Grid point.
        data : pandas.DataFrame
            Time series data to write. Index has to be pandas.DateTimeIndex.
        """

        if 'time' in data.keys():
            data = data.drop('time', axis=1)
        data.index = data.index.tz_localize(None)  # todo do we need this?
        if self.mode == 'r':
            raise IOError("trying to write but file is in 'read' mode")

        self._open(gp)
        lon, lat = self.grid.gpi2lonlat(gp)
        ds = data.to_dict('list')
        for key in ds:
            ds[key] = np.array(ds[key])

        self.fid.write_ts(gp, ds, data.index.to_pydatetime(),
                          lon=lon, lat=lat, **kwargs)


class C3SImg(ImageBase):
    """
    Module for a single C3S image (for one time stamp)
    """

    def __init__(self, filename, mode='r', parameters='sm', array_1D=False):
        '''
        Parameters
        ----------
        filename : str
            Path to the file to read
        mode : str, optional (default: 'r')
            # FIXME: if this class is for reading only, we can remove this option?
            Mode, in which the file is opened
        parameters : str or Iterable, optional (default: 'sm')
            Names of parameters in the file to read.
            If None are passed, all are read.
        array_1D : bool, optional (default: False)
            Read image as one dimensional array, instead of a 2D array
        '''

        super(C3SImg, self).__init__(filename, mode=mode)

        if not isinstance(parameters, list):
            parameters = [parameters]

        self.parameters = parameters
        self.grid = SMECV_Grid_v042(subset_flag=None)  # todo: give the option to use the rainforest-masked grid?
        self.array_1D = array_1D

    def read(self, timestamp=None):
        """
        Reads a single C3S image.
        # FIXME: reading the metadata could be separated, or there could be an option to (de)activate it...

        Parameters
        -------
        timestamp: datetime
            # todo: we dont need this, because there is only 1 date per file

        Returns
        -------
        image : Image
            Image object from netcdf content
        """

        ds = Dataset(self.filename, mode='r')

        param_img = {}
        img_meta = {}

        file_meta = {} #FIXME: Include this as well?

        if self.parameters[0] is None:
            parameters = ds.variables.keys()
        else:
            parameters = self.parameters

        for param in parameters:
            param_metadata = {}

            variable = ds.variables[param]

            for attr in variable.ncattrs():
                param_metadata.update({str(attr): getattr(variable, attr)})

            #there is always only day per file?
            param_img[param] = variable[0][:].flatten().filled() # fixme: fill nans -9999 or smt else?

            img_meta[param] = param_metadata

        for attr in ds.ncattrs():
            file_meta[attr] = ds.getncattr(attr)

        ds.close()

        if self.array_1D:
            return Image(self.grid.activearrlon, self.grid.activearrlat,
                         param_img, img_meta, timestamp)
        else:
            for key in param_img:
                param_img[key] = param_img[key].reshape(720, 1440) # fixme, the resolution is always the same, grid is aways the global one?

            return Image(self.grid.activearrlon.reshape(720, 1440),
                         self.grid.activearrlat.reshape(720, 1440),
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
    # todo i think we need a separate one for monthly, dekdal and daily, but you may be able to change this
    '''#todo update documentation
    Class for reading lots of files based on dates.
    Class name determines product it is applicable to. Should be of format:
    {product}_{fileformat}_{product_time_period}_{product_sub_type}_images
    where product is the product that it is applicable, i.e. cci, fileformat is the type of file that are being read,
    for example, netcdf, product_time_period is the period of the product, for example "daily" or "monthly" and
    product_sub_type is an optional addition to cover where other subdivisions of the product are used, for example,
    ICDR or TCDR.

    #TODO - need to make this so coverts from the file of the input images to the generic template
    #todo write a check to make sure the file is the expected file type (i.e. check on version num or something like that)
    '''



    def __init__(self, data_path, parameters=['sm'], product='C3S', product_sensor_type='combined',
                 temp_res='D', product_sub_type='TCDR', version='v201801',sub_path = ['%Y'],
                 subgrid=None, array_1D=False):
        # FIXME: WHy all the paramters? We can just read them from the path that was passed?
        #FIXME what is produc
        # FIXME: is the subgrid needed?


        ioclass_kwargs = {'parameters': parameters,
                          #'subgrid' : subgrid,
                          'array_1D': array_1D}

        self.product_datatype_str = {'active': 'SSMS',
                                     'passive': 'SSMV',
                                     'combined': 'SSMV'}

        self.temp_res = temp_res

        temp_res_lut = {'D': 'DAILY', 'M': 'MONTHLY', '10D': 'DEKADAL'}
        fname_cont = [product,
                      '-SOILMOISTURE-L3S-',
                      self.product_datatype_str[product_sensor_type],
                      '-',
                      product_sensor_type.upper(),
                      '-',
                      temp_res_lut[self.temp_res],
                      '-{datetime}000000-',
                      product_sub_type,
                      '-',
                      version,
                      '.0.0.nc']

        filename_templ = ''.join(fname_cont)


        super(C3S_Nc_Img_Stack, self).__init__(path=data_path, ioclass=C3SImg, mode='r',
                                               fname_templ=filename_templ ,
                                               datetime_format="%Y%m%d",
                                               subpath_templ=sub_path,
                                               exact_templ=True,
                                               ioclass_kws=ioclass_kwargs)


    def tstamps_for_daterange(self, start_date, end_date):
        '''
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
        '''
        # FIXME: work directly with offset input

        if self.temp_res == 'M':
            next = lambda date : date + relativedelta(months=+1)
        elif self.temp_res == 'D':
            next = lambda date : date + relativedelta(days=+1)
        elif self.temp_res == '10D':
            next = lambda date : date + relativedelta(days=+10)
        else:
            raise NotImplementedError

        timestamps = [start_date]
        while next(timestamps[-1])  <= end_date:
            timestamps.append(next(timestamps[-1]))

        return timestamps






if __name__ == '__main__':
    afile = r"C:\Temp\tcdr\active_daily\1991\C3S-SOILMOISTURE-L3S-SSMS-ACTIVE-DAILY-19910805000000-TCDR-v201801.0.0.nc"
    img = C3SImg(afile, 'r', 'sm', True)
    image = img.read()

    afile = r"C:\Temp\tcdr\active_daily"
    ds = C3S_Nc_Img_Stack(afile, parameters=['sm'], product='C3S', product_sensor_type='active',
                          temp_res='D', product_sub_type='TCDR', version='v201801',
                          subgrid=None, array_1D=False)
    image = ds.read(datetime(1991,8,6))

    images = ds.iter_images(start_date=datetime(1991,8,5), end_date=datetime(1991,8,10))