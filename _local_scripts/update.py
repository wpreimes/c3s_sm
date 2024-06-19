from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from cadati.dekad import dekad_index, dekad2day, day2dekad

from c3s_sm.download import download_and_extract
from c3s_sm.download import infer_file_props

def first_missing_date(last_date, freq='daily'):
    assert freq in ['daily', 'dekadal', 'monthly'], \
        "Freq must be daily, dekadal, or monthly"
    if freq == 'daily':
        next_date = last_date + relativedelta(days=1)
    elif freq == 'monthly':
        next_date = last_date + relativedelta(months=1)
    elif freq == 'dekadal':
        this_dekad = day2dekad(last_date.day)
        if last_date.day not in [1, 11, 21]:
            raise ValueError("Dekad day must be 1, 11 or 21")
        if (this_dekad == 1) or (this_dekad == 2):
            next_date = last_date + relativedelta(days=10)
        else:
            next_date = last_date + relativedelta(months=1)
            next_date = datetime(next_date.year, next_date.month, 1)

    return next_date

def update_c3s_images(data_root):
    """
    Update C3S data in out path

    Parameters:
    -----------
    data_root : str
        Path where the data is and new files are stored to. Can container
        subfolder for years (daily images) or nc files directly.
    """

    props = infer_file_props(data_root)

    freq = props['temp'].lower()
    sensor = props['prod'].lower()
    version = props['vers']

    last_available_date = pd.to_datetime(freq['datetime']).to_pydatetime()

    startdate = first_missing_date(last_available_date, freq=freq)

    download_and_extract(data_root, startdate=startdate, freq=freq,
                         version=version, sensor=sensor,
                         keep_original=False)


if __name__ == '__main__':
    update_c3s_images('/data-read/USERS/wpreimes/temp/c3s/monthly/')