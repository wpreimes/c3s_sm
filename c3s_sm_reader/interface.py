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
from smecv.grids.esa_cci_sm_grid import esa_cci_sm_grid_v04_2  # todo replace this with the c3s grid package
from pynetcf.time_series import OrthoMultiTs
from pynetcf.time_series import IndexedRaggedTs, GriddedNcTs
from pygeogrids.grids import CellGrid
from datetime import datetime
from datetime import time as dt_time


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



# TCDR timeseries attributes --------------------------------------------------------------------------------------------
class c3s_sm_ts_attr():
	def __init__(self):#todo add documentation
		#todo current is the base case which and should be called if version is not specified. need to add in functionality to deal with user specifying verions and where these might change, for example frewqbandID dictionary is different if we add new sensros
		self.product_datatype_str = {'active' : 'SSMS',
								'passive' : 'SSMV',
								'combined' : 'SSMV'}

	def atts_product_sensor_type(self, product_sensor_type):
		if product_sensor_type == "active" :
			self.sm_units = "percentage (%)"
			self.sm_uncertainty_units = "percentage (%)"
			self.sm_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
			self.sm_uncertainty_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
		else :
			self.sm_units = "m3 m-3"
			self.sm_uncertainty_units = "m3 m-3"
			self.sm_full_name = 'Volumetric Soil Moisture Uncertainty'
			self.sm_uncertainty_full_name = 'Volumetric Soil Moisture Uncertainty'


	def dn_flag(self):
		dn_flag_dict = {0 : 'nan',
						1 : "day",
						2 : 'night',
						3 : 'day_night_combination'}
		self.dn_flag_values = np.array(sorted(dn_flag_dict.keys()), dtype=np.byte)
		self.dn_flag_meanings = " ".join([dn_flag_dict[key] for key in self.dn_flag_values])


	def flag(self):
		flag_dict = {0 : 'no_data_inconsistency_detected',
					 1 : 'snow_coverage_or_temperature_below_zero',
					 2 : 'dense_vegetation',
					 3 : 'combination_of_flag_values_1_and_2',
					 4 : 'others_no_convergence_in_the_model_thus_no_valid_sm_estimates',
					 5 : 'combination_of_flag_values_1_and_4',
					 6 : 'combination_of_flag_values_2_and_4',
					 7 : 'combination_of_flag_values_1_and_2_and_4',
					 8 : 'soil_moisture_value_exceeds_physical_boundary',
					 16 : 'weight_of_measurement_below_threshold',
					 17 : 'combination_of_flag_values_1_and_16',
					 18 : 'combination_of_flag_values_2_and_16',
					 19 : 'combination_of_flag_values_1_and_2_and_16',
					 20 : 'combination_of_flag_values_4_and_16',
					 21 : 'combination_of_flag_values_1_and_4_and_16',
					 22 : 'combination_of_flag_values_2_and_4_and_16',
					 23 : 'combination_of_flag_values_1_and_2_and_4_and_16',
					 127 : 'nan'}
		self.flag_values = np.array(sorted(flag_dict.keys()), dtype=np.byte)
		self.flag_meanings = " ".join([flag_dict[key] for key in self.flag_values])

	def freqbandID_flag(self):
		freqbandID_flag_dict = {0 : 'NaN',
						  2 : 'C53',
						  4 : 'C66',
						  8 : 'C68',
						  10 : 'C53+C68',
						  16 : 'C69',
						  18 : 'C53+C69',
						  24 : 'C68+C69',
						  26 : 'C53+C68+C69',
						  32 : 'C73',
						  34 : 'C53+C73',
						  64 : 'X107',
						  66 : 'C53+X107',
						  72 : 'C68+X107',
						  74 : 'C53+C68+X107',
						  80 : 'C69+X107',
						  82 : 'C53+C69+X107',
						  128 : 'K194',
						  130 : 'C53+K194'}
		self.freqbandID_flag_values = np.array(sorted(freqbandID_flag_dict.keys()), dtype=np.int)
		self.freqbandID_flag_meanings = " ".join([freqbandID_flag_dict[key] for key in self.freqbandID_flag_values])

	def sensor_flag(self):
		sensor_flag_dict = {0 : 'NaN',
							1 : 'SMMR',
							2 : 'SSMI',
							4 : 'TMI',
							8 : 'AMSRE',
							16 : 'WindSat',
							24 : 'AMSRE+WindSat',
							32 : 'AMSR2',
							128 : 'AMIWS',
							130 : 'SSMI+AMIWS',
							132 : 'TMI+AMIWS',
							136 : 'AMSRE+AMIWS',
							256 : 'ASCATA',
							264 : 'AMSRE+ASCATA',
							272 : 'WindSat+ASCATA',
							280 : 'AMSRE+WindSat+ASCATA',
							288 : 'AMSR2+ASCATA',
							512 : 'ASCATB',
							520 : 'AMSRE+ASCATB',
							528 : 'WindSat+ASCATB',
							536 : 'AMSRE+WindSat+ASCATB',
							544 : 'AMSR2+ASCATB',
							768 : 'ASCATA+ASCATB',
							776 : 'AMSRE+ASCATA+ASCATB',
							784 : 'WindSat+ASCATA+ASCATB',
							792 : 'AMSRE+WindSat+ASCATA+ASCATB',
							800 : 'AMSR2+ASCATA+ASCATB'}
		self.sensor_flag_values = np.array(sorted(sensor_flag_dict.keys()), dtype=np.int)
		self.sensor_flag_meanings = " ".join([sensor_flag_dict[key] for key in self.sensor_flag_values])

	def mode_flag(self):
		mode_flag_dict = {0 : 'nan',
		                  1 : 'ascending',
		                  2 : 'descending',
		                  3 : 'ascending_descending_combination'}
		self.mode_flag_values = np.array(sorted(mode_flag_dict.keys()), dtype=np.int)
		self.mode_flag_meanings = " ".join([mode_flag_dict[key] for key in self.mode_flag_values])


