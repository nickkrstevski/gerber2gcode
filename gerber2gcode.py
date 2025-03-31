from pygerber.gerberx3.api.v2 import GerberFile, FileTypeEnum, Project, ParsedFile, GerberFileInfo
from pygerber.gerberx3.parser2.command_buffer2 import CommandBuffer2
from pygerber.gerberx3.parser2.commands2.arc2 import CCArc2
from pygerber.gerberx3.parser2.commands2.line2 import Line2
from pygerber.gerberx3.parser2.commands2.flash2 import Flash2
from pygerber.gerberx3.parser2.commands2.region2 import Region2
from pygerber.gerberx3.parser2.commands2.aperture_draw_command2 import ApertureDrawCommand2
import matplotlib.pyplot as plt
from shapely import Polygon
from helpers import add_polygon_to_plot, recur_is_bounded

outline_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM1",FileTypeEnum.INFER_FROM_ATTRIBUTES)
mask_gerber = GerberFile.from_file("./gerbers/1930238-00-D_02-1.GM10",FileTypeEnum.INFER_FROM_ATTRIBUTES)

outline_info = outline_gerber.parse().get_info()

parsed_outline = mask_gerber.parse()

custom_command_buffer_solid: CommandBuffer2 = CommandBuffer2()
custom_command_buffer_hatch: CommandBuffer2 = CommandBuffer2()

# FORM THE HATCH AND SOLID COMMAND BUFFERS
for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Line2) or isinstance(command,CCArc2):
            custom_command_buffer_hatch.add_command(command)

for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Region2) or isinstance(command,Flash2):
            custom_command_buffer_solid.add_command(command)

fig, ax = plt.subplots(figsize=(8, 8))
plt.gca().set_aspect('equal', adjustable='box')

polys = []
for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Region2):
            coordinates = []
            for cmd in command.command_buffer:
                cmd: Line2
                coordinates.append((cmd.start_point.x.value,cmd.start_point.y.value))
            polys.append(Polygon(coordinates))
            add_polygon_to_plot(Polygon(coordinates), ax, color='red', alpha=0.5)

plt.show()
exit()

custom_readonly_command_buffer_hatch = custom_command_buffer_hatch.get_readonly()
custom_parsed_hatch = ParsedFile(
        GerberFileInfo.from_readonly_command_buffer(custom_readonly_command_buffer_hatch),
        custom_readonly_command_buffer_hatch,
        FileTypeEnum.EDGE,
    )
custom_parsed_hatch.render_raster("test_hatch.png")
custom_parsed_hatch.render_svg("test_hatch.svg")

custom_readonly_command_buffer_solid = custom_command_buffer_solid.get_readonly()
custom_parsed_solid = ParsedFile(
        GerberFileInfo.from_readonly_command_buffer(custom_readonly_command_buffer_solid),
        custom_readonly_command_buffer_solid,
        FileTypeEnum.EDGE,
    )
custom_parsed_solid.render_raster("test_solid.png")
custom_parsed_solid.render_svg("test_solid.svg")