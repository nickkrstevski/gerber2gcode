from pygerber.gerberx3.api.v2 import GerberFile, FileTypeEnum, Project, ParsedFile, GerberFileInfo
from pygerber.gerberx3.parser2.command_buffer2 import CommandBuffer2
from pygerber.gerberx3.parser2.commands2.arc2 import CCArc2
from pygerber.gerberx3.parser2.commands2.line2 import Line2
from pygerber.gerberx3.parser2.commands2.flash2 import Flash2
from pygerber.gerberx3.parser2.commands2.region2 import Region2
from pygerber.gerberx3.parser2.commands2.aperture_draw_command2 import ApertureDrawCommand2
from pygerber.gerberx3.math.bounding_box import BoundingBox
import matplotlib.pyplot as plt

outline_gerber = GerberFile.from_file("./1930238-00-D_02-1.GM1",FileTypeEnum.INFER_FROM_ATTRIBUTES)
mask_gerber = GerberFile.from_file("./1930238-00-D_02-1.GM10",FileTypeEnum.INFER_FROM_ATTRIBUTES)

outline_info = outline_gerber.parse().get_info()

parsed_outline = mask_gerber.parse()

custom_command_buffer_solid: CommandBuffer2 = CommandBuffer2()
custom_command_buffer_hatch: CommandBuffer2 = CommandBuffer2()

def recur_is_bounded(command: ApertureDrawCommand2, bounding_info: BoundingBox) -> bool:
    '''
    Check if each command is with the bounding box of the outline.
    Recursively checks all lines within regions.
    '''
    if isinstance(command, Line2) or isinstance(command, CCArc2):
        if command.start_point.y.value<=outline_info.max_y_mm or command.end_point.y.value<=outline_info.max_y_mm:
            return True
    elif isinstance(command,Region2):
        return all(recur_is_bounded(cmd,bounding_info) for cmd in command.command_buffer)
    elif isinstance(command,Flash2):
        return command.flash_point.y.value<=outline_info.max_y_mm
    else:
        print(f"Command {command} not printed")
        return False

# FORM THE HATCH AND SOLID COMMAND BUFFERS
for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Line2) or isinstance(command,CCArc2):
            custom_command_buffer_hatch.add_command(command)

for command in parsed_outline._command_buffer:
    if recur_is_bounded(command=command,bounding_info=outline_info):
        if isinstance(command,Region2) or isinstance(command,Flash2):
            custom_command_buffer_solid.add_command(command)


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






from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# Instantiate a compiler, specifying the interface type and the speed at which the tool should move. pass_depth controls
# how far down the tool moves after every pass. Set it to 0 if your machine does not support Z axis movement.
gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)

curves = parse_file("test_solid.svg") # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file("drawing.gcode", passes=1)




import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import re