class c3s_v201706_daily_tcdr_active_tsatt_nc(object) :
	#todo somehow incorporate this with the attributes above. for exmaple does this if active product, this if dekadal, etc.
	'''	Attributes for c3s daily active tcdr timeseries files.'''#todo update documentation

	common_attributes = c3s_sm_ts_attr()

	def __init__(self, version, product_sensor_type, product_temp_res, product_sub_type, version_sub_string='.0.0') :
		self.product_temp_res = product_temp_res
		self.product_sub_type = product_sub_type
		self.version_sub_string = version_sub_string
		self.common_attributes.atts_product_sensor_type(product_sensor_type)
		self.common_attributes.dn_flag()
		self.common_attributes.flag()
		self.common_attributes.freqbandID_flag()
		self.common_attributes.mode_flag()
		self.common_attributes.sensor_flag()

		self.ts_attributes = {
			'dnflag' : {'full_name' : 'Day / Night Flag',
						'units' : '1',
						'flag_values' : self.common_attributes.dn_flag_values,
						'flag_meanings' : self.common_attributes.dn_flag_meanings},
			'flag' : {'full_name' : 'Flag',
					  'units' : '1',
					  'flag_values' : self.common_attributes.flag_values,
					  'flag_meanings' : self.common_attributes.flag_meanings},
			'freqbandID' : {'full_name' : 'Frequency Band Identification',
							'units' : '1',
							'flag_values' : self.common_attributes.freqbandID_flag_values,
							'flag_meanings' : self.common_attributes.freqbandID_flag_meanings},
			'mode' : {'full_name' : 'Satellite  Mode',
					  'units' : '1',
					  'flag_values' : self.common_attributes.mode_flag_values,
					  'flag_meanings' : self.common_attributes.mode_flag_meanings},
			'sensor' : {'full_name' : 'Sensor',
						'units' : '1',
						'flag_values' : self.common_attributes.sensor_flag_values,
						'flag_meanings' : self.common_attributes.sensor_flag_meanings},
			'sm' : {'full_name' : self.common_attributes.sm_full_name,
					'units' : self.common_attributes.sm_units},
			'sm_uncertainty' : {'full_name' : self.common_attributes.sm_uncertainty_full_name,
								'units' : self.common_attributes.sm_uncertainty_units},
			't0' : {'full_name' : 'Observation Timestamp',
					'units' : 'days since 1970-01-01 00:00:00 UTC'}}

		product_name = "-".join(['C3S', 'SOILMOISTURE','L3S',
		                         self.common_attributes.product_datatype_str[product_sensor_type].upper(),
		                         product_sensor_type.upper(), self.product_temp_res.upper(),
		                         self.product_sub_type.upper(),
		                         version + self.version_sub_string])

		self.global_attr = {'product' : product_name,
							'resolution' : '0.25 degree',
							'temporalspacing' : self.product_temp_res}


