#!/usr/bin/env python3
import subprocess
import pandas as pd

# ------------------ CONFIG ------------------
patterns = ["copy", "rand", "rand_v2", "rand_write"]
sizes_mb = [2, 8, 1024]
iters = 10
duration = 10
batch = 50000
# Phase 2 : Test Stride (TLB)
stride_list = [64, 256, 512, 1024, 2048, 4096, 8192]
fixed_size_for_stride = 512 

results = []

# ------------------ FUNCTION ------------------
def run_perf(mode, size_mb, stride_val=None):
    """Lance mem_stress.py avec perf et récupère les métriques"""
    cmd = [
        "perf", "stat",
        "-e", "cycles,instructions,L1-dcache-load-misses,LLC-load-misses,dTLB-load-misses",
        "-x", ";",
        "python3", "mem_stress.py",
        "--mode", mode,
        "--size-mb", str(size_mb),
        "--iters", str(iters),
        "--duration", str(duration),
        "--batch", str(batch)
        #"--stride-bytes", str(stride)
    ]

    if stride_val is not None:
        cmd.extend(["--stride-bytes", str(stride_val)])

    print(f"Running benchmark: {mode}, size={size_mb}MiB | Stride: {stride_val if stride_val else 'N/A'}")
    proc = subprocess.run(cmd, capture_output=True, text=True)

    stdout = proc.stdout
    stderr = proc.stderr

    # -------- Extraire débit / ops --------
    ops = None
    lat = None
    for line in stdout.splitlines():
        if "Copy" in line:
            ops = float(line.split("=>")[1].split("GB/s")[0].strip())
            if "latence" in line:
                lat = float(line.split("latence:")[1].split("ns")[0].strip())
        elif "Random" in line:
            ops = float(line.split(":")[1].split(",")[0].strip())
            if "latence" in line:
                lat = float(line.split("latence:")[1].split("ns")[0].strip())
        elif "Stride" in line: # Gère le nouveau mode stride
            try: ops = float(line.split("ops/s:")[1].strip())
            except: pass

    # -------- Extraire perf counters --------
    metrics = {
        "cycles": 0,
        "instructions": 0,
        "L1_misses": 0,
        "LLC_misses": 0,
        "TLB_misses": 0,
    }

    for line in stderr.splitlines():
        parts = line.strip().split(";")
        if len(parts) < 3:
            continue
        try:
            value = int(parts[0].replace(",", ""))
        except ValueError:
            continue

        counter = parts[2]
        if counter == "cycles":
            metrics["cycles"] = value
        elif counter == "instructions":
            metrics["instructions"] = value
        elif counter == "L1-dcache-load-misses":
            metrics["L1_misses"] = value
        elif counter == "LLC-load-misses":
            metrics["LLC_misses"] = value
        elif counter == "dTLB-load-misses":
            metrics["TLB_misses"] = value

    IPC = metrics["instructions"] / metrics["cycles"] if metrics["cycles"] > 0 else 0

    return {
        "pattern": mode,
        "ops_or_bw": ops,
        "lat_ns": lat,
        "cycles": metrics["cycles"],
        "instructions": metrics["instructions"],
        "IPC": IPC,
        "L1_misses": metrics["L1_misses"],
        "LLC_misses": metrics["LLC_misses"],
        "TLB_misses": metrics["TLB_misses"],
    }

# ------------------ RUN BENCHMARK ------------------
for size_mb in sizes_mb:
        for mode in patterns:
            results.append(run_perf(mode, size_mb))


# 2. Boucle Stride (Impact du saut TLB)
print("\n=== PHASE 2: IMPACT SAUT (STRIDE) ===")
for s in stride_list:
    # we launch this mode with a fixed size_mb and different stride values
    results.append(run_perf("stride", fixed_size_for_stride, stride_val=s))

# ------------------ SAVE RESULTS ------------------
df = pd.DataFrame(results)
df.to_csv("../results/memory_benchmark_results_full.csv", index=False)

print("\n=== BENCHMARK RESULTS ===")

pd.set_option('display.max_columns', None) 
pd.set_option('display.width', 200)         
print(df)
print("\n[OK] Résultats sauvegardés dans memory_benchmark_results_full.csv")
