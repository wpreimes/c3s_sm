# -*- coding: utf-8 -*-

import numpy as np
from collections import OrderedDict

class C3S_SM_TS_Attrs(object):
    '''Default, common metadata for daily and monthly, dekadal products'''
    def __init__(self, product_sensor_type, version='v0000', sub_version='.0.0'):
        # todo: version keyword might be unnecessary?
        '''
        Parameters
        ----------
        product_sensor_type : str
            Sensor type: active, passive, combined
        version : str
            Version name to read attributes for
        sub_version : str
            Sub version to read attributes for
        '''
        self.version, self.version_sub_string = version, sub_version

        self.product_datatype_str = {'active': 'SSMS',
                                     'passive': 'SSMV',
                                     'combined': 'SSMV'}

        self.product_sensor_type = product_sensor_type

        self.atts_product_sensor_type(product_sensor_type)

    def atts_product_sensor_type(self, product_sensor_type='active'):
        if product_sensor_type == "active":
            self.sm_units = "percentage (%)"
            self.sm_uncertainty_units = "percentage (%)"
            self.sm_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
            self.sm_uncertainty_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
        else:
            # todo: some names are wrong? sm_full_name...
            self.sm_units = "m3 m-3"
            self.sm_uncertainty_units = "m3 m-3"
            self.sm_full_name = 'Volumetric Soil Moisture Uncertainty'
            self.sm_uncertainty_full_name = 'Volumetric Soil Moisture Uncertainty'

    def dn_flag(self):
        dn_flag_dict = OrderedDict([
            ('0', 'NaN'),
            ('Bit1', "day"),
            ('Bit2', 'night'),
        ])
        self.dn_flag_values = np.array(list(dn_flag_dict.keys()))
        self.dn_flag_meanings = np.array(list(dn_flag_dict.values()))

        return self.dn_flag_values, self.dn_flag_meanings

    def flag(self):
        flag_dict = OrderedDict([
            ('0', 'no_data_inconsistency_detected'),
            ('Bit0', 'snow_coverage_or_temperature_below_zero'),
            ('Bit1', 'dense_vegetation'),
            ('Bit2', 'others_no_convergence_in_the_model_thus_no_valid_sm_estimates'),
            ('Bit3', 'soil_moisture_value_exceeds_physical_boundary'),
            ('Bit4', 'weight_of_measurement_below_threshold'),
            ('Bit5', 'all_datasets_deemed_unreliable'),
            ('Bit6', 'NaN'),
        ])

        self.flag_values = np.array(list(flag_dict.keys()))
        self.flag_meanings = np.array(list(flag_dict.values()))

        return self.flag_values, self.flag_meanings

    def freqbandID_flag(self):
        freqbandID_flag_dict = OrderedDict([
            ('0', 'NaN'),
            ('Bit0', 'L14'),
            ('Bit1', 'C53'),
            ('Bit2', 'C66'),
            ('Bit3', 'C68'),
            ('Bit4', 'C69'),
            ('Bit5', 'C73'),
            ('Bit6', 'X107'),
            ('Bit7', 'K194'),
        ])

        self.freqbandID_flag_values = np.array(list(freqbandID_flag_dict.keys()))
        self.freqbandID_flag_meanings = np.array(list(freqbandID_flag_dict.values()))

        return self.freqbandID_flag_values, self.freqbandID_flag_meanings

    def sensor_flag(self):
        sensor_flag_dict = OrderedDict([
            ('0', 'NaN'),
            ('Bit0', 'SMMR'),
            ('Bit1', 'SSMI'),
            ('Bit2', 'TMI'),
            ('Bit3', 'AMSRE'),
            ('Bit4', 'WindSat'),
            ('Bit5', 'AMSR2'),
            ('Bit6', 'AMIWS'),
            ('Bit7', 'ASCATA'),
            ('Bit8', 'ASCATB'),
            ])

        self.sensor_flag_values = np.array(list(sensor_flag_dict.keys()))
        self.sensor_flag_meanings = np.array(list(sensor_flag_dict.values()))

        return self.sensor_flag_values, self.sensor_flag_meanings

    def mode_flag(self):
        mode_flag_dict = OrderedDict([
            ('0', 'NaN'),
            ('Bit0', 'ascending'),
            ('Bit1', 'descending'),
            ])
        self.mode_flag_values = np.array(list(mode_flag_dict.keys()))
        self.mode_flag_meanings = np.array(list(mode_flag_dict.values()))

        return self.mode_flag_meanings, self.mode_flag_values


