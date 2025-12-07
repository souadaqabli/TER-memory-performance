#!/usr/bin/env python3
# mem_stress.py -- différents patterns de charge mémoire
import numpy as np
import time
import argparse
import multiprocessing as mp

# -------------------------------------------------------------------
# 1. TEST DE COPIE MÉMOIRE (séquentiel haut débit)
# -------------------------------------------------------------------
def copy_test(size_mb, iterations):
    size = size_mb * 1024 * 1024 // 8  # éléments float64 (8 bytes)
    src = np.random.rand(size)
    dst = np.empty_like(src)
    t0 = time.perf_counter()
    for _ in range(iterations):
        dst[:] = src[:]   
    t1 = time.perf_counter()
    bytes_copied = size_mb * 1024 * 1024 * iterations
    gb_s = bytes_copied / (t1 - t0) / (1024**3)
    return gb_s, t1 - t0

# -------------------------------------------------------------------
# 2. TEST RANDOM SIMPLE 
# -------------------------------------------------------------------
def random_access_test(size_mb, duration_s):
    size = size_mb * 1024 * 1024 // 8
    arr = np.random.rand(size)
    start = time.time()
    ops = 0
    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, 10000)
        _ = arr[idx].sum()
        ops += idx.size
    return ops / duration_s

# -------------------------------------------------------------------
# 3. RANDOM v2 (accès aléatoires + latence)
# -------------------------------------------------------------------
def random_access_test_v2(size_mb, duration_s, batch=50000):
    size = size_mb * 1024 * 1024 // 8
    arr = np.random.rand(size)
    start = time.time()
    ops = 0
    latencies = []

    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, batch)
        t0 = time.perf_counter_ns()
        _ = arr[idx].sum()
        t1 = time.perf_counter_ns()
        ops += batch
        latencies.append((t1 - t0) / batch)

    avg_latency_ns = sum(latencies) / len(latencies)
    return ops / duration_s, avg_latency_ns

# -------------------------------------------------------------------
# 4. RANDOM WRITE (écritures aléatoires, très agressif)
# -------------------------------------------------------------------
def random_write_test(size_mb, duration_s, batch=50000):
    size = size_mb * 1024 * 1024 // 8
    arr = np.random.rand(size)
    start = time.time()
    ops = 0

    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, batch)
        arr[idx] = np.random.rand(batch)
        ops += batch

    return ops / duration_s

# -------------------------------------------------------------------
# 5. Worker pour mode parallèle (rand_multi)
# -------------------------------------------------------------------
def worker_random(args):
    return random_access_test_v2(args.size_mb, args.duration, args.batch)

def worker_copy(args):
    return copy_test(args.size_mb, args.iters)

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",
                        choices=["copy", "rand", "rand_v2", "rand_write", "rand_multi"],
                        default="copy")
    parser.add_argument("--size-mb", type=int, default=1024)
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--procs", type=int, default=1)
    parser.add_argument("--batch", type=int, default=50000)
    args = parser.parse_args()

    # MULTIPROCESSING
    if args.mode == "rand_multi":
        pool = mp.Pool(args.procs)
        results = pool.map(worker_random, [args] * args.procs)
        print("\nRESULTATS PAR PROCESS (ops/s, latence ns) :")
        for r in results:
            print(r)
        exit(0)

    # MODES SIMPLES
    if args.mode == "copy":
        bw, dur = copy_test(args.size_mb, args.iters)
        print(f"Copy {args.size_mb} MiB x {args.iters} => {bw:.2f} GB/s in {dur:.2f}s")

    elif args.mode == "rand":
        ops_s = random_access_test(args.size_mb, args.duration)
        print(f"Random ops/s: {ops_s:.0f}")

    elif args.mode == "rand_v2":
        ops_s, lat = random_access_test_v2(args.size_mb, args.duration, args.batch)
        print(f"Random v2 ops/s: {ops_s:.0f}, latence: {lat:.1f} ns")

    elif args.mode == "rand_write":
        ops_s = random_write_test(args.size_mb, args.duration, args.batch)
        print(f"Random WRITE ops/s: {ops_s:.0f}")
