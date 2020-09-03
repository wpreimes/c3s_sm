# -*- coding: utf-8 -*-

"""
Load the latest smecv_grid with the option to cut it to a bounding box
"""

from smecv_grid.grid import SMECV_Grid_v052
from pygeogrids.grids import CellGrid

def C3SCellGrid(subset_flag=None, subset_value=1.):
    """
    Load a specific C3S subgrid, different subset flags and values can be
    selected, see the smecv grid package for a description:
    https://github.com/TUW-GEO/smecv-grid

    Parameters
    ----------
    subset_flag : str or None, optional (default: 'land')
        Select a subset that should be loaded, e.g. land, high_vod, rainforest, cci_lc
    subset_value : float or list, optional (default: 1.)
        Select one or more values of the variable that defines the subset,
        i.e 1. for masks (high_vod, land) or a float or list of floats for one or
        multiple ESA CCI Landcover classes (e.g 190 to load urban points only)

    Returns
    -------
    C3SCellgrid : SMECV_Grid_v052
        Global C3S SM Grid
    """
    return SMECV_Grid_v052(subset_flag, subset_value, 5.)

def C3SLandGrid():
    """
    Shortcut to get the (subset) landgrid only.

    Parameters
    ----------
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat)
        Bounding box to create subset for, if None is passed a global
        grid is used.

    Returns
    -------
    c3s_glob_grid : CellGrid
        Global/bbox grid
    """

    return C3SCellGrid(subset_flag='land', subset_value=1.)


if __name__ == '__main__':
    bbox = [-11, 34,43, 71]
    C3SCellGrid(None, bbox=bbox)