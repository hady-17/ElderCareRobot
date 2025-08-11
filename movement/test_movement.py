# test_movement.py

from movement.move import (
    move_forward,
    rotate_left_90,
    rotate_right_90,
    strafe_left,
    strafe_right,
    avoid_obstacles,
    stop_movement
)
import time

def main():
    print("[TEST] Starting movement test...")

    print("\n[STEP 1] Moving forward")
    move_forward(duration=2)

    print("\n[STEP 2] Rotating left 90°")
    rotate_left_90()
    time.sleep(1)

    print("\n[STEP 3] Rotating right 90°")
    rotate_right_90()
    time.sleep(1)

    print("\n[STEP 4] Strafing left")
    strafe_left(duration=2)

    print("\n[STEP 5] Strafing right")
    strafe_right(duration=2)

    print("\n[STEP 6] Obstacle avoidance check")
    avoid_obstacles()

    print("\n[FINAL] Stopping movement")
    stop_movement()

    print("\n✅ [DONE] Movement test complete.")

if __name__ == "__main__":
    main()
