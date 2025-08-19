import subprocess
import playwright.__main__ as pw_main

try:
    # Check if Chromium is already installed
    subprocess.run(["playwright", "install", "chromium"], check=True)
except Exception as e:
    print("Error installing Playwright Chromium:", e)
