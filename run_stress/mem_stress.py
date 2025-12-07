#!/usr/bin/env python3
# mem_stress.py -- différents patterns de charge mémoire
import numpy as np
import time
import argparse
import multiprocessing as mp

def copy_test(size_mb, iterations):
    size = size_mb * 1024 * 1024 // 8  # éléments float64 (8 bytes)
    src = np.random.rand(size)
    dst = np.empty_like(src)
    t0 = time.perf_counter()
    for _ in range(iterations):
        dst[:] = src[:]   # grosse copie
    t1 = time.perf_counter()
    bytes_copied = size_mb * 1024 * 1024 * iterations
    gb_s = bytes_copied / (t1 - t0) / (1024**3)
    return gb_s, t1 - t0

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

def worker_copy(args):
    return copy_test(args.size_mb, args.iters)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["copy","rand"], default="copy")
    parser.add_argument("--size-mb", type=int, default=1024)
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--procs", type=int, default=1)
    args = parser.parse_args()

    if args.procs > 1:
        pool = mp.Pool(args.procs)
        results = pool.map(worker_copy, [args]*args.procs)
        print("Per-process GB/s:", results)
    else:
        if args.mode == "copy":
            bw, dur = copy_test(args.size_mb, args.iters)
            print(f"Copy {args.size_mb} MiB x {args.iters} => {bw:.2f} GB/s in {dur:.2f}s")
        else:
            ops_s = random_access_test(args.size_mb, args.duration)
            print(f"Random ops/s: {ops_s:.0f}")

