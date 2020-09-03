# -*- coding: utf-8 -*-

from tempfile import mkdtemp
import os
from datetime import datetime
import matplotlib.pyplot as plt

# first download some C3S Soil Moisture data


workdir = mkdtemp()
print(f'All data and results will be stored in {workdir}')

from c3s_sm.download import download_and_extract

download_dir = os.path.join(workdir, 'raw_data')
download_and_extract(target_path=download_dir,
                     startdate=datetime(2019,1,1), enddate=datetime(2019,12,31),
                     sensor='combined', aggregation='dekadal',
                     version='v201912.0.0', keep_original=False)


from c3s_sm.interface import C3SDs
from c3s_sm.grid import C3SCellGrid


bbox_europe = (-11, 34, 43, 71)
europe_grid = C3SCellGrid().subgrid_from_bbox(*bbox_europe)
dataset = C3SDs(os.path.join(workdir, 'raw_data'), grid=europe_grid)

# look at one soil moisture image in summer
image_2019_7_1 = dataset.read(datetime(2019,7,1))
plt.imshow(image_2019_7_1.data['sm'])
plt.show()

# now write spatial subsets as new images
europe_data_dir = os.path.join(workdir, 'europe_subsets')
os.makedirs(europe_data_dir, exist_ok=True)

# Finally use the newly generated files together with the matching grid
# to create time series for the selected area.
from c3s_sm.reshuffle import reshuffle




