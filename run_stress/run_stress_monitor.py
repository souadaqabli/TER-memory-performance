#!/usr/bin/env python3
import subprocess
import time

# Modes à tester
modes = ["copy", "rand", "rand_v2", "rand_write", "rand_multi"]

# Paramètres généraux
size_mb = 1024
iters = 50
duration = 10
procs = 2
batch = 50000

for mode in modes:
    print(f"\n=== Lancement du test {mode} ===")

    # Nom du CSV du monitor pour ce test
    monitor_csv = f"../results/run_monitor_{mode}.csv"

    # 1. Lancer le monitor en arrière-plan
    monitor_proc = subprocess.Popen(
        ["python3", "monitor.py",
         "--out", monitor_csv,
         "--interval", "1"]
    )

    # 2. Construire la commande mem_stress selon le mode
    cmd = ["python3", "mem_stress_v2.py", "--mode", mode, "--size-mb", str(size_mb)]

    if mode == "copy":
        cmd += ["--iters", str(iters)]
    elif mode in ["rand", "rand_v2", "rand_write"]:
        cmd += ["--duration", str(duration), "--batch", str(batch)]
    elif mode == "rand_multi":
        cmd += ["--duration", str(duration), "--batch", str(batch), "--procs", str(procs)]

    # Lancer le stress mémoire et attendre la fin
    subprocess.run(cmd)

    # 3. Arrêter le monitor
    monitor_proc.terminate()
    monitor_proc.wait()

    print(f"=== Fin du test {mode} ===\n")
