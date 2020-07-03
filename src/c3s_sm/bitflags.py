# -*- coding: utf-8 -*-

from c3s_sm.bitflag_shuffle import BitFlagShuffler

class ProductBitFlag(BitFlagShuffler):
    def __init__(self, *args, active_bits=None, passive_bits=None):
        """
        Parameters
        ----------
        args :
            Passed to BitFlagShuffler
        active_bits : list
            Bit values that are valid for active sensors
        passive_bits : list
            Bit values that are valid for passive sensors
        """
        self.active_bits = active_bits
        self.passive_bits = passive_bits
        super(ProductBitFlag, self).__init__(*args)

    def get_active(self):
        # get sensor flags for active sensors only (exclude passive from combined)
        return self.df4bit(include_bits=self.active_bits,
                           exclude_bits=self.passive_bits)

    def get_passive(self):
        # get sensor flags for passive sensors only (exclude active from combined)
        return self.df4bit(include_bits=self.passive_bits,
                           exclude_bits=self.active_bits)

    def get_combined(self):
        # get sensor flag for all sensors
        return self.df # no filtering necessary


class C3SSMQualityFlag(BitFlagShuffler):
    # Describes the quality flag values. These are the same for all 3 products
     def __init__(self):
         super(C3SSMQualityFlag, self).__init__(
             'no_data_inconsistency_detected',                                  # None, int(0)
             'snow_coverage_or_temperature_below_zero',                         # b1,  bit0
             'dense_vegetation',                                                # b2,  bit1
             'others_no_convergence_in_the_model_thus_no_valid_sm_estimates',   # b4,  bit2
             'soil_moisture_value_exceeds_physical_boundary',                   # b8,  bit3
             'weight_of_measurement_below_threshold',                           # b16, bit4
             'all_datasets_deemed_unreliable',                                  # b32, bit5
         )

         # combine flags like: combination_of_flag_values_1_and_2
         super(C3SSMQualityFlag, self).build(
             True, 'combination_of_flag_values_', '_and_', '')

class C3SSmSensorFlag(ProductBitFlag):
    # Sensors used in the COMBINED products of C3S SM (v2017xx, v2018xx, v2019xx)
    def __init__(self):
        super(C3SSmSensorFlag, self).__init__(
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
        super(C3SSmSensorFlag, self).build(False, '', '+', '')


class C3SSmFreqbandId(ProductBitFlag):
    def __init__(self):
        super(C3SSmFreqbandId, self).__init__(
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
        super(C3SSmFreqbandId, self).build(False, '', '+', '')

class C3SSmDnFlag(BitFlagShuffler):
    def __init__(self):
        super(C3SSmDnFlag, self).__init__('NaN', 'day', 'night')
        # combine flags like: day_night_combination
        super(C3SSmDnFlag, self).build(False, '', '_', 'combination')
