#!/usr/bin/env python3
# coding=utf-8

import time
from face_Recoginition.videoPersonDetection import search_for_elder_with_rover

def test_search_and_detect():
    print("[TEST] Initiating test of elder search and recognition system...")
    time.sleep(1)
    print("[INFO] Starting rover movement and arm-based scan...")
    time.sleep(1)
    print("[USER] Starting search for the elder. Please wait...")

    name = search_for_elder_with_rover()

    if name == "Unknown":
        print("[RESULT] Elder not recognized. Manual check required.")
    else:
        print(f"[RESULT] Elder recognized as: {name}")

if __name__ == "__main__":
    test_search_and_detect()
