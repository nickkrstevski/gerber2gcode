#################################################################################################
#                                       🛠 G-CODE CHEAT SHEET 🛠                                #
#################################################################################################

# 🚀 MOVEMENT COMMANDS:
# | Command       | Description                           | Example             |
# |--------------|-------------------------------------|---------------------|
# | G0 X# Y# Z#  | Rapid move (no cutting)            | G0 X10 Y20          |
# | G1 X# Y# Z# F# | Linear move (cutting)           | G1 X50 Y30 F1000    |
# | G2 X# Y# I# J# | Clockwise arc                    | G2 X10 Y10 I5 J0    |
# | G3 X# Y# I# J# | Counterclockwise arc              | G3 X10 Y10 I-5 J0   |

# 🔄 MACHINE CONTROL:
# | Command  | Description                     | Example  |
# |---------|---------------------------------|----------|
# | G4 P#   | Dwell (pause for P seconds)    | G4 P2    |
# | G17     | Select XY plane                | G17      |
# | G18     | Select XZ plane                | G18      |
# | G19     | Select YZ plane                | G19      |
# | G20     | Set units to inches            | G20      |
# | G21     | Set units to millimeters       | G21      |
# | G28     | Move to home position          | G28      |

# 🔧 TOOL & SPINDLE CONTROL:
# | Command | Description                      | Example       |
# |---------|----------------------------------|--------------|
# | M3 S#   | Spindle on (clockwise)          | M3 S1000     |
# | M4 S#   | Spindle on (counterclockwise)   | M4 S800      |
# | M5      | Spindle stop                    | M5           |
# | M6 T#   | Tool change                      | M6 T2        |

# 💧 COOLANT CONTROL:
# | Command | Description         | Example  |
# |---------|---------------------|----------|
# | M7      | Mist coolant on     | M7       |
# | M8      | Flood coolant on    | M8       |
# | M9      | Coolant off         | M9       |

# 🛑 PROGRAM CONTROL:
# | Command | Description                   | Example |
# |---------|-------------------------------|---------|
# | M0      | Program stop (wait for input) | M0      |
# | M1      | Optional stop                 | M1      |
# | M2      | Program end                   | M2      |
# | M30     | Program end & rewind          | M30     |

# 📏 WORK OFFSETS & POSITIONING:
# | Command | Description                  | Example |
# |---------|------------------------------|---------|
# | G54     | Work offset #1               | G54     |
# | G55     | Work offset #2               | G55     |
# | G90     | Absolute positioning         | G90     |
# | G91     | Relative positioning         | G91     |

# 🌀 LOOPS & SUBROUTINES:
# | Command  | Description       | Example       |
# |----------|------------------|--------------|
# | M

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import re
import math
import time
from typing import List, Dict, Tuple, Optional, Any
import xml.etree.ElementTree as ET
from html import escape
import base64
from shapely import Polygon

