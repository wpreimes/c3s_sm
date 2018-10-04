# -*- coding: utf-8 -*-

from pygeogrids.grids import BasicGrid, CellGrid
import numpy as np
from smecv_grid.grid import SMECV_Grid_v042

def C3SCellGrid():
    '''
    Returns
    -------
    grid : CellGrid
    '''
    resolution = 0.25
    lon, lat = np.meshgrid(
        np.arange(-180 + resolution / 2, 180 + resolution / 2, resolution),
        np.flipud(np.arange(-90 + resolution / 2, 90 + resolution / 2, resolution)))

    return BasicGrid(lon.flatten(), lat.flatten()).to_cell_grid(cellsize=5.)

def C3SLandPoints(grid):
    lg = SMECV_Grid_v042('land')
    lat = lg.get_grid_points()[2]
    lon = lg.get_grid_points()[1]

    points, dist =  grid.find_nearest_gpi(lon, lat)

    return points, dist


def C3SLandGrid():
    '''
    0.25deg cell grid of land points from gldas land mask.
    :return: global QDEG-LandGrid
    '''
    grid = C3SCellGrid()
    land_gpis, dist = C3SLandPoints(grid)
    if any(dist) > 0:
        raise Exception('GLDAS grid does not conform with QDEG grid')
    return grid.subgrid_from_gpis(land_gpis)


if __name__ == '__main__':
    grid = C3SCellGrid()
    shape = grid.get_grid_points()[0].size
    assert shape == 1036800

    landpoints, dist = C3SLandPoints(grid)

    land_grid = C3SLandGrid()
    shape = land_grid.get_grid_points()[0].size
    assert shape == 244243