class C3S_daily_tsatt_nc(object):

    def __init__(self, VersionAttrs=C3S_SM_TS_Attrs, product_sub_type='TCDR',
                 product_sensor_type='active', sub_version='.0.0'):

        self.general_attrs = VersionAttrs(product_sensor_type=product_sensor_type,
                                          sub_version=sub_version)

        self.version = self.general_attrs.version
        version_sub_string = self.general_attrs.version_sub_string
        product_sensor_type = self.general_attrs.product_sensor_type

        self.product_temp_res = 'daily'
        self.product_sub_type = product_sub_type
        self.version_sub_string = version_sub_string
        self.general_attrs.atts_product_sensor_type(product_sensor_type)
        self.general_attrs.dn_flag()
        self.general_attrs.flag()
        self.general_attrs.freqbandID_flag()
        self.general_attrs.mode_flag()
        self.general_attrs.sensor_flag()

        self.ts_attributes = {
            'dnflag': {'full_name': 'Day / Night Flag',
                       'flag_values': self.general_attrs.dn_flag_values,
                       'flag_meanings': self.general_attrs.dn_flag_meanings},
            'flag': {'full_name': 'Flag',
                     'flag_values': self.general_attrs.flag_values,
                     'flag_meanings': self.general_attrs.flag_meanings},
            'freqbandID': {'full_name': 'Frequency Band Identification',
                           'flag_values': self.general_attrs.freqbandID_flag_values,
                           'flag_meanings': self.general_attrs.freqbandID_flag_meanings},
            'mode': {'full_name': 'Satellite  Mode',
                     'flag_values': self.general_attrs.mode_flag_values,
                     'flag_meanings': self.general_attrs.mode_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'flag_values': self.general_attrs.sensor_flag_values,
                       'flag_meanings': self.general_attrs.sensor_flag_meanings},
            'sm': {'full_name': self.general_attrs.sm_full_name,
                   'units': self.general_attrs.sm_units},
            'sm_uncertainty': {'full_name': self.general_attrs.sm_uncertainty_full_name,
                               'units': self.general_attrs.sm_uncertainty_units},
            't0': {'full_name': 'Observation Timestamp',
                   'units': 'days since 1970-01-01 00:00:00 UTC'}}

        product_name = "-".join(['C3S', 'SOILMOISTURE', 'L3S',
                                 self.general_attrs.product_datatype_str[product_sensor_type].upper(),
                                 product_sensor_type.upper(), self.product_temp_res.upper(),
                                 self.product_sub_type.upper(),
                                 self.version + self.version_sub_string])

        self.global_attr = {'product': product_name,
                            'resolution': '0.25 degree',
                            'temporalspacing': self.product_temp_res}


class C3S_dekmon_tsatt_nc(object):
    '''	Attributes for c3s dekadal and monthly for active, passive and combined
    tcdr and icdr timeseries files.'''

    def __init__(self, VersionAttrs, product_temp_res='monthly',
                 product_sub_type='TCDR', product_sensor_type='active', sub_version='.0.0'):

        self.general_attrs = VersionAttrs(product_sensor_type=product_sensor_type,
                                          sub_version=sub_version)


        self.version = self.general_attrs.version
        version_sub_string = self.general_attrs.version_sub_string
        product_sensor_type = self.general_attrs.product_sensor_type

        self.product_temp_res = product_temp_res
        self.product_sub_type = product_sub_type
        self.version_sub_string = version_sub_string
        self.general_attrs.atts_product_sensor_type(product_sensor_type)
        self.general_attrs.dn_flag()
        self.general_attrs.freqbandID_flag()

        self.general_attrs.sensor_flag()



        self.ts_attributes = {
            'freqbandID': {'full_name': 'Frequency Band Identification',
                           'flag_values': self.general_attrs.freqbandID_flag_values,
                           'flag_meanings': self.general_attrs.freqbandID_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'flag_values': self.general_attrs.sensor_flag_values,
                       'flag_meanings': self.general_attrs.sensor_flag_meanings},
            'nobs': {'full_name': 'Number of valid observation'},
            'sm': {'full_name': self.general_attrs.sm_full_name,
                   'units': self.general_attrs.sm_units}}

        product_name = "-".join(['C3S', 'SOILMOISTURE', 'L3S',
                                 self.general_attrs.product_datatype_str[product_sensor_type].upper(),
                                 product_sensor_type.upper(), self.product_temp_res.upper(),
                                 self.product_sub_type.upper(),
                                 self.version + self.version_sub_string])

        self.global_attr = {'product': product_name,
                            'resolution': '0.25 degree',
                            'temporalspacing': self.product_temp_res}


class C3S_SM_TS_Attrs_v201706(C3S_SM_TS_Attrs):
    # Example for a version specific attribute class, last part defines version
    def __init__(self, product_sensor_type, sub_version='.0.0'):

        version = type(self).__name__.split('_')[-1]
        super(C3S_SM_TS_Attrs_v201706, self).__init__(product_sensor_type, version,
                                                      sub_version)

class C3S_SM_TS_Attrs_v201801(C3S_SM_TS_Attrs):
    # Example for a version specific attribute class, last part defines version
    def __init__(self, product_sensor_type, sub_version='.0.0'):

        version = type(self).__name__.split('_')[-1]
        super(C3S_SM_TS_Attrs_v201801, self).__init__(product_sensor_type, version,
                                                      sub_version)

class C3S_SM_TS_Attrs_v201812(C3S_SM_TS_Attrs):
    # Example for a version specific attribute class, last part defines version
    def __init__(self, product_sensor_type, sub_version='.0.0'):

        version = type(self).__name__.split('_')[-1]
        super(C3S_SM_TS_Attrs_v201812, self).__init__(product_sensor_type, version,
                                                      sub_version)