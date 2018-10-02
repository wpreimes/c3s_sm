# -*- coding: utf-8 -*-



# TCDR timeseries attributes --------------------------------------------------------------------------------------------
class C3S_SM_TS_Attrs():
    # FIXME: maybe this should be in the file metadata, and we read it directly from the files?
    # FIXME : maybe store the large dicts in a ini file the classes
    # FIXME : Should this be automatically generated or read from predefined file

    def __init__(self, version=None):  # todo add documentation
        # todo current is the base case which and should be called if version is not specified. need to add in functionality
        # to deal with user specifying verions and where these might change, for example frewqbandID dictionary is different if we add new sensros
        self.product_datatype_str = {'active': 'SSMS',
                                     'passive': 'SSMV',
                                     'combined': 'SSMV'}

    def atts_product_sensor_type(self, product_sensor_type):
        if product_sensor_type == "active":
            self.sm_units = "percentage (%)"
            self.sm_uncertainty_units = "percentage (%)"
            self.sm_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
            self.sm_uncertainty_full_name = 'Percent of Saturation Soil Moisture Uncertainty'
        else:
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

    def mode_flag(self):
        mode_flag_dict = {0: 'nan',
                          1: 'ascending',
                          2: 'descending',
                          3: 'ascending_descending_combination'}
        self.mode_flag_values = np.array(sorted(mode_flag_dict.keys()), dtype=np.int)
        self.mode_flag_meanings = " ".join([mode_flag_dict[key] for key in self.mode_flag_values])


class c3s_v201706_daily_tcdr_active_tsatt_nc(object):
    # todo somehow incorporate this with the attributes above. for exmaple does this if active product, this if dekadal, etc.
    '''	Attributes for c3s daily ACTIVE tcdr timeseries files.'''  # todo update documentation

    common_attributes = c3s_sm_ts_attr()

    def __init__(self, version, product_sensor_type, product_temp_res, product_sub_type, version_sub_string='.0.0'):
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
            'dnflag': {'full_name': 'Day / Night Flag',
                       'units': '1',
                       'flag_values': self.common_attributes.dn_flag_values,
                       'flag_meanings': self.common_attributes.dn_flag_meanings},
            'flag': {'full_name': 'Flag',
                     'units': '1',
                     'flag_values': self.common_attributes.flag_values,
                     'flag_meanings': self.common_attributes.flag_meanings},
            'freqbandID': {'full_name': 'Frequency Band Identification',
                           'units': '1',
                           'flag_values': self.common_attributes.freqbandID_flag_values,
                           'flag_meanings': self.common_attributes.freqbandID_flag_meanings},
            'mode': {'full_name': 'Satellite  Mode',
                     'units': '1',
                     'flag_values': self.common_attributes.mode_flag_values,
                     'flag_meanings': self.common_attributes.mode_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'units': '1',
                       'flag_values': self.common_attributes.sensor_flag_values,
                       'flag_meanings': self.common_attributes.sensor_flag_meanings},
            'sm': {'full_name': self.common_attributes.sm_full_name,
                   'units': self.common_attributes.sm_units},
            'sm_uncertainty': {'full_name': self.common_attributes.sm_uncertainty_full_name,
                               'units': self.common_attributes.sm_uncertainty_units},
            't0': {'full_name': 'Observation Timestamp',
                   'units': 'days since 1970-01-01 00:00:00 UTC'}}

        product_name = "-".join(['C3S', 'SOILMOISTURE', 'L3S',
                                 self.common_attributes.product_datatype_str[product_sensor_type].upper(),
                                 product_sensor_type.upper(), self.product_temp_res.upper(),
                                 self.product_sub_type.upper(),
                                 version + self.version_sub_string])

        self.global_attr = {'product': product_name,
                            'resolution': '0.25 degree',
                            'temporalspacing': self.product_temp_res}


class c3s_v201706_dekadal_tcdr_active_tsatt_nc(object):
    # todo same as above - integrate with c3s_sm_ts_attr
    '''	Attributes for c3s dekadal and monthly for active, passive and combined tcdr and icdr timeseries files.'''

    common_attributes = c3s_sm_ts_attr()

    def __init__(self, version, product_sensor_type, product_temp_res, product_sub_type, version_sub_string='.0.0'):
        # todo update documentation
        self.product_temp_res = product_temp_res
        self.product_sub_type = product_sub_type
        self.version_sub_string = version_sub_string
        self.common_attributes.atts_product_sensor_type(product_sensor_type)
        self.common_attributes.sensor_flag()

        self.ts_attributes = {
            'freqbandID': {'full_name': 'Frequency Band Identification',
                           'units': '1',
                           'flag_values': self.common_attributes.freqbandID_flag_values,
                           'flag_meanings': self.common_attributes.freqbandID_flag_meanings},
            'sensor': {'full_name': 'Sensor',
                       'units': '1',
                       'flag_values': self.common_attributes.sensor_flag_values,
                       'flag_meanings': self.common_attributes.sensor_flag_meanings},
            'nobs': {'full_name': 'Number of valid observation'},
            'sm': {'full_name': self.common_attributes.sm_full_name,
                   'units': self.common_attributes.sm_units}}

        product_name = "-".join(['C3S', 'SOILMOISTURE', 'L3S',
                                 self.common_attributes.product_datatype_str[product_sensor_type].upper(),
                                 product_sensor_type.upper(), self.product_temp_res.upper(),
                                 self.product_sub_type.upper(),
                                 version + self.version_sub_string])

        self.global_attr = {'product': product_name,
                            'resolution': '0.25 degree',
                            'temporalspacing': self.product_temp_res}