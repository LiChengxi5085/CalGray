import subprocess
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.run(["python", "main.py"])
