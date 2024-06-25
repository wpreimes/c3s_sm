from c3s_sm.const import fntempl as _default_template
from c3s_sm.download import infer_file_props


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
