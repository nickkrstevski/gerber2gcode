import FlatCAM

App = FlatCAM.App()

# Load Gerber as a mask/boundary
gerber_obj = App.open_gerber("your_mask.gbr")

# Create a CNC job object from the gerber
cncjob_obj = App.make_cncjob(gerber_obj, 
                             tool_dia=0.2,  # Tool diameter
                             cut_z=-1.0,    # Cutting depth
                             travel_z=2.0,  # Safe travel height
                             feedrate=800,  # Feedrate for cutting
                             multidepth=True, # Use multiple depth passes
                             depthperpass=0.5) # Depth per pass

# Generate area clear operation with zigzag pattern
App.generate_area_clear(cncjob_obj, 
                        tooldia=0.2, 
                        stepover=0.5, # Controls infill density
                        algo="zigzag") # infill pattern - options include: zigzag, lines, spiral

# Export the g-code
App.export_gcode(cncjob_obj, "output.gcode")