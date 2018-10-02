# -*- coding: utf-8 -*-


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
from smecv_grid.grid import SMECV_Grid_v042 as esa_cci_sm_grid_v04_2  # todo replace this with the c3s grid package
from pynetcf.time_series import OrthoMultiTs
from pynetcf.time_series import IndexedRaggedTs, GriddedNcTs
from pygeogrids.grids import CellGrid
from datetime import datetime
from datetime import time as dt_time
from collections import Iterable



# TCDR timeseries readers-----------------------------------------------------------------------------------------------
class c3s_sm_ts(GriddedNcTs) :

	def __init__(self, path, mode='r', grid=None,
				 fn_format='{:04d}', remove_nans=True) :

		self.remove_nans = remove_nans

		if grid is None :
			grid = esa_cci_sm_grid_v04_2()  # todo replace this with the c3s grid package

		super(c3s_sm_ts, self).__init__(path, grid=grid,
																  ioclass=OrthoMultiTs,
																  ioclass_kws={
																	  'read_bulk' : True},
																  mode=mode,
																  fn_format=fn_format)

	def _read_gp(self, gpi, **kwargs) :

		ts = super(c3s_sm_ts, self)._read_gp(gpi, **kwargs)
		if ts is None :
			return None

		if self.remove_nans:
			ts = ts.replace(-9999.0000, np.nan)

		ts.index = ts.index.tz_localize('UTC')

		return ts


	def read_cell(self, cell, var) :
		file_path = os.path.join(self.path, '{}.nc'.format("%04d" % (cell,)))
		with nc.Dataset(file_path) as ncfile :
			loc_id = ncfile.variables['location_id'][:]
			time = ncfile.variables['time'][:]
			unit_time = ncfile.variables['time'].units
			delta = lambda t : timedelta(t)
			vfunc = np.vectorize(delta)
			since = pd.Timestamp(unit_time.split('since ')[1])
			time = since + vfunc(time)
			variable = ncfile.variables[var][:]
			variable = np.transpose(variable)
			data = pd.DataFrame(variable, columns=loc_id, index=time)
			if self.remove_nans :
				data = data.replace(-9999.0000, np.nan)
			return data


	def write_gp(self, gp, data, **kwargs) :
		#todo this should keep the global attributes of the image files
		"""
		Method writing data for given gpi.

		Parameters
		----------
		gp : int
			Grid point.
		data : pandas.DataFrame
			Time series data to write. Index has to be pandas.DateTimeIndex.
		"""

		if 'time' in data.keys() :
			data = data.drop('time', axis=1)
		data.index = data.index.tz_localize(None) #todo do we need this?
		if self.mode == 'r' :
			raise IOError("trying to write but file is in 'read' mode")

		self._open(gp)
		lon, lat = self.grid.gpi2lonlat(gp)
		ds = data.to_dict('list')
		for key in ds :
			ds[key] = np.array(ds[key])

		self.fid.write_ts(gp, ds, data.index.to_pydatetime(),
						  lon=lon, lat=lat, **kwargs)




