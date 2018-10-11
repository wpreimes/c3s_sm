# -*- coding: utf-8 -*-

from c3s_sm.metadata import C3S_daily_tsatt_nc, C3S_SM_TS_Attrs, C3S_dekmon_tsatt_nc


def test_daily_metadata_default_active():

    default_attr = C3S_SM_TS_Attrs('active')

    assert(default_attr.version == 'v0000')
    assert(default_attr.product_sensor_type == 'active')
    assert(default_attr.version_sub_string == '.0.0')
    assert(default_attr.sm_full_name == 'Percent of Saturation Soil Moisture Uncertainty')
    assert(default_attr.sm_units == "percentage (%)")

    default_attr.flag()
    assert(default_attr.flag_values[0] == 0)
    assert(default_attr.flag_meanings.split(' ')[0] == 'no_data_inconsistency_detected')
    assert(default_attr.flag_values[10] == 17)
    assert(default_attr.flag_meanings.split(' ')[10] == 'combination_of_flag_values_1_and_16')

    default_attr.freqbandID_flag()
    assert (default_attr.freqbandID_flag_values[0] == 0)
    assert (default_attr.freqbandID_flag_meanings.split(' ')[0] == 'NaN')

    assert (default_attr.freqbandID_flag_values[10] == 34)
    assert (default_attr.freqbandID_flag_meanings.split(' ')[10] == 'C53+C73')

    default_attr.sensor_flag()
    assert (default_attr.sensor_flag_values[0] == 0)
    assert (default_attr.sensor_flag_meanings.split(' ')[0] == 'NaN')

    assert (default_attr.sensor_flag_values[10] == 132)
    assert (default_attr.sensor_flag_meanings.split(' ')[10] == 'TMI+AMIWS')

    default_attr.mode_flag()
    assert (default_attr.mode_flag_values[0] == 0)
    assert (default_attr.mode_flag_meanings.split(' ')[0] == 'nan')

    assert (default_attr.mode_flag_values[3] == 3)
    assert (default_attr.mode_flag_meanings.split(' ')[3] == 'ascending_descending_combination')


def test_daily_metadata_default_passive_and_combined():
    for sensor in ['passive', 'combined']:
        default_attr = C3S_SM_TS_Attrs(sensor)

        assert (default_attr.version == 'v0000')
        assert (default_attr.product_sensor_type == sensor)
        assert (default_attr.version_sub_string == '.0.0')
        assert (default_attr.sm_full_name == 'Volumetric Soil Moisture Uncertainty')
        assert (default_attr.sm_units == "m3 m-3")

        default_attr.flag()
        assert (default_attr.flag_values[0] == 0)
        assert (default_attr.flag_meanings.split(' ')[0] == 'no_data_inconsistency_detected')
        assert (default_attr.flag_values[10] == 17)
        assert (default_attr.flag_meanings.split(' ')[10] == 'combination_of_flag_values_1_and_16')

        default_attr.freqbandID_flag()
        assert (default_attr.freqbandID_flag_values[0] == 0)
        assert (default_attr.freqbandID_flag_meanings.split(' ')[0] == 'NaN')

        assert (default_attr.freqbandID_flag_values[10] == 34)
        assert (default_attr.freqbandID_flag_meanings.split(' ')[10] == 'C53+C73')

        default_attr.sensor_flag()
        assert (default_attr.sensor_flag_values[0] == 0)
        assert (default_attr.sensor_flag_meanings.split(' ')[0] == 'NaN')

        assert (default_attr.sensor_flag_values[10] == 132)
        assert (default_attr.sensor_flag_meanings.split(' ')[10]== 'TMI+AMIWS')

        default_attr.mode_flag()
        assert (default_attr.mode_flag_values[0] == 0)
        assert (default_attr.mode_flag_meanings.split(' ')[0] == 'nan')

        assert (default_attr.flag_values[3] == 3)
        assert (default_attr.mode_flag_meanings.split(' ')[3] == 'ascending_descending_combination')

def test_C3s_daily_tsatt_nc():
    subtype = 'TCDR'
    sensor = 'active'
    dob = C3S_daily_tsatt_nc(C3S_SM_TS_Attrs, product_sub_type=subtype,
                 product_sensor_type=sensor, sub_version='.9.9')

    glob = dob.global_attr

    assert glob == {'product': 'C3S-SOILMOISTURE-L3S-SSMS-%s-%s-%s-v0000.9.9'
                               %(sensor.upper(), 'DAILY', subtype),
                    'resolution': '0.25 degree',
                    'temporalspacing': 'daily'}
    assert dob.ts_attributes['flag']['flag_values'].size == 18

    sm_should = {'units': 'percentage (%)', 'full_name': 'Percent of Saturation Soil Moisture Uncertainty'}
    assert dob.ts_attributes['sm'] == sm_should

    assert dob.ts_attributes['mode']['flag_values'].size == 4

    t0_should = {'units': 'days since 1970-01-01 00:00:00 UTC', 'full_name': 'Observation Timestamp'}
    assert dob.ts_attributes['t0'] == t0_should

def test_C3s_dekmon_tsatt_nc():
    subtype = 'TCDR'
    sensor = 'passive'
    dob = C3S_dekmon_tsatt_nc(C3S_SM_TS_Attrs, product_sub_type=subtype,
                             product_sensor_type=sensor, sub_version='.9.9')

    glob = dob.global_attr

    assert glob == {'product': 'C3S-SOILMOISTURE-L3S-SSMV-%s-%s-%s-v0000.9.9'
                               % (sensor.upper(), 'MONTHLY', subtype),
                    'resolution': '0.25 degree',
                    'temporalspacing': 'monthly'}
    assert dob.ts_attributes['freqbandID']['flag_values'].size == 19

    sm_should = {'units': 'm3 m-3', 'full_name': 'Volumetric Soil Moisture Uncertainty'}
    assert dob.ts_attributes['sm'] == sm_should

    assert dob.ts_attributes['nobs'] == {'full_name': 'Number of valid observation'}

    t0_should = {'units': 'days since 1970-01-01 00:00:00 UTC', 'full_name': 'Observation Timestamp'}
    assert dob.ts_attributes['sensor']['flag_values'].size == 27


if __name__ == '__main__':
    test_C3s_dekmon_tsatt_nc()
    test_C3s_daily_tsatt_nc()
    test_daily_metadata_default_passive_and_combined()
    test_daily_metadata_default_active()