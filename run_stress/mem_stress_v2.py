#!/usr/bin/env python3
# mem_stress.py -- various memory load patterns
import numpy as np
import time
import argparse
import multiprocessing as mp

# -------------------------------------------------------------------
# 1. MEMORY COPY TEST (High-Speed Sequential)
# -------------------------------------------------------------------
def copy_test(size_mb, iterations):
    """
    Measures maximum memory bandwidth via sequential copy.

    Creates two large NumPy arrays and copies data from one to the other
    multiple times. This is a pure bandwidth test.

    Args:
        size_mb (int): Size of the source/destination array in MiB.
        iterations (int): Number of times the copy operation is repeated.

    Returns:
        tuple: (bandwidth_GB_s, total_time_s)
            bandwidth_GB_s (float): Data throughput in Gigabytes/second (GB/s).
            total_time_s (float): Total duration of the test in seconds.
    """
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
# 2. SIMPLE RANDOM ACCESS TEST
# -------------------------------------------------------------------
def random_access_test(size_mb, duration_s):
    """
    Measures simple random read access operations.

    Accesses random blocks of the array for a defined duration.
    This stresses the memory controller and caches .

    Args:
        size_mb (int): Size of the working array in MiB.
        duration_s (int): Test duration in seconds.

    Returns:
        float: Number of random access operations per second (ops/s).
    """
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
# 3. RANDOM v2 (random access + latency)
# -------------------------------------------------------------------
def random_access_test_v2(size_mb, duration_s, batch=50000):
    """
    Measures complex random read access operations and average latency.

    Identical to random_access_test, but also measures the time taken
    for each access batch to calculate latency per operation.

    Args:
        size_mb (int): Size of the working array in MiB.
        duration_s (int): Test duration in seconds.
        batch (int): Number of elements accessed per batch.

    Returns:
        tuple: (ops_per_second, average_latency_ns)
            ops_per_second (float): Number of random access operations per second (ops/s).
            average_latency_ns (float): Average latency per access operation in nanoseconds (ns).

    """
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
# 4. RANDOM WRITE (Aggressive Random Writes)
# -------------------------------------------------------------------
def random_write_test(size_mb, duration_s, batch=50000):
    """
    Measures the performance of aggressive random memory writes.

    Selects random indices in the array and writes new random data,
    stressing non-sequential write performance.

    Args:
        size_mb (int): Size of the working array in MiB.
        duration_s (int): Test duration in seconds.
        batch (int): Number of elements written per batch.

    Returns:
        float: Number of random write operations per second (ops/s).
    """
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
# 5. Worker for Parallel Mode (rand_multi)
# -------------------------------------------------------------------
def worker_random(args):
    """
    Wrapper function to execute random_access_test_v2 in multiprocessing mode.

    Args:
        args (Namespace): Object containing parser arguments (size_mb, duration, batch).

    Returns:
        tuple: The result of random_access_test_v2 (ops/s, latency ns).
    """
    return random_access_test_v2(args.size_mb, args.duration, args.batch)


def worker_copy(args):
    """
    Wrapper function to execute copy_test in multiprocessing mode.

    Args:
        args (Namespace): Object containing parser arguments (size_mb, iters).

    Returns:
        tuple: The result of copy_test (GB/s, total_time_s).
    """
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
