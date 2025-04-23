from pygerber.gerberx3.api.v2 import GerberFile, FileTypeEnum, Project, ParsedFile, GerberFileInfo
from pygerber.gerberx3.parser2.command_buffer2 import CommandBuffer2
from pygerber.gerberx3.parser2.commands2.arc2 import CCArc2
from pygerber.gerberx3.parser2.commands2.line2 import Line2
from pygerber.gerberx3.parser2.commands2.flash2 import Flash2
from pygerber.gerberx3.parser2.commands2.region2 import Region2
from pygerber.gerberx3.parser2.commands2.aperture_draw_command2 import ApertureDrawCommand2
from pocketing import pocketing
import matplotlib.pyplot as plt
import numpy as np
from shapely import Polygon
from helpers import add_polygon_to_plot, recur_is_bounded, sort_polygons_by_min_x
from gcode import GCode

outline_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM1",FileTypeEnum.INFER_FROM_ATTRIBUTES)
mask_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM10",FileTypeEnum.INFER_FROM_ATTRIBUTES)

outline_info = outline_gerber.parse().get_info()

parsed_outline = mask_gerber.parse()

TOOLHEAD = 2
points = []

custom_command_buffer_solid: CommandBuffer2 = CommandBuffer2()
custom_command_buffer_hatch: CommandBuffer2 = CommandBuffer2()

# FORM THE HATCH AND SOLID COMMAND BUFFERS
for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Line2) or isinstance(command,CCArc2):
            custom_command_buffer_hatch.add_command(command)
            points.append((float(command.start_point.x.value),float(command.start_point.y.value)))
            points.append((float(command.end_point.x.value),float(command.end_point.y.value)))

# fig, ax = plt.subplots(figsize=(8, 8))
# plt.gca().set_aspect('equal', adjustable='box')

custom_readonly_command_buffer_hatch = custom_command_buffer_hatch.get_readonly()
custom_parsed_hatch = ParsedFile(
        GerberFileInfo.from_readonly_command_buffer(custom_readonly_command_buffer_hatch),
        custom_readonly_command_buffer_hatch,
        FileTypeEnum.EDGE,
    )

import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, MultiPoint
from shapely import concave_hull
import matplotlib.pyplot as plt

# Example points (x, y)
# points = np.array([[0, 0], [1, 1], [0.2, 0.7], [10, 10], [11, 11], [10.2, 10.7]])

import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

# Step 1: DBSCAN Clustering
dbscan = DBSCAN(eps=2, min_samples=2)  # Adjust `eps` based on your data
labels = dbscan.fit_predict(points)

# Step 2: Group points by label
grouped_points = {}
for label, point in zip(labels, points):
    if label not in grouped_points:
        grouped_points[label] = []
    grouped_points[label].append(point)

# Step 3: Custom Polygon Generation
polygons: list[Polygon] = []

for label, group in grouped_points.items():
    if label == -1:  # Ignore noise points
        continue
    group = np.array(group)

    if len(group) >= 3:  # At least 3 points required to form a polygon
        # Step 3a: Calculate the center of the group (centroid)
        center = np.mean(group, axis=0)

        # Step 3b: Calculate angle of each point relative to the center
        angles = np.arctan2(group[:, 1] - center[1], group[:, 0] - center[0])

        # Step 3c: Sort points by angle in counterclockwise order
        sorted_indices = np.argsort(angles)
        sorted_points = group[sorted_indices]

        # Step 3d: Create the Shapely Polygon (connect the sorted points)
        polygon = Polygon(sorted_points)  # Create a Shapely Polygon
        polygon = polygon.buffer(0.2,resolution=16, join_style=1)
        polygons.append(polygon)

gcode = GCode("./outputs/hash.gcode")
all_toolpaths=[]
polygons = sort_polygons_by_min_x(polygons)
for poly in polygons:
    if poly.area<20:
        poly = poly.buffer(0.75,16,join_style=1)
    gcode.add_array(pocketing.contour.contour_parallel(poly.buffer(-TOOLHEAD/2), TOOLHEAD))

gcode.save()
gcode.plot_gcode_and_polygons(polygons)

# Step 4: Plot results
plt.figure(figsize=(8, 8))
# Generate distinct colors for each label
unique_labels = set(labels)
colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
# Fill the polygons
for polygon in polygons:
    x, y = polygon.exterior.xy
    plt.fill(x, y, color='blue', alpha=0.5)  # alpha for transparency
# Scatter plot with colors based on groups
for label, point in zip(labels, points):
    color = colors[label % len(colors)] if label != -1 else "black"  # Black for noise
    plt.scatter(point[0], point[1], color=color, edgecolors="k", s=50)
# Ensure equal scaling
plt.axis("equal")
# Remove duplicate legend labels
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), loc="upper left")
plt.show()