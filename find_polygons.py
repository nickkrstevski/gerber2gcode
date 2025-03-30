from pocketing import pocketing
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from helpers import add_polygon_to_plot, recur_is_bounded

from pygerber.gerberx3.parser2.commands2.arc2 import CCArc2
from pygerber.gerberx3.parser2.commands2.line2 import Line2
from pygerber.gerberx3.parser2.commands2.flash2 import Flash2
from pygerber.gerberx3.parser2.commands2.region2 import Region2
from pygerber.gerberx3.parser2.commands2.aperture_draw_command2 import ApertureDrawCommand2

from pygerber.gerberx3.api.v2 import GerberFile, FileTypeEnum, Project, ParsedFile, GerberFileInfo
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Point, Polygon
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
plt.gca().set_aspect('equal', adjustable='box')
TOOLHEAD = 1

outline_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM1",FileTypeEnum.INFER_FROM_ATTRIBUTES)
mask_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM10",FileTypeEnum.INFER_FROM_ATTRIBUTES)

outline_info = outline_gerber.parse().get_info()

parsed_outline = mask_gerber.parse()

poly_originals = []
polys = []
for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Region2):
            coordinates = []
            for cmd in command.command_buffer:
                cmd: Line2
                coordinates.append((cmd.start_point.x.value,cmd.start_point.y.value))
            poly_original = Polygon(coordinates)
            poly = Polygon(coordinates).buffer(-TOOLHEAD/2,resolution=16, join_style=1)
            poly_originals.append(poly_original)
            polys.append(poly)
# generate tool paths
all_toolpaths=[]
all_travelpaths=[]
for poly in polys:
    toolpaths, travelpaths = pocketing.contour.contour_parallel(poly, TOOLHEAD)
    all_toolpaths.append(toolpaths)
    all_travelpaths.append(travelpaths)

for poly in poly_originals:    
    add_polygon_to_plot(poly, ax, color='blue', alpha=0.3)

# visualize by plotting
for toolpaths in all_toolpaths:
    for toolpath in toolpaths:
        plt.plot(*toolpath.T, color='black')
for toolpaths in all_travelpaths:
    for toolpath in toolpaths:
        plt.plot(*toolpath.T, color='red')

plt.show()