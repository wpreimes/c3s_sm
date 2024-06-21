# Downloading C3S SM data via API

This packages provides a simple command line tool to download C3S Satellite
Soil Moisture data from CDS. This is just a wrapper around the [CDS python
API](https://pypi.org/project/cdsapi/) that should work for any datasets on
the CDS.

There are 2 download tools in this package. They are available after running 
``pip install c3s_sm``.
1) ``c3s_sm download`` takes a time range, version etc. and will download the
respective C3S Satellite Soil Moisture images from CDS.
2) ``c3s_sm update`` is similar, but it used to search for new images for a
locally existing record collection. It will detect the product, version and 
locally available data and download any new images that have appeared online
since the last update (e.g. you can set up a cron job to keep your records 
up-to-date)

Before any of the 2 scripts can be used, you must provide your CDS API key. 
Follow this guide: https://cds.climate.copernicus.eu/api-how-to#install-the-cds-api-key

Make sure that 
- On Linux: You have your credentials stored in `$HOME/.cdsapirc`
- On Windows: Your have your credentials stored in `%USERPROFILE%\.cdsapirc`,
%USERPROFILE% is usually located at C:\Users\Username folder
- On MacOS: Your have your credentials stored in `~/.cdsapirc`

Alternatively you can pass your UID and API Key (that you get from your CDS
profile page) directly with the download command (but the .cdsapirc option
is safer).

## c3s_sm download

Type ``c3s_sm download --help`` to see the full help page. A path is
always required (where the downloaded data is stored), all other arguments are 
optional.

Example command to download the daily passive product v202212 in the period from
2019-05-01 to 2019-05-10 (change the token and target path accordingly).

```
c3s_sm download /target/path -s 2019-05-01 -e 2019-05-10 --product passive 
--freq daily -v v202212 --cds_token XXXX:xxxx-xxxxxx-xxxx-xxxx
```

This will create a subfolder for each year in the target directory and store 
individual downloaded images there.

```
/target/path/
├── 2019/
│   ├── C3S-SOILMOISTURE-L3S-SSMV-PASSIVE-DAILY-20190501000000-TCDR-v202212.0.0.nc
│   ├── C3S-SOILMOISTURE-L3S-SSMV-PASSIVE-DAILY-20190502000000-TCDR-v202212.0.0.nc
│   ├── ...
├── .../
```

## c3s_sm update