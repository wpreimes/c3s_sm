
def mkdate(datestring:str) -> datetime:
    # datestring to datetime
    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')

def parse_args(args):
    """
    Parse command line parameters for recursive download
    Parameters
    ----------
    args : list
        Command line parameters as list of strings

    Returns
    ----------
    clparams : argparse.Namespace
        Parsed command line parameters
    """

    parser = argparse.ArgumentParser(
        description="Download C3S SM images in a period. "
                    "Before this program can be used, you have to register at the CDS "
                    "and setup your .cdsapirc file as described here: "
                    "https://cds.climate.copernicus.eu/api-how-to")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the downloaded data will be stored.')
    parser.add_argument("-s", "--start", type=mkdate,
                        default='1978-11-01',
                        help=("Startdate in format YYYY-MM-DD. "
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate,
                        default=datetime.now().date().isoformat(),
                        help=("Enddate in format YYYY-MM-DD. "
                              "If not given then the current date is used."))
    parser.add_argument("-f", "--freq", type=str, default='daily',
                        help=("The C3S SM sensor product temporal sampling frequency to download. "
                              "Choose one of 'daily', 'dekadal', 'monthly'. "
                              "Default is 'daily'."))
    parser.add_argument("-p", "--sensor", type=str, default='combined',
                        help=("The C3S SM sensor product to download. "
                              "Choose one of 'combined', 'active', 'passive'. "
                              "Default is 'combined'."))
    parser.add_argument("-v", "--version", type=str, default='v202212',
                        help=("The C3S SM product version to download. "
                              "Choose one that is on the CDS, "
                              "e.g. 'deprecated_v201912', 'v201706', 'v201812', "
                              "'v201912_1', 'v202012', 'v202212', 'v202312'"
                              "Default is 'v202212'"))
    parser.add_argument("-keep", "--keep_original", type=bool, default=False,
                        help=("Also keep the originally, temporarily downloaded image stack instead of deleting it "
                              "after extracting single images. Default is False."))

    args = parser.parse_args(args)

    print(f"Downloading C3S CDR/ICDR SM {args.freq} {args.sensor} "
          f"from {args.start.isoformat()} to {args.end.isoformat()} "
          f"into {args.localroot}")

    return args


def main(args):
    args = parse_args(args)
    download_and_extract(target_path=args.localroot,
                         startdate=args.start,
                         enddate=args.end,
                         sensor=args.sensor,
                         freq=args.freq,
                         version=args.version,
                         keep_original=args.keep_original)






def parse_args(args):
    """
    Parse command line parameters for C3S reshuffling.

    Parameters
    ----------
    args : list of str
        Command line parameters as list of strings.

    Returns
    -------
    args : argparse.Namespace
        Command line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Convert C3s image data to time series format.")
    parser.add_argument("dataset_root",
                        help='Root of local filesystem where the '
                             'data is stored.')

    parser.add_argument("timeseries_root",
                        help='Root of local filesystem where the timeseries '
                             'should be stored.')

    parser.add_argument("start", type=mkdate,
                        help=("Startdate. In format YYYY-MM-DD"))

    parser.add_argument("end", type=mkdate,
                        help=("Enddate. In format YYYY-MM-DD"))

    parser.add_argument("--parameters", metavar="parameters", default=None,
                        nargs="+",
                        help=("Parameters to reshuffle into time series format. "
                              "E.g. sm for creating soil moisture time series."
                              "If None are passed, all variables from the first image file in the path are used."))

    parser.add_argument("--land_points", type=str2bool, default='False',
                        help=("Set True to convert only land points as defined"
                              " in the C3s land mask (faster and less/smaller files)"))

    parser.add_argument("--bbox", type=float, default=None, nargs=4,
                        help=("min_lon min_lat max_lon max_lat. "
                              "Bounding Box (lower left and upper right corner) "
                              "of area to reshuffle (WGS84)"))

    parser.add_argument("--ignore_meta", type=str2bool, default='False',
                        help=("Do not apply image metadata to the time series."
                              "E.g. for unsupported data versions."))

    parser.add_argument("--fntempl", type=str, default=_default_template,
                        help=("Filename template to parse datetime from. Must contain"
                              "a {datetime} placeholder"))


    parser.add_argument("--imgbuffer", type=int, default=200,
                        help=("How many images to read at once. Bigger "
                              "numbers make the conversion faster but "
                              "consume more memory."))

    args = parser.parse_args(args)
    # set defaults that can not be handled by argparse

    print(f"Converting data from {args.start.isoformat()} to"
          f" {args.end.isoformat()} into folder {args.timeseries_root}.")

    return args


def main(args):
    """
    Main routine used for command line interface.
    Parameters
    ----------
    args : list of str
        Command line arguments.
    """
    args = parse_args(args)

    reshuffle(args.dataset_root,
              args.timeseries_root,
              args.start,
              args.end,
              args.parameters,
              land_points=args.land_points,
              bbox=args.bbox,
              ignore_meta=args.ignore_meta,
              imgbuffer=args.imgbuffer)