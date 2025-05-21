from spin_servos import Tool, Axis
import time

tool = Tool(sn="3423931353535120B1E0")
long_motor_sn = '209D3077484E'
long_motor = Axis(sn=long_motor_sn)
short_motor_sn = '205D305F484E'
short_motor = Axis(sn=short_motor_sn)

for i in range(10000):
    tool.tool_off()
    long_motor.set_target_pos_mm(50)
    time.sleep(1)
    tool.tool_on()
    long_motor.set_target_pos_mm(0)
    time.sleep(1)