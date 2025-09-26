#!/usr/bin/env python3
import subprocess
import os

# Virtuelle Umgebung aktivieren (Pfad zu deinem venv)
venv_python = "/srv/poe_manager/venv/bin/python3"

# Poe.sh über bash ausführen, innerhalb der venv
subprocess.run(["/bin/bash", "/usr/local/bin/custom/poe.sh"], env={"PATH": f"/srv/poe_manager/venv/bin:" + os.environ["PATH"]})
