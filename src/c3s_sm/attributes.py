# -*- coding: utf-8 -*-

"""
This module defines the variable attributes for all C3S SM versions & products

"""
from c3s_sm.bitflags import ProductBitFlag, ProdVarAttr
from collections import OrderedDict
import numpy as np
from netCDF4 import date2num
from datetime import datetime

class v201706_sm(ProdVarAttr):
    # Describes sm attributes of v201706 version, probably won't change in future

    def __init__(self):
        a_attrs = OrderedDict([
                ("long_name", "Percent of Saturation Soil Moisture"),
                ("units", "percent"),
                ("valid_range", np.array([0, 100])),
                ])
        cp_attrs = OrderedDict([
            ("long_name", "Volumetric Soil Moisture"),
            ("units", "m3 m-3"),
            ("valid_range", np.array([0, 1])),
        ])

        super(v201706_sm, self).__init__('sm', a_attrs, cp_attrs, cp_attrs)


class v201706_sm_uncertainty(ProdVarAttr):
    # Describes sm_uncertainty attributes of v201706, probably won't change in future

    def __init__(self):
        a_attrs = OrderedDict([
                ("description", "Uncertainty is the estimated standard deviation "
                                "of the observation"),
                ("long_name", "Percent of Saturation Soil Moisture Uncertainty"),
                ("units", "percent"),
                ("valid_range", np.array([0, 100])),
                ])
        cp_attrs = OrderedDict([
            ("description", "Uncertainty is the estimated standard deviation "
                            "of the observation"),
            ("long_name", "Volumetric Soil Moisture Uncertainty"),
            ("units", "m3 m-3"),
            ("valid_range", np.array([0, 1])),
        ])

        super(v201706_sm_uncertainty, self).__init__(
            'sm_uncertainty', a_attrs, cp_attrs, cp_attrs)


class v201706_t0(ProdVarAttr):
    # Describes t0 attributes of v201706, probably won't change in future

    def __init__(self, base_date:datetime=datetime(1970,1,1,0,0)):

        self.base_date = base_date

        units = f"days since {str(base_date)} UTC"

        acp_attrs = OrderedDict([
            ("description", "Uncertainty is the estimated standard deviation "
                            "of the observation"),
            ("long_name", "Observation Timestamp"),
            ("units", units),
            ("valid_range", np.array([date2num(self.base_date, units=units),
                                      date2num(datetime.now(), units=units)])),
        ])

        super(v201706_t0, self).__init__(
            'sm_uncertainty', acp_attrs, acp_attrs, acp_attrs)


class v201706_dnflag(ProdVarAttr):
    # Describes dnflag attributes of v201706, probably won't change in future

    def __init__(self):
        flags = ProductBitFlag('NaN', 'day', 'night')
        flags.build(False, '', '_', 'combination') # like: day_night_combination

        dnflag = flags.get_flags(index='intflag', drop_other=True, no_combis=True,
                                as_type='dict')

        values, meanings = list(dict(dnflag).keys()), list(dict(dnflag).values())

        acp_attrs = OrderedDict([
            ('flag_values', ' '.join(['{}'.format(e) for e in values])),
            ('flag_meanings', ' '.join(['{}'.format(e) for e in meanings])),
            ('long_name', 'Day / Night Flag'),
            ('format', 'bit2int / meaning'),
        ])

        super(v201706_dnflag, self).__init__(
            'dnflag', acp_attrs, acp_attrs, acp_attrs)


class v201706_mode(ProdVarAttr):
    # Describes mode attributes of v201706, probably won't change in future

    def __init__(self):
        flags = ProductBitFlag('NaN', 'ascending', 'descending')
        flags.build(False, '', '_', 'combination') # like: ascending_descending_combination

        modeflag = flags.get_flags(index='intflag', drop_other=True,
                                   no_combis=True, as_type='dict')

        values, meanings = list(dict(modeflag).keys()), list(dict(modeflag).values())

        acp_attrs = OrderedDict([
            ('flag_values', ' '.join(['{}'.format(e) for e in values])),
            ('flag_meanings', ' '.join(['{}'.format(e) for e in meanings])),
            ('long_name', 'Satellite Mode'),
        ])

        super(v201706_mode, self).__init__('mode', acp_attrs, acp_attrs, acp_attrs)


