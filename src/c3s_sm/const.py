import sys
import os

import warnings
from pathlib import Path
import logging
from datetime import datetime
from plistlib import UID

try:
    import xarray as xr
    xr_supported = True
except ImportError:
    xr_supported = False

# CDSAPI_RC variable must be set or we use home dir
dotrc = os.environ.get('CDSAPI_RC', os.path.join(Path.home(), '.cdsapirc'))

def check_api_read() -> bool:
    if not os.path.isfile(dotrc):
        url = os.environ.get('CDSAPI_URL')
        key = os.environ.get('CDSAPI_KEY')
        if url is None or key is None:
            ValueError('CDS API KEY or .cdsapirc file not found, '
                       'download will not work! '
                       'Please create a .cdsapirc file with your credentials'
                       'or pass your uid/key to the command line tool '
                       'See: '
                       'https://cds.climate.copernicus.eu/api-how-to')
            api_ready = False
        elif ":" not in key:
            raise ValueError('Your CDS token is not valid. It must be in the format '
                             '<UID>:<APIKEY>, both of which are found on your CDS'
                             'profile page.')
        else:
            api_ready = True
    else:
        api_ready = True
    return api_ready

variable_lut = {
    'combined': {'variable': 'volumetric_surface_soil_moisture',
                 'type_of_sensor': 'combined_passive_and_active'},
    'passive': {'variable': 'volumetric_surface_soil_moisture',
                'type_of_sensor': 'passive'},
    'active': {'variable': 'soil_moisture_saturation',
               'type_of_sensor': 'active'}
}

freq_lut = {
    'daily': 'day_average',
    'dekadal': '10_day_average',
    'monthly': 'month_average'
}

startdates = {'combined': datetime(1978,11,1),
              'passive': datetime(1978, 11, 1),
              'active': datetime(1991, 8, 5)}


fntempl = "C3S-SOILMOISTURE-L3S-SSM{unit}-{product}-{freq}-{datetime}-{record}-{version}.{subversion}.nc"