class c3s_v201706_dekadal_tcdr_active_tsatt_nc(object) :
	#todo same as above - integrate with c3s_sm_ts_attr
	'''	Attributes for c3s dekadal and monthly for active, passive and combined tcdr and icdr timeseries files.'''

	common_attributes = c3s_sm_ts_attr()

	def __init__(self, version, product_sensor_type, product_temp_res, product_sub_type, version_sub_string='.0.0') :
		# todo update documentation
		self.product_temp_res = product_temp_res
		self.product_sub_type = product_sub_type
		self.version_sub_string = version_sub_string
		self.common_attributes.atts_product_sensor_type(product_sensor_type)
		self.common_attributes.sensor_flag()

		self.ts_attributes = {
			'freqbandID' : {'full_name' : 'Frequency Band Identification',
							'units' : '1',
							'flag_values' : self.common_attributes.freqbandID_flag_values,
							'flag_meanings' : self.common_attributes.freqbandID_flag_meanings},
			'sensor' : {'full_name' : 'Sensor',
						'units' : '1',
						'flag_values' : self.common_attributes.sensor_flag_values,
						'flag_meanings' : self.common_attributes.sensor_flag_meanings},
			'nobs':     {'full_name': 'Number of valid observation'},
			'sm' : {'full_name' : self.common_attributes.sm_full_name,
					'units' : self.common_attributes.sm_units}}

		product_name = "-".join(['C3S', 'SOILMOISTURE','L3S',
		                         self.common_attributes.product_datatype_str[product_sensor_type].upper(),
		                         product_sensor_type.upper(), self.product_temp_res.upper(),
		                         self.product_sub_type.upper(),
		                         version + self.version_sub_string])

		self.global_attr = {'product' : product_name,
							'resolution' : '0.25 degree',
							'temporalspacing' : self.product_temp_res}




# TCDR single image readers ---------------------------------------------------------------------------------------------
class c3s_sm_daily_img(ImageBase) :
	#todo can we combine for daily, dekal and monthly?
	'''#todo update documentation
	Class for reading a single ESA CCI SM image (for one timestamp)
	Class name determines product it is applicable to. Should be of format:
	{product}_{fileformat}_{product_time_period}_{product_sub_type}
	where product is the product that it is applicable, i.e. cci, fileformat is the type of file that are being read,
	for example, netcdf, product_time_period is the period of the product, for example "daily" or "monthly" and
	product_sub_type is an optional addition to cover where other subdivisions of the product are used, for example,
	ICDR or TCDR.
	'''

	def read(self, timestamp=None, **kwargs) :
		''' #todo update documentation
		Reads a single CCI image and returns it.
		:param timestamp: The date of the images required
		:param kwargs: None currently specified
		:return: The CCI image
		'''
		return_img = {}
		with Dataset(self.filename) as ds :
			parameters = ['dnflag', 'flag', 'freqbandID',
						  'lat', 'lon', 'mode', 'sensor',
						  'sm', 'sm_uncertainty',
						  't0', 'time']

			for param in parameters :
				return_img[param] = ds.variables[param][:]

		return return_img

	def write(self, *args, **kwargs) :
		pass

	def close(self, *args, **kwargs) :
		pass

	def flush(self, *args, **kwargs) :
		pass


