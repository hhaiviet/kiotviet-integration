#!/usr/bin/env python3
"""Run auto sync on Pi with visible output"""

import subprocess
import sys
import os

# Change to the correct directory
project_dir = r"c:\Users\PeterHoang\OneDrive - Li & Fung\Documents\kiotviet 248minimart project\kiotviet-integration"
os.chdir(project_dir)

print(f"Working directory: {os.getcwd()}\n")

# Run the auto_sync_on_pi.py script
result = subprocess.run([sys.executable, "auto_sync_on_pi.py"], 
                       capture_output=False, 
                       text=True)

sys.exit(result.returncode)