# TCDR single image readers ---------------------------------------------------------------------------------------------
class c3s_sm_daily_img(ImageBase):
    # todo can we combine for daily, dekal and monthly?
    '''#todo update documentation
    Class for reading a single ESA CCI SM image (for one timestamp)
    Class name determines product it is applicable to. Should be of format:
    {product}_{fileformat}_{product_time_period}_{product_sub_type}
    where product is the product that it is applicable, i.e. cci, fileformat is the type of file that are being read,
    for example, netcdf, product_time_period is the period of the product, for example "daily" or "monthly" and
    product_sub_type is an optional addition to cover where other subdivisions of the product are used, for example,
    ICDR or TCDR.
    '''

    def read(self, timestamp=None, **kwargs):
        ''' #todo update documentation
        Reads a single CCI image and returns it.
        :param timestamp: The date of the images required
        :param kwargs: None currently specified
        :return: The CCI image
        '''
        return_img = {}
        with Dataset(self.filename) as ds:
            parameters = ['dnflag', 'flag', 'freqbandID',
                          'lat', 'lon', 'mode', 'sensor',
                          'sm', 'sm_uncertainty',
                          't0', 'time']

            for param in parameters:
                return_img[param] = ds.variables[param][:]

        return return_img

    def write(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass


class c3s_v201706_dekadal_tcdr_active_img_nc(ImageBase):
    def read(self, timestamp=None, **kwargs):
        '''#todo update documentation
        Reads a single C3S image and returns it.
        :param timestamp: The date of the images required
        :param kwargs: None currently specified
        :return: The CCI image
        '''
        return_img = {}
        with Dataset(self.filename) as ds:
            parameters = ['freqbandID',
                          'lat', 'lon',
                          'nobs'
                          'sensor',
                          'sm',
                          'time']

            for param in parameters:
                return_img[param] = ds.variables[param][:]

        return return_img

    def write(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass


# TCDR multiple image readers -------------------------------------------------------------------------------------------
class c3s_sm_daily_multiimg(MultiTemporalImageBase):
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
    '''

    product_datatype_str = {'active': 'SSMS',
                            'passive': 'SSMV',
                            'combined': 'SSMV'}

    def __init__(self, path, product, version, product_sensor_type, product_sub_type, **kwargs):

        filename_templ = "C3S-SOILMOISTURE-L3S-" + self.product_datatype_str[
            product_sensor_type] + "-" + product_sensor_type.upper() + '-DAILY-{datetime}000000-' + product_sub_type.upper() + '-' + version + '.0.0.nc'  # todo alter this so does not have daily and tcdr hardcoded
        # todo somehow access the filename and then use this in the logging so we can see which files went in
        self.grid = SMECV_Grid_v042()
        super(c3s_sm_daily_multiimg, self).__init__(
            path, c3s_sm_daily_img,
            fname_templ=filename_templ,
            datetime_format="%Y%m%d",
            **kwargs)  # This is calling io_base.MultiTemporalImageBase

    def read(self, timestamp, **kwargs):
        """#todo update documentation
        Return an image for a specific timestamp.

        Parameters
        ----------
        timestamp : datetime.datetime
            Time stamp.

        Returns
        -------
        image : object
            pygeobase.object_base.Image object
        """
        try:
            data = super(c3s_sm_daily_multiimg, self).read(timestamp, **kwargs)
        except RuntimeError as e:
            raise IOError(e.message)
        # we take latitude and longitude from the grid object instead of the
        # netcdf file
        del data['lat']
        del data['lon']
        del data['time']

        for key in data:
            data[key] = np.flipud(data[key].data[0]).flatten()[self.grid.activegpis]

        return Image(self.grid.activearrlon,
                     self.grid.activearrlat,
                     data,
                     {},
                     timestamp)

    def tstamps_for_daterange(self, start_date, end_date):
        """#todo update documentation
        return timestamps for daterange,

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

        timestamps = []
        diff = end_date - start_date
        for i in xrange(diff.days + 1):
            daily_dates = start_date + timedelta(days=i)
            timestamps.append(daily_dates)
        return timestamps


class c3s_sm_monthly_multiimg(MultiTemporalImageBase):
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

    product_datatype_str = {'active': 'SSMS',
                            'passive': 'SSMV',
                            'combined': 'SSMV'}

    def __init__(self, path, product, version, product_sensor_type, product_sub_type, **kwargs):

        filename_templ = "C3S-SOILMOISTURE-L3S-" + self.product_datatype_str[
            product_sensor_type] + "-" + product_sensor_type.upper() + '-MONTHLY-{datetime}000000-TCDR-' + version + '.0.0.nc'
        self.grid = SMECV_Grid_v042()
        super(c3s_sm_monthly_multiimg, self).__init__(
            path, c3s_sm_daily_img,
            fname_templ=filename_templ,
            datetime_format="%Y%m%d",
            **kwargs)  # This is calling io_base.MultiTemporalImageBase

    def read(self, timestamp, **kwargs):
        """#todo update documentation
        Return an image for a specific timestamp.

        Parameters
        ----------
        timestamp : datetime.datetime
            Time stamp.

        Returns
        -------
        image : object
            pygeobase.object_base.Image object
        """
        try:
            data = super(c3s_sm_monthly_multiimg, self).read(timestamp, **kwargs)
        except RuntimeError as e:
            raise IOError(e.message)
        # we take latitude and longitude from the grid object instead of the
        # netcdf file
        del data['lat']
        del data['lon']

        for key in data:
            data[key] = np.flipud(data[key].data[0]).flatten()[self.grid.activegpis]

        return Image(self.grid.activearrlon,
                     self.grid.activearrlat,
                     data,
                     {},
                     timestamp)

    def tstamps_for_daterange(self, start_date, end_date):
        """#todo update documentation
        return timestamps for daterange,

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
        # todo ammend this for monthly
        timestamps = []
        diff = end_date - start_date
        for i in xrange(12):
            # monthly_dates = start_date + timedelta(month=i)
            monthly_dates = start_date + relativedelta(months=i)
            timestamps.append(monthly_dates)
        return timestamps
