#!/usr/bin/env python3
import subprocess
import time

# 1. Lancer le monitor en arrière-plan
monitor_proc = subprocess.Popen(
    ["python3", "monitor.py", "--out", "../results/run_monitor_copy.csv", "--interval", "1"]
)

# 2. Lancer le stress mémoire
stress_proc = subprocess.run(
    ["python3", "mem_stress.py", "--mode", "copy", "--size-mb", "1024", "--iters", "50"]
)

# 3. Arrêter le monitor quand le stress est fini
monitor_proc.terminate()
monitor_proc.wait()
