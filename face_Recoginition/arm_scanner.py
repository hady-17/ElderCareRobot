# arm_scanner.py
from movement.arm_move_ik import ArmIK
import time

arm = ArmIK()

# Define a series of scanning poses (theta3–theta6 in degrees)
scan_sequence = [
    {"theta3": 45, "theta4": 70, "theta5": 90, "theta6": -30},  # left
    {"theta3": 45, "theta4": 70, "theta5": 90, "theta6": 0},    # center
    {"theta3": 45, "theta4": 70, "theta5": 90, "theta6": 30},   # right
    {"theta3": 45, "theta4": 70, "theta5": 90, "theta6": 0}     # back to center
]

print("[SCAN] Starting arm-based scan sequence...")

for idx, angles in enumerate(scan_sequence):
    print(f"[SCAN] Moving to position {idx + 1} - {angles}")
    pwm = arm.transformAngelAdaptArm(
        angles["theta3"], angles["theta4"], angles["theta5"], angles["theta6"]
    )
    if pwm:
        arm.servosMove((pwm["servo3"], pwm["servo4"], pwm["servo5"], pwm["servo6"]), movetime=800)
    else:
        print(f"[WARNING] Angles out of range: {angles}")
    time.sleep(1.0)  # Pause for processing or detection

print("[SCAN] Scan complete.")
