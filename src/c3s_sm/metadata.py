# -*- coding: utf-8 -*-

import numpy as np

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
        dn_flag_dict = {0: 'nan',
                        1: "day",
                        2: 'night',
                        3: 'day_night_combination'}
        self.dn_flag_values = np.array(sorted(dn_flag_dict.keys()), dtype=np.byte)
        self.dn_flag_meanings = " ".join([dn_flag_dict[key] for key in self.dn_flag_values])

        return self.dn_flag_values, self.dn_flag_meanings

    def flag(self):
        flag_dict = {0: 'no_data_inconsistency_detected',
                     1: 'snow_coverage_or_temperature_below_zero',
                     2: 'dense_vegetation',
                     3: 'combination_of_flag_values_1_and_2',
                     4: 'others_no_convergence_in_the_model_thus_no_valid_sm_estimates',
                     5: 'combination_of_flag_values_1_and_4',
                     6: 'combination_of_flag_values_2_and_4',
                     7: 'combination_of_flag_values_1_and_2_and_4',
                     8: 'soil_moisture_value_exceeds_physical_boundary',
                     16: 'weight_of_measurement_below_threshold',
                     17: 'combination_of_flag_values_1_and_16',
                     18: 'combination_of_flag_values_2_and_16',
                     19: 'combination_of_flag_values_1_and_2_and_16',
                     20: 'combination_of_flag_values_4_and_16',
                     21: 'combination_of_flag_values_1_and_4_and_16',
                     22: 'combination_of_flag_values_2_and_4_and_16',
                     23: 'combination_of_flag_values_1_and_2_and_4_and_16',
                     127: 'nan'}
        self.flag_values = np.array(sorted(flag_dict.keys()), dtype=np.byte)
        self.flag_meanings = " ".join([flag_dict[key] for key in self.flag_values])

        return self.flag_values, self.flag_meanings

    def freqbandID_flag(self):
        freqbandID_flag_dict = {0: 'NaN',
                                2: 'C53',
                                4: 'C66',
                                8: 'C68',
                                10: 'C53+C68',
                                16: 'C69',
                                18: 'C53+C69',
                                24: 'C68+C69',
                                26: 'C53+C68+C69',
                                32: 'C73',
                                34: 'C53+C73',
                                64: 'X107',
                                66: 'C53+X107',
                                72: 'C68+X107',
                                74: 'C53+C68+X107',
                                80: 'C69+X107',
                                82: 'C53+C69+X107',
                                128: 'K194',
                                130: 'C53+K194'}
        self.freqbandID_flag_values = np.array(sorted(freqbandID_flag_dict.keys()), dtype=np.int)
        self.freqbandID_flag_meanings = " ".join([freqbandID_flag_dict[key] for key in self.freqbandID_flag_values])

        return self.freqbandID_flag_values, self.freqbandID_flag_meanings

    def sensor_flag(self):
        sensor_flag_dict = {0: 'NaN',
                            1: 'SMMR',
                            2: 'SSMI',
                            4: 'TMI',
                            8: 'AMSRE',
                            16: 'WindSat',
                            24: 'AMSRE+WindSat',
                            32: 'AMSR2',
                            128: 'AMIWS',
                            130: 'SSMI+AMIWS',
                            132: 'TMI+AMIWS',
                            136: 'AMSRE+AMIWS',
                            256: 'ASCATA',
                            264: 'AMSRE+ASCATA',
                            272: 'WindSat+ASCATA',
                            280: 'AMSRE+WindSat+ASCATA',
                            288: 'AMSR2+ASCATA',
                            512: 'ASCATB',
                            520: 'AMSRE+ASCATB',
                            528: 'WindSat+ASCATB',
                            536: 'AMSRE+WindSat+ASCATB',
                            544: 'AMSR2+ASCATB',
                            768: 'ASCATA+ASCATB',
                            776: 'AMSRE+ASCATA+ASCATB',
                            784: 'WindSat+ASCATA+ASCATB',
                            792: 'AMSRE+WindSat+ASCATA+ASCATB',
                            800: 'AMSR2+ASCATA+ASCATB'}
        self.sensor_flag_values = np.array(sorted(sensor_flag_dict.keys()), dtype=np.int)
        self.sensor_flag_meanings = " ".join([sensor_flag_dict[key] for key in self.sensor_flag_values])

        return self.sensor_flag_values, self.sensor_flag_meanings

    def mode_flag(self):
        mode_flag_dict = {0: 'nan',
                          1: 'ascending',
                          2: 'descending',
                          3: 'ascending_descending_combination'}
        self.mode_flag_values = np.array(sorted(mode_flag_dict.keys()), dtype=np.int)
        self.mode_flag_meanings = " ".join([mode_flag_dict[key] for key in self.mode_flag_values])

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
                       'units': '1',
                       'flag_values': self.general_attrs.dn_flag_values,
                       'flag_meanings': self.general_attrs.dn_flag_meanings},
            'flag': {'full_name': 'Flag',
                     'units': '1',
                     'flag_values': self.general_attrs.flag_values,
                     'flag_meanings': self.general_attrs.flag_meanings},
            'freqbandID': {'full_name': 'Frequency Band Identification',
                           'units': '1',
                           'flag_values': self.general_attrs.freqbandID_flag_values,
                           'flag_meanings': self.general_attrs.freqbandID_flag_meanings},
            'mode': {'full_name': 'Satellite  Mode',
                     'units': '1',
                     'flag_values': self.general_attrs.mode_flag_values,
                     'flag_meanings': self.general_attrs.mode_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'units': '1',
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
                           'units': '1',
                           'flag_values': self.general_attrs.freqbandID_flag_values,
                           'flag_meanings': self.general_attrs.freqbandID_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'units': '1',
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

    # TODO: Version specific values can be changed here by changing the functions
    def freqbandID_flag(self):
        freqbandID_flag_dict = {0: 'NaN',
                                2: 'C53',
                                4: 'C66',
                                8: 'C68',
                                10: 'C53+C68',
                                16: 'C69',
                                18: 'C53+C69',
                                24: 'C68+C69',
                                26: 'C53+C68+C69',
                                32: 'C73',
                                34: 'C53+C73',
                                64: 'X107',
                                66: 'C53+X107',
                                72: 'C68+X107',
                                74: 'C53+C68+X107',
                                80: 'C69+X107',
                                82: 'C53+C69+X107',
                                128: 'K194',
                                130: 'C53+K194'}
        self.freqbandID_flag_values = np.array(sorted(freqbandID_flag_dict.keys()), dtype=np.int)
        self.freqbandID_flag_meanings = " ".join([freqbandID_flag_dict[key] for key in self.freqbandID_flag_values])

        return self.freqbandID_flag_values, self.freqbandID_flag_meanings



if __name__ == '__main__':
    o = C3S_SM_TS_Attrs_v201801('active')

    dob = C3S_dekmon_tsatt_nc(C3S_SM_TS_Attrs_v201801, product_sub_type='TCDR',
                 product_sensor_type='active', product_temp_res='monthly', sub_version='.9.9')

    attr = C3S_SM_TS_Attrs_v201801('active')

