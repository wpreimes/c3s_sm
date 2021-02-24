# -*- coding: utf-8 -*-

import pytest
from c3s_sm.metadata import C3S_daily_tsatt_nc, C3S_SM_TS_Attrs_v201912, C3S_dekmon_tsatt_nc, C3S_SM_TS_Attrs

@pytest.mark.parametrize("sens", ["active", "passive", "combined"])
def test_daily_metadata_default(sens):
    default_attr = C3S_SM_TS_Attrs(sens, version='v201912')

    assert(default_attr.version == 'v201912')
    assert(default_attr.sensor_type == sens)
    assert(default_attr.sm_units == "percentage (%)" if sens == 'active' else 'm3 m-3')

    default_attr.flag()
    assert(default_attr.flag_values[0] == '0')
    assert(default_attr.flag_meanings[0] == 'no_data_inconsistency_detected')
    assert(default_attr.flag_values[5] == 'Bit4')
    assert(default_attr.flag_meanings[5] == 'weight_of_measurement_below_threshold')

    default_attr.freqbandID_flag()
    assert (default_attr.freqbandID_flag_values[0] == '0')
    assert (default_attr.freqbandID_flag_meanings[0] == 'NaN')

    assert (default_attr.freqbandID_flag_values[5] == 'Bit4')
    assert (default_attr.freqbandID_flag_meanings[5] == 'C69')

    default_attr.sensor_flag()
    assert (default_attr.sensor_flag_values[0] == '0')
    assert (default_attr.sensor_flag_meanings[0] == 'NaN')

    assert (default_attr.sensor_flag_values[5] == 'Bit4')
    assert (default_attr.sensor_flag_meanings[5] == 'WindSat')

    default_attr.mode_flag()
    assert (default_attr.mode_flag_values[0] == '0')
    assert (default_attr.mode_flag_meanings[0] == 'NaN')

    assert (default_attr.mode_flag_values[1] == 'Bit0')
    assert (default_attr.mode_flag_meanings[1] == 'ascending')

def test_C3s_daily_tsatt_nc():
    cdr_type = 'TCDR'
    sensor = 'active'
    dob = C3S_daily_tsatt_nc(cdr_type=cdr_type, sensor_type=sensor,
                             cls=C3S_SM_TS_Attrs_v201912)

    glob = dob.global_attr

    assert glob == {'product': f'C3S SOILMOISTURE L3S SSMS {sensor.upper()} DAILY TCDR v201912',
                    'resolution': '0.25 degree',
                    'temporalspacing': 'daily'}
    assert dob.ts_attributes['flag']['flag_values'].size == 8

    sm_should = {'units': 'percentage (%)',
                 'full_name': 'Percent of Saturation Soil Moisture Uncertainty'}
    assert dob.ts_attributes['sm'] == sm_should

    assert dob.ts_attributes['mode']['flag_values'].size == 3

    t0_should = {'units': 'days since 1970-01-01 00:00:00 UTC',
                 'full_name': 'Observation Timestamp'}
    for k, v in t0_should.items(): assert dob.ts_attributes['t0'][k] == v

def test_C3s_dekmon_tsatt_nc():
    subtype = 'TCDR'
    sensor = 'passive'
    dob = C3S_dekmon_tsatt_nc(product_temp_res='monthly',
                              cdr_type=subtype,
                              sensor_type=sensor,
                              cls=C3S_SM_TS_Attrs_v201912)

    glob = dob.global_attr

    assert glob['product'] == f'C3S SOILMOISTURE L3S SSMV {sensor.upper()} MONTHLY TCDR v201912'
    assert glob['resolution'] =='0.25 degree'
    assert glob['temporalspacing'] == f'monthly'

    assert dob.ts_attributes['freqbandID']['flag_values'].size == 9

    sm_should = {'units': 'm3 m-3', 'full_name': 'Volumetric Soil Moisture'}
    assert dob.ts_attributes['sm'] == sm_should

    assert dob.ts_attributes['nobs'] == {'full_name': 'Number of valid observation'}

    assert dob.ts_attributes['sensor']['flag_values'].size == 11
