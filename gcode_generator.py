import math

# Circle parameters
center_x = 200
center_y = 200
radius = 100
segments = 500  # Number of linear segments

# Open the file in write mode
with open('circle.gcode', 'w') as file:
    # Write G-code headers
    file.write("G21         ; Set units to millimeters\n")
    file.write("G90         ; Use absolute positioning\n")
    # file.write("G17         ; Select XY plane\n")
    # file.write("G0 Z5       ; Lift to safe height\n")

    # Calculate starting point
    start_x = center_x + radius * math.cos(0)
    start_y = center_y + radius * math.sin(0)
    # file.write(f"G0 X{start_x:.4f} Y{start_y:.4f} ; Move to starting point\n")
    # file.write("G1 Z0 F300  ; Lower to cutting depth\n")

    # Generate points around the circle
    for i in range(1, segments + 1):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        file.write(f"G1 X{x:.4f} Y{y:.4f} F500\n")

    # Write G-code footers
    # file.write("G0 Z5       ; Lift to safe height\n")
    # file.write("G0 X0 Y0    ; Return to origin\n")
    file.write("M30         ; End of program\n")