class c3s_v201706_dekadal_tcdr_active_img_nc(ImageBase) :
	def read(self, timestamp=None, **kwargs) :
		'''#todo update documentation
		Reads a single C3S image and returns it.
		:param timestamp: The date of the images required
		:param kwargs: None currently specified
		:return: The CCI image
		'''
		return_img = {}
		with Dataset(self.filename) as ds :
			parameters = ['freqbandID',
						  'lat', 'lon',
						  'nobs'
						  'sensor',
						  'sm',
						  'time']

			for param in parameters :
				return_img[param] = ds.variables[param][:]

		return return_img

	def write(self, *args, **kwargs) :
		pass

	def close(self, *args, **kwargs) :
		pass

	def flush(self, *args, **kwargs) :
		pass


# TCDR multiple image readers -------------------------------------------------------------------------------------------
class c3s_sm_daily_multiimg(MultiTemporalImageBase) :
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

	product_datatype_str = {'active' : 'SSMS',
							'passive' : 'SSMV',
							'combined' : 'SSMV'}

	def __init__(self, path, product, version, product_sensor_type, product_sub_type, **kwargs) :

		filename_templ = "C3S-SOILMOISTURE-L3S-" + self.product_datatype_str[
			product_sensor_type] + "-" + product_sensor_type.upper() + '-DAILY-{datetime}000000-' + product_sub_type.upper() + '-' + version + '.0.0.nc'  # todo alter this so does not have daily and tcdr hardcoded
		# todo somehow access the filename and then use this in the logging so we can see which files went in
		self.grid = SMECV_Grid_v042()
		super(c3s_sm_daily_multiimg, self).__init__(
			path, c3s_sm_daily_img,
			fname_templ=filename_templ,
			datetime_format="%Y%m%d",
			**kwargs)  # This is calling io_base.MultiTemporalImageBase

	def read(self, timestamp, **kwargs) :
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
		try :
			data = super(c3s_sm_daily_multiimg, self).read(timestamp, **kwargs)
		except RuntimeError as e :
			raise IOError(e.message)
		# we take latitude and longitude from the grid object instead of the
		# netcdf file
		del data['lat']
		del data['lon']
		del data['time']

		for key in data :
			data[key] = np.flipud(data[key].data[0]).flatten()[self.grid.activegpis]

		return Image(self.grid.activearrlon,
					 self.grid.activearrlat,
					 data,
					 {},
					 timestamp)

	def tstamps_for_daterange(self, start_date, end_date) :
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
		for i in xrange(diff.days + 1) :
			daily_dates = start_date + timedelta(days=i)
			timestamps.append(daily_dates)
		return timestamps



class c3s_sm_monthly_multiimg(MultiTemporalImageBase) :
	#todo i think we need a separate one for monthly, dekdal and daily, but you may be able to change this
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

	product_datatype_str = {'active' : 'SSMS',
							'passive' : 'SSMV',
							'combined' : 'SSMV'}

	def __init__(self, path, product, version, product_sensor_type, product_sub_type, **kwargs) :

		filename_templ = "C3S-SOILMOISTURE-L3S-" + self.product_datatype_str[
			product_sensor_type] + "-" + product_sensor_type.upper() + '-MONTHLY-{datetime}000000-TCDR-' + version + '.0.0.nc'
		self.grid = SMECV_Grid_v042()
		super(c3s_sm_monthly_multiimg, self).__init__(
			path, c3s_sm_daily_img,
			fname_templ=filename_templ,
			datetime_format="%Y%m%d",
			**kwargs)  # This is calling io_base.MultiTemporalImageBase

	def read(self, timestamp, **kwargs) :
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
		try :
			data = super(c3s_sm_monthly_multiimg, self).read(timestamp, **kwargs)
		except RuntimeError as e :
			raise IOError(e.message)
		# we take latitude and longitude from the grid object instead of the
		# netcdf file
		del data['lat']
		del data['lon']

		for key in data :
			data[key] = np.flipud(data[key].data[0]).flatten()[self.grid.activegpis]

		return Image(self.grid.activearrlon,
					 self.grid.activearrlat,
					 data,
					 {},
					 timestamp)

	def tstamps_for_daterange(self, start_date, end_date) :
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
		for i in xrange(12) :
			# monthly_dates = start_date + timedelta(month=i)
			monthly_dates = start_date + relativedelta(months=i)
			timestamps.append(monthly_dates)
		return timestamps
