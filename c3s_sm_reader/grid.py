# -*- coding: utf-8 -*-

from smecv_grid.grid import SMECV_Grid_v042

def C3SCellGrid(subset='land'):
    return SMECV_Grid_v042(subset_flag=subset)