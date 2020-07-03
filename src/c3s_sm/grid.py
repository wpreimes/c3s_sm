# -*- coding: utf-8 -*-

from smecv_grid.grid import SMECV_Grid_v052
from pygeogrids.grids import CellGrid

def cut_grid_bbox(grid, bbox=None):
    """
    Cut a grid to the area of the passed bbox

    Parameters
    ----------
    grid : CellGrid
        Input Grid to cut to bbox
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat)
        Bounding box to create subset for, if None is passed a global
        grid is used.

    Returns
    -------
    grid : CellGrid
        The cut input grid
    """

    if bbox is not None:
        sgpis = grid.get_bbox_grid_points(
            latmin=bbox[1], latmax=bbox[3],
            lonmin=bbox[0], lonmax=bbox[2])

        return grid.subgrid_from_gpis(sgpis)
    else:
        return grid

def C3SCellGrid(subset_flag='land', subset_value=1., bbox=None):
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
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat)
        Bounding box to create subset for, if None is passed a global
        grid is used.

    Returns
    -------
    c3s_glob_grid : CellGrid
        Global/bbox grid
    """

    glob_grid = SMECV_Grid_v052(subset_flag, subset_value)

    if bbox is not None:
        return cut_grid_bbox(glob_grid, bbox)
    else:
        return glob_grid


def C3SLandGrid(bbox=None):
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

    return C3SCellGrid(subset_flag='land', subset_value=1., bbox=bbox)


