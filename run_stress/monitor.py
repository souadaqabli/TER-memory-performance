#!/usr/bin/env python3
import psutil, time, csv, subprocess, shlex
from datetime import datetime

def sample_psutil():
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    # page faults
    pf = psutil.disk_io_counters(perdisk=False)  # ex. I/O, pas direct pagefaults
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ram_total": vm.total,
        "ram_used": vm.used,
        "ram_percent": vm.percent,
        "swap_used": swap.used,
        "swap_percent": swap.percent
    }

def perf_sample(duration=1, events=None):
    # exemple simple: "perf stat -I 1000 -e <events> sleep 1"
    if events is None:
        #events = ["cycles","instructions"]
        events=["cycles","instructions","cache-misses","cache-references","dTLB-load-misses"]

    cmd = f"perf stat -I 1000 -e {','.join(events)} sleep {duration}"
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    return proc.stderr

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="monitor_log.csv")
    parser.add_argument("--interval", type=int, default=1)
    args = parser.parse_args()

    with open(args.out, "w", newline="") as csvfile:
        writer = None
        try:
            while True:
                row = sample_psutil()
                perf = perf_sample(duration=1, events=["cycles","instructions"])
                row["perf_raw"] = perf.replace("\n","; ")
                if writer is None:
                    fieldnames = list(row.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                writer.writerow(row)
                csvfile.flush()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopped monitoring")
