#!/usr/bin/env python3
# stl.py - STAR LINK Keep-Alive Launcher

import sys

try:
    import starlink as sl
except ImportError as e:
    print(f"Error: Could not load module - {e}")
    print("Make sure starlink.so is in the same directory")
    sys.exit(1)

if __name__ == "__main__":
    sl.run()
