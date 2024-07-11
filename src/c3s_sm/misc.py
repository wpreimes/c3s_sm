import os
from glob import glob
import pandas as pd
import yaml
from parse import parse
from c3s_sm.const import fntempl as _default_template
from netCDF4 import Dataset, num2date



def infer_file_props(path: str,
                     fntempl: str = _default_template,
                     start_from='last') -> dict:
    """
    Parse file names to retrieve properties from :func:`c3s_sm.const.fntempl`.
    """
    files = glob(os.path.join(path, '**', '*.nc'), recursive=True)
    files.sort()
    if len(files) == 0:
        raise ValueError(f"No matching files for chosen template found in "
                         f"the directory {path}")
    else:
        if start_from.lower() == 'last':
            files = files[::-1]
        elif start_from.lower() == 'first':
            pass
        else:
            raise NotImplementedError(f"`start_from` must be one of: "
                                      f"`first`, `last`.")
        for f in files:
            file_args = parse(fntempl,  os.path.basename(f))
            if file_args is None:
                continue
            return file_args.named

    raise ValueError(f"No matching files for chosen template found in the "
                     f"directory {path}")


def read_overview_yml(path: str) -> dict:
    """
    Read image summary and return fields as dict.
    """
    with open(path, 'r') as stream:
        props = yaml.safe_load(stream)
    return props

def update_ts_summary(data_path, out_file=None,
                      fn_templ="[0-9][0-9][0-9][0-9].nc",
                      verify_with=1):
    """
    Summarize time series metadata as yml file.
    Open first cell file in data_path and extract the available time range.
    If multiple files are available verify at least with 2 other files.
    Then write the summary to out_file.
    """
    fl = glob(os.path.join(data_path, '**', fn_templ), recursive=True)

    props = dict(period_from=None, period_to=None)

    for v in ['product', 'temporal_sampling', 'version']:
        props[v] = None

    if len(fl) == 0:
        raise ValueError(f"No matching files found in {data_path}")
    if len(fl) <= verify_with:
        verify_with = len(fl) - 1

    i = 0
    while i < verify_with:
        with Dataset(fl[i], mode='r') as ds:
            t = ds['time'][:]
            units = ds['time'].getncattr('units')

            kwargs = dict(times=t, units=units, only_use_cftime_datetimes=False,
                          only_use_python_datetimes=True)
            try:
                calendar = ds['time'].getncattr('calendar')
                kwargs['calendar'] = calendar
            except AttributeError:
                pass

            dt = pd.DatetimeIndex(
                num2date(**kwargs))

            end_date = str(dt[-1].to_pydatetime())
            start_date = str(dt[0].to_pydatetime())

            if props['period_to'] is None:
                props['period_to'] = end_date
            else:
                assert props['period_to'] == end_date, "Unexpected end date"

            if props['period_from'] is None:
                props['period_from'] = start_date
            else:
                assert props['period_from'] == start_date, "Unexpected start date"

            for k in props.keys():
                if k in ['period_from', 'period_to']:
                    continue
                else:
                    if props[k] is None:
                        try:
                            p = ds.getncattr(k)
                        except AttributeError:
                            p = None
                        props[k] = p

        i += 1

    if out_file is None:
        out_file = os.path.join(data_path, f"000_overview.yml")

    with open(out_file, 'w') as f:
        yaml.dump(props, f, default_flow_style=False)

def update_image_summary(data_path: str, out_file=None,
                         fntempl: str = _default_template):
    """
    Summarize image metadata as yml file

    Parameters
    ----------
    data_path: str
        Root path to the image archive
    out_file: str, optional (default: None)
        Path to summary file. File will be created/updated.
        If not specified, then `data_path` is used. If a file already exists,
        it will be overwritten.
    fntempl: str, optional
        The filename template used to parse image file names.
        Must contain a field `datetime` that indicates the location of the
        image time stamp in the filename.
    """
    first_image_date = get_first_image_date(data_path, fntempl=fntempl)
    last_image_date = get_last_image_date(data_path, fntempl=fntempl)

    props = infer_file_props(data_path, start_from='first')
    _ = props.pop("datetime")
    props['period_from'] = str(pd.to_datetime(first_image_date).date())
    props['period_to'] = str(pd.to_datetime(last_image_date).date())

    if out_file is None:
        out_file = os.path.join(data_path, f"000_overview.yml")

    with open(out_file, 'w') as f:
        yaml.dump(props, f, default_flow_style=False)


def get_first_image_date(path: str, fntempl: str = _default_template) -> str:
    """
    Parse files in the given directory (or any subdir) using the passed
    filename template. props will contain all fields specified in the template.
    the `datetime` field is required and used to determine the first image date.

    Parameters
    ----------
    path: str
        Path to the directory containing the image files
    fntempl: str, optional
        The filename template used to parse image file names.
        Must contain a field `datetime` that indicates the location of the
        image time stamp in the filename.

    Returns
    -------
    date: str
        Parse date from the first found image file that matches `fntempl`.
    """
    try:
        props = infer_file_props(path, fntempl=fntempl,
                                 start_from='first')
        startdate = props['datetime']
    except ValueError:
        raise ValueError('Could not infer start date from image files. '
                         'Please specify startdate manually.')
    return startdate


def get_last_image_date(path: str, fntempl: str) -> str:
    """
    Parse files in the given directory (or any subdir) using the passed
    filename template. props will contain all fields specified in the template.
    the `datetime` field is required and used to determine the last image date.

    Parameters
    ----------
    path: str
        Path to the directory containing the image files
    fntempl: str (optional)
        The filename template used to parse image file names.
        Must contain a field `datetime` that indicates the location of the
        image time stamp in the filename.

    Returns
    -------
    date: str
        Parse date from the last found image file that matches `fntempl`.
    """
    try:
        props = infer_file_props(path, fntempl=fntempl,
                                 start_from='last')
        enddate = props['datetime']
    except ValueError:
        raise ValueError('Could not infer end date from image files. '
                         'Please specify enddate manually.')
    return enddate
