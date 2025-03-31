import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Point, Polygon
import numpy as np
from pygerber.gerberx3.parser2.command_buffer2 import CommandBuffer2
from pygerber.gerberx3.parser2.commands2.arc2 import CCArc2
from pygerber.gerberx3.parser2.commands2.line2 import Line2
from pygerber.gerberx3.parser2.commands2.flash2 import Flash2
from pygerber.gerberx3.parser2.commands2.region2 import Region2
from pygerber.gerberx3.parser2.commands2.aperture_draw_command2 import ApertureDrawCommand2
from pygerber.gerberx3.math.bounding_box import BoundingBox
from pygerber.gerberx3.api.v2 import GerberFile, FileTypeEnum, Project, ParsedFile, GerberFileInfo

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import re

def add_polygon_to_plot(polygon, ax, color='blue', alpha=0.5):
    if polygon.is_empty:
        return
    if polygon.geom_type == 'Polygon':
        coords = np.array(polygon.exterior.coords)
        patch = patches.Polygon(coords, closed=True, facecolor=color, edgecolor='black', alpha=alpha)
        ax.add_patch(patch)
    elif polygon.geom_type == 'MultiPolygon':
        for poly in polygon:
            add_polygon_to_plot(poly, ax, color, alpha)


def recur_is_bounded(command: ApertureDrawCommand2, bounding_info: GerberFileInfo) -> bool:
    '''
    Check if each command is with the bounding box of the outline.
    Recursively checks all lines within regions.
    '''
    if isinstance(command, Line2) or isinstance(command, CCArc2):
        if command.start_point.y.value<=bounding_info.max_y_mm or command.end_point.y.value<=bounding_info.max_y_mm:
            return True
    elif isinstance(command,Region2):
        return all(recur_is_bounded(cmd,bounding_info) for cmd in command.command_buffer)
    elif isinstance(command,Flash2):
        return command.flash_point.y.value<=bounding_info.max_y_mm
    else:
        print(f"Command {command} not printed")
        return False




# animate_gcode("./drawing.gcode","./animation.gif")