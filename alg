#!/usr/bin/env python3
"""Run the original Algol 68S compiler; create a68.out in the caller's directory."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
if not (root / 'build/ready.json').is_file():
    subprocess.run([sys.executable, str(root / 'scripts/build.py')], check=True)
output = Path('a68.out')
output.unlink(missing_ok=True)
env = dict(os.environ, APOUT_ROOT='/', APOUT_UNIX_VERSION='V6')
result = subprocess.run([str(root / 'build/apout'),
                         str(root / 'build/original/alg68'), *sys.argv[1:]], env=env)
if result.returncode or not output.is_file():
    output.unlink(missing_ok=True)
    sys.exit(result.returncode if result.returncode > 0 else 1)