class GCode:
    def __init__(self, filename="output.gcode"):
        """
        Initialize a GCode object with a file to store G-code commands.
        """
        self.filename = filename
        self.commands = []
        self._add_line("G21")  # Set units to millimeters
        self._add_line("G90")  # Absolute positioning
        self._add_line("G0 X0 Y0 Z10")  # Move to start position
        self.location = (0,0)

    def _add_line(self, command):
        """
        Add a single G-code command to the list.
        """
        self.commands.append(command)

    def set_location(self, x, y, feed = 800):
        x = round(x,3)
        y = round(y,3)
        self.location = (x,y)
        self._add_line(f"G1 X{x} Y{y} F{feed}")

    def add_array(self, array, feed = 800):
        if array:
            for idx, toolpath in enumerate(array): #individual contour
                # Move with tool off
                self.tool_on(False)
                self.set_location(x=toolpath[0][0],y=toolpath[0][1])
                self.tool_on(True)
                for step in toolpath:
                    self.set_location(x=step[0],y=step[1])

    def tool_on(self,tool_on: bool):
        self._add_line(f"{'M3 S1' if tool_on else 'M5'}")

    def save(self):
        """
        Save the G-code commands to the file.
        """
        with open(self.filename, "w") as f:
            f.write("\n".join(self.commands))

    def preview(self):
        """
        Print the G-code commands to preview them before saving.
        """
        print("\n".join(self.commands))

    def animate_gcode(self, output_file=None, dpi=100, interval=1, figsize=(5, 4),polygons:List[Polygon]=None):
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
        with open(self.filename, 'r') as file:
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
                if current_segment['x'] and current_segment['tool_state'] != 1:
                    path_segments.append(current_segment)
                    current_segment = {'x': [current_x], 'y': [current_y], 'tool_state': 1}
                current_tool_state = 1
                if not current_segment['x']:
                    current_segment['tool_state'] = 1
                    
            elif line.startswith('M5'):
                if current_segment['x'] and current_segment['tool_state'] != 0:
                    path_segments.append(current_segment)
                    current_segment = {'x': [current_x], 'y': [current_y], 'tool_state': 0}
                current_tool_state = 0
                if not current_segment['x']:
                    current_segment['tool_state'] = 0
            
            # Check for movement
            elif line.startswith('G1'):
                x_match = re.search(r'X([-\d.]+)', line)
                y_match = re.search(r'Y([-\d.]+)', line)
                
                if x_match:
                    current_x = float(x_match.group(1))
                if y_match:
                    current_y = float(y_match.group(1))
                
                current_segment['x'].append(current_x)
                current_segment['y'].append(current_y)
        
        if current_segment['x']:
            path_segments.append(current_segment)
        
        all_x = [x for segment in path_segments for x in segment['x']]
        all_y = [y for segment in path_segments for y in segment['y']]
        
        fig, ax = plt.subplots(figsize=figsize)

        if all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            
            x_range = max(0.1, x_max - x_min)
            y_range = max(0.1, y_max - y_min)
            
            ax.set_xlim(x_min - 0.1 * x_range, x_max + 0.1 * x_range)
            ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
        else:
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        
        ax.set_aspect('equal')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title('G-code Animation')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        line_objects = []
        for _ in path_segments:
            if _['tool_state'] == 1:
                line, = ax.plot([], [], 'r-', linewidth=2)
            else:
                line, = ax.plot([], [], 'b-', linewidth=1, alpha=0.5)
            line_objects.append(line)
        
        current_point, = ax.plot([], [], 'go', markersize=8)
        
        ax.plot([], [], 'r-', linewidth=2, label='Tool On')
        ax.plot([], [], 'b-', linewidth=1, alpha=0.5, label='Tool Off')
        ax.plot([], [], 'go', markersize=6, label='Current Position')
        ax.legend(loc="upper right")#, bbox_to_anchor=(1, 1))
        
        total_points = sum(len(segment['x']) for segment in path_segments)
        
        for polygon in polygons:
            x, y = polygon.exterior.xy
            ax.fill(x,y, color='green', alpha=0.3)

        def init():
            for line in line_objects:
                line.set_data([], [])
            current_point.set_data([], [])
            return [*line_objects, current_point]

        def update(frame):
            points_seen = 0
            current_segment_idx = 0
            current_point_idx = 0
            
            for i, segment in enumerate(path_segments):
                if points_seen + len(segment['x']) > frame:
                    current_segment_idx = i
                    current_point_idx = frame - points_seen
                    break
                points_seen += len(segment['x'])
            
            for i, (line, segment) in enumerate(zip(line_objects, path_segments)):
                if i < current_segment_idx:
                    line.set_data(segment['x'], segment['y'])
                elif i == current_segment_idx:
                    line.set_data(
                        segment['x'][:current_point_idx + 1],
                        segment['y'][:current_point_idx + 1]
                    )
                else:
                    line.set_data([], [])
            
            if current_segment_idx < len(path_segments) and current_point_idx < len(path_segments[current_segment_idx]['x']):
                current_x = path_segments[current_segment_idx]['x'][current_point_idx]
                current_y = path_segments[current_segment_idx]['y'][current_point_idx]
                current_point.set_data([current_x], [current_y])
            
            ax.set_title(f'G-code Animation (Progress: {frame+1}/{total_points})')
            
            return [*line_objects, current_point]
        
        anim = animation.FuncAnimation(
            fig, update, frames=total_points,
            init_func=init, blit=True, interval=interval
        )

        if output_file:
            if output_file.endswith('.mp4'):
                writer = animation.FFMpegWriter(fps=60, metadata=dict(artist='G-code Animator'))
                anim.save(output_file, writer=writer, dpi=dpi)
            elif output_file.endswith('.gif'):
                anim.save(output_file,fps=30, writer='pillow', dpi=dpi)
            else:
                print("Unsupported output format. Use .mp4 or .gif")
        else:
            plt.show()

        return anim

    def plot_gcode_and_polygons(self, shapely_polygons=None):
        """
        Plots the toolpath from a list of G-code commands and overlays Shapely polygons,
        ensuring equal scaling on both axes, with different colors for tool on/off states.

        Parameters:
            gcode_commands (list of str): List of G-code commands as strings.
            shapely_polygons (list of shapely.geometry.Polygon or shapely.geometry.MultiPolygon, optional):
                List of Shapely polygon objects to overlay on the plot.
                Defaults to None.
        """
        x, y, colors = [], [], []
        tool_on = False
        current_x, current_y = 0, 0

        # Define G-code command prefixes for movement and tool control
        movement_commands = ('G0', 'G1')
        tool_on_commands = ('M3', 'M4')
        tool_off_commands = ('M5',)

        for command in self.commands:
            parts = command.strip().split()
            if not parts:
                continue

            cmd = parts[0]
            params = {p[0]: float(p[1:]) for p in parts[1:]}

            # Update tool state
            if cmd in tool_on_commands:
                tool_on = True
            elif cmd in tool_off_commands:
                tool_on = False

            # Process movement commands
            if cmd in movement_commands:
                new_x = params.get('X', current_x)
                new_y = params.get('Y', current_y)
                if new_x != current_x or new_y != current_y:
                    x.append([current_x, new_x])
                    y.append([current_y, new_y])
                    colors.append('red' if tool_on else 'blue')
                current_x, current_y = new_x, new_y

        # Plotting
        fig, ax = plt.subplots()
        for i in range(len(x)):
            ax.plot(x[i], y[i], color=colors[i])

        # Overlay Shapely polygons if provided
        if shapely_polygons:
            for polygon in shapely_polygons:
                if isinstance(polygon, Polygon):
                    x, y = polygon.exterior.xy
                    ax.fill(x, y, alpha=0.5, color='gray')

        # Set equal scaling for both axes
        ax.set_aspect('equal', adjustable='box')

        # Set labels and title
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title('G-code Toolpath and Shapely Polygons')

        # Display the plot
        plt.show()


if __name__ == "__main__":
    # Example usage:
    gcode = GCode()
    gcode._add_line("M3 S1")      # Start spindle at 1000 RPM
    gcode._add_line("G1 X50 Y50 F800")  # Linear move to (50,50) at 800 mm/min
    gcode._add_line("G1 X100 Y100 F800")  # Linear move to (50,50) at 800 mm/min
    gcode._add_line("M5")            # Stop spindle
    gcode._add_line("G1 X50 Y100 F800")  # Linear move to (50,50) at 800 mm/min
    gcode._add_line("G1 X50 Y50 F800")  # Linear move to (50,50) at 800 mm/min
    gcode._add_line("G28")           # Return to home
    gcode._add_line("M30")           # End program

    gcode.preview()  # Show the G-code
    gcode.save()     # Save to file

    GCode.animate_gcode("./output.gcode","./animation.gif")