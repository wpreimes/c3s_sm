import sys
import os

import warnings
from pathlib import Path
import logging
from datetime import datetime

try:
    import xarray as xr
    xr_supported = True
except ImportError:
    xr_supported = False

# CDSAPI_RC variable must be set or we use home dir
dotrc = os.environ.get('CDSAPI_RC', os.path.join(Path.home(), '.cdsapirc'))

if not os.path.isfile(dotrc):
    url = os.environ.get('CDSAPI_URL')
    key = os.environ.get('CDSAPI_KEY')
    if url is None or key is None:
        warnings.warn('CDS API URL or KEY not found, download will not work! '
                      'Please set CDSAPI_URL and CDSAPI_KEY  or set up a '
                      '.cdsapirc file as described here: '
                      'https://cds.climate.copernicus.eu/api-how-to')
        api_ready = False
    else:
        api_ready = True
else:
    api_ready = True

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



def logger(fname, level=logging.DEBUG, verbose=False):

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(filename=fname, level=level,
                        format='%(levelname)s %(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    if verbose:
        logger.addHandler(logging.StreamHandler(sys.stdout))
    logging.captureWarnings(True)

    assert os.path.exists(fname)

    return logger