def animate_gcode(gcode_file, output_file=None, dpi=100, interval=10, figsize=(12, 3)):
    """
    Animates G-code file showing the tool path.
    
    Parameters:
    gcode_file (str): Path to the G-code file
    output_file (str, optional): Path to save the animation (mp4, gif). If None, displays animation
    dpi (int): Resolution of the output animation
    interval (int): Interval between frames in milliseconds
    figsize (tuple): Size of the figure in inches
    
    Returns:
    matplotlib.animation.Animation: Animation object
    """
    # Read G-code file
    with open(gcode_file, 'r') as file:
        lines = file.readlines()
    
    # Initialize variables
    path_segments = []
    current_segment = {'x': [], 'y': [], 'tool_state': None}
    
    current_x, current_y = 0, 0
    current_tool_state = 0
    
    # Parse G-code
    for line in lines:
        line = line.strip()
        
        # Check for tool on/off
        if line.startswith('M3'):
            # If we were tracking a segment and the tool state changes, save it and start a new one
            if current_segment['x'] and current_segment['tool_state'] != 1:
                path_segments.append(current_segment)
                current_segment = {'x': [current_x], 'y': [current_y], 'tool_state': 1}
            current_tool_state = 1
            if not current_segment['x']:
                current_segment['tool_state'] = 1
                
        elif line.startswith('M5'):
            # If we were tracking a segment and the tool state changes, save it and start a new one
            if current_segment['x'] and current_segment['tool_state'] != 0:
                path_segments.append(current_segment)
                current_segment = {'x': [current_x], 'y': [current_y], 'tool_state': 0}
            current_tool_state = 0
            if not current_segment['x']:
                current_segment['tool_state'] = 0
        
        # Check for movement
        elif line.startswith('G1'):
            # Extract X and Y coordinates if they exist
            x_match = re.search(r'X([-\d.]+)', line)
            y_match = re.search(r'Y([-\d.]+)', line)
            
            if x_match:
                current_x = float(x_match.group(1))
            if y_match:
                current_y = float(y_match.group(1))
            
            current_segment['x'].append(current_x)
            current_segment['y'].append(current_y)
    
    # Add the last segment if it has data
    if current_segment['x']:
        path_segments.append(current_segment)
    
    # Create a flattened list of all points for setting axis limits
    all_x = [x for segment in path_segments for x in segment['x']]
    all_y = [y for segment in path_segments for y in segment['y']]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set limits with padding
    if all_x and all_y:
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        
        # Add 10% padding
        x_range = max(0.1, x_max - x_min)
        y_range = max(0.1, y_max - y_min)
        
        ax.set_xlim(x_min - 0.1 * x_range, x_max + 0.1 * x_range)
        ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
    else:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    
    # Equal aspect ratio
    ax.set_aspect('equal')
    
    # Set labels and title
    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_title('G-code Animation')
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Create a list of line objects, one for each segment
    line_objects = []
    for _ in path_segments:
        if _['tool_state'] == 1:
            line, = ax.plot([], [], 'r-', linewidth=2)
        else:
            line, = ax.plot([], [], 'b-', linewidth=1, alpha=0.5)
        line_objects.append(line)
    
    # Current position indicator
    current_point, = ax.plot([], [], 'go', markersize=8)
    
    # Add legend manually
    ax.plot([], [], 'r-', linewidth=2, label='Tool On')
    ax.plot([], [], 'b-', linewidth=1, alpha=0.5, label='Tool Off')
    ax.plot([], [], 'go', markersize=8, label='Current Position')
    ax.legend(loc='upper right')
    
    # Determine the total number of points across all segments
    total_points = sum(len(segment['x']) for segment in path_segments)
    
    # Animation initialization function
    def init():
        for line in line_objects:
            line.set_data([], [])
        current_point.set_data([], [])
        return [*line_objects, current_point]

    # Animation update function
    def update(frame):
        # Determine which segment and point we're at
        points_seen = 0
        current_segment_idx = 0
        current_point_idx = 0
        
        for i, segment in enumerate(path_segments):
            if points_seen + len(segment['x']) > frame:
                current_segment_idx = i
                current_point_idx = frame - points_seen
                break
            points_seen += len(segment['x'])
        
        # Update all segments up to the current frame
        for i, (line, segment) in enumerate(zip(line_objects, path_segments)):
            if i < current_segment_idx:
                # Show the entire segment
                line.set_data(segment['x'], segment['y'])
            elif i == current_segment_idx:
                # Show segment up to current point
                line.set_data(
                    segment['x'][:current_point_idx + 1],
                    segment['y'][:current_point_idx + 1]
                )
            else:
                # Hide future segments
                line.set_data([], [])
        
        # Update current position marker
        if current_segment_idx < len(path_segments) and current_point_idx < len(path_segments[current_segment_idx]['x']):
            current_x = path_segments[current_segment_idx]['x'][current_point_idx]
            current_y = path_segments[current_segment_idx]['y'][current_point_idx]
            current_point.set_data([current_x], [current_y])
        
        # Update title to show progress
        ax.set_title(f'G-code Animation (Progress: {frame+1}/{total_points})')
        
        return [*line_objects, current_point]

    # Create animation
    anim = animation.FuncAnimation(
        fig, update, frames=total_points,
        init_func=init, blit=True, interval=interval
    )
    
    # Save or display the animation
    if output_file:
        if output_file.endswith('.mp4'):
            writer = animation.FFMpegWriter(fps=30, metadata=dict(artist='G-code Animator'))
            anim.save(output_file, writer=writer, dpi=dpi)
        elif output_file.endswith('.gif'):
            anim.save(output_file, writer='pillow', dpi=dpi)
        else:
            print("Unsupported output format. Use .mp4 or .gif")
    else:
        plt.show()
    
    return anim

animate_gcode("./drawing.gcode","./animation.gif")