class v201706_flag(ProdVarAttr):
    # Describes the quality flag attributes of v201706, might change in future

    def __init__(self):

        flags = ProductBitFlag(
             'no_data_inconsistency_detected',                                  # None, int(0)
             'snow_coverage_or_temperature_below_zero',                         # b1,  bit0
             'dense_vegetation',                                                # b2,  bit1
             'others_no_convergence_in_the_model_thus_no_valid_sm_estimates',   # b4,  bit2
             'soil_moisture_value_exceeds_physical_boundary',                   # b8,  bit3
             'weight_of_measurement_below_threshold',                           # b16, bit4
             'all_datasets_deemed_unreliable',                                  # b32, bit5
        )
        # combine flags like: combination_of_flag_values_1_and_2
        flags.build(True, 'combination_of_flag_values_', '_and_', '')

        qflag = flags.get_flags(index='intflag', drop_other=True, no_combis=False,
                                as_type='dict')

        acp_attrs = OrderedDict([
            ('flag_values', ' '.join(['{}'.format(e) for e in list(dict(qflag).keys())])),
            ('flag_meanings', ' '.join(['{}'.format(e) for e in list(dict(qflag).values())])),
            ('long_name', 'Flag'),
            ('format', 'bitflag combinations converted to integer values / meaning'),
        ])

        # These are the same for all 3 products
        super(v201706_flag, self).__init__('flag', acp_attrs, acp_attrs, acp_attrs)


class v201706_sensor(ProdVarAttr):
    # Describes the sensors flag attributes of v201706, will change in future

    def __init__(self):

        flags = ProductBitFlag(
            'NaN',                                                              # None, int(0)
            'SMMR',                                                             # b1,   bit0
            'SSMI',                                                             # b2,   bit1
            'TMI',                                                              # b4,   bit2
            'AMSRE',                                                            # b8,   bit3
            'Windsat',                                                          # b16,  bit4
            'AMSR2',                                                            # b32,  bit5
            'SMOS',                                                             # b64,  bit6
            'AMIWS',                                                            # b128, bit7
            'ASCATA',                                                           # b256, bit8
            'ASCATB',                                                           # b512, bit9
            active_bits=[128, 256, 512],
            passive_bits=[1, 2, 4, 8, 16, 32, 64]
        )
        # combine flags like: SMMR+SSMI
        flags.build(False, '', '+', '')

        kwargs = dict(index='intflag', drop_other=True,
                      no_combis=True, as_type='dict')

        super(v201706_sensor, self).__init__(
            'sensor',
            flags.get_prod_flags('active', **kwargs),
            flags.get_prod_flags('combined', **kwargs),
            flags.get_prod_flags('passive', **kwargs))


class v201706_freqbandId(ProdVarAttr):
    # Describes the frequency flag attributes of v201706, might change in future

    def __init__(self):
        flags = ProductBitFlag(
            'NaN',                                                              # None, int(0)
            'L14',                                                              # b1,   bit0
            'C53',                                                              # b2,   bit1
            'C66',                                                              # b4,   bit2
            'C68',                                                              # b8,   bit3
            'C69',                                                              # b16,  bit4
            'C73',                                                              # b32,  bit5
            'X107',                                                             # b64,  bit6
            'K194',                                                             # b128, bit7
            active_bits=[2],
            passive_bits=[1,4,8,16,32,64,128]
        )
        # combine flags like: C53+X107
        flags.build(False, '', '+', '')

        kwargs = dict(index='intflag', drop_other=True,
                      no_combis=True, as_type='dict')

        super(v201706_freqbandId, self).__init__(
            'freqbandID',
            flags.get_prod_flags('active', **kwargs),
            flags.get_prod_flags('combined', **kwargs),
            flags.get_prod_flags('passive', **kwargs))


# Nothing changed in v201806
class v201806_dnflag(v201706_dnflag): pass
class v201806_flag(v201706_flag): pass
class v201806_freqbandId(v201706_freqbandId): pass
class v201806_mode(v201706_mode): pass
class v201806_sensor(v201706_sensor): pass
class v201806_t0(v201706_t0): pass
class v201806_sm(v201706_sm): pass
class v201806_sm_uncertainty(v201706_sm_uncertainty): pass

# Nothing changed in v201812
class v201812_dnflag(v201806_dnflag): pass
class v201812_flag(v201806_flag): pass
class v201812_freqbandId(v201806_freqbandId): pass
class v201812_mode(v201806_mode): pass
class v201812_sensor(v201806_sensor): pass
class v201812_t0(v201806_t0): pass
class v201812_sm(v201806_sm): pass
class v201812_sm_uncertainty(v201806_sm_uncertainty): pass

# Nothing changed in v201912
class v201912_dnflag(v201812_dnflag): pass
class v201912_flag(v201812_flag): pass
class v201912_freqbandId(v201812_freqbandId): pass
class v201912_mode(v201812_mode): pass
class v201912_sensor(v201812_sensor): pass
class v201912_t0(v201812_t0): pass
class v201912_sm(v201812_sm): pass
class v201912_sm_uncertainty(v201812_sm_uncertainty): pass


