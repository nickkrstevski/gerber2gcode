import math

# Circle parameters
start_x = 50
start_y = 50
tool_head = 4
end_x = 210
end_y = 210

# Open the file in write mode
with open('infill.gcode', 'w') as file:
    # Write G-code headers
    file.write("G21         ; Set units to millimeters\n")
    file.write("G90         ; Use absolute positioning\n")
    # file.write("G17         ; Select XY plane\n")
    # file.write("G0 Z5       ; Lift to safe height\n")

    x = start_x
    y = start_y
    file.write(f"G1 X{start_x:.4f} Y{start_y:.4f} \n")
    file.write(f"M3\n")
    # file.write("G1 Z0 F300  ; Lower to cutting depth\n")

    # Generate points around the circle
    while y <= end_y:
        x = end_x
        file.write(f"G1 X{x:.4f} Y{y:.4f}\n")
        y = y + tool_head
        file.write(f"G1 X{x:.4f} Y{y:.4f}\n")
        x = start_x
        file.write(f"G1 X{x:.4f} Y{y:.4f}\n")
        y = y + tool_head
        file.write(f"G1 X{x:.4f} Y{y:.4f}\n")
    file.write(f"M5\n")

    # Write G-code footers
    # file.write("G0 Z5       ; Lift to safe height\n")
    # file.write("G0 X0 Y0    ; Return to origin\n")
    file.write("M30         ; End of program\n")
