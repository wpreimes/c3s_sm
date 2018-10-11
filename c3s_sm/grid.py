# -*- coding: utf-8 -*-

from pygeogrids.grids import BasicGrid, CellGrid
import numpy as np
try:
    from smecv_grid.grid import SMECV_Grid_v042
except:
    import warnings
    warnings.warn('SMECV grid is not installed')

def C3SCellGrid():
    '''
    Returns
    -------
    grid : CellGrid
        The global QDEG grid
    '''
    resolution = 0.25
    lon, lat = np.meshgrid(
        np.arange(-180 + resolution / 2, 180 + resolution / 2, resolution),
        np.flipud(np.arange(-90 + resolution / 2, 90 + resolution / 2, resolution)))

    return BasicGrid(lon.flatten(), lat.flatten()).to_cell_grid(cellsize=5.)

def C3SLandPoints(grid):
    '''
    Create a subset of land points.
    Returns
    -------
    points : np.array
        Points in the passed grid that are over land
    dist : np.array
        Distance between the reference land points and the next point in the
        passed grid.
    '''
    lg = SMECV_Grid_v042('land')
    lat = lg.get_grid_points()[2]
    lon = lg.get_grid_points()[1]

    points, dist =  grid.find_nearest_gpi(lon, lat)

    return points, dist


def C3SLandGrid():
    '''
    0.25deg cell grid of land points from c3s land mask.

    Returns
    -------
    landgrid : CellGrid
        The reduced QDEG grid
    '''
    grid = C3SCellGrid()
    land_gpis, dist = C3SLandPoints(grid)
    if any(dist) > 0:
        raise Exception('C3S grid does not conform with QDEG grid')
    return grid.subgrid_from_gpis(land_gpis)


if __name__ == '__main__':
    grid = C3SCellGrid()
    shape = grid.get_grid_points()[0].size
    assert shape == 1036800

    landpoints, dist = C3SLandPoints(grid)

    land_grid = C3SLandGrid()
    shape = land_grid.get_grid_points()[0].size
    assert shape == 244243

