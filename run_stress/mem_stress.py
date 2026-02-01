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
    latencies = []
    t_start = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        dst[:] = src[:]   
        t1 = time.perf_counter_ns()
        latencies.append((t1 - t0)/len(src))
    t_end = time.perf_counter()
    bytes_copied = size_mb * 1024 * 1024 * iterations
    gb_s = bytes_copied / (t_end - t_start) / (1024**3)
    avg_latency_ns = sum(latencies)/len(latencies)
    return gb_s, t_end - t_start , avg_latency_ns, latencies


#-------------------------------------------------
# 2. Sequential read  
#-------------------------------------------------

def sequential_read(size_mb, iterations):
    """
    Benchmarks sequential memory read performance (linear access).

    Allocates a contiguous array and reads it fully to measure maximum bandwidth 
    and hardware prefetcher efficiency.

    Args:
        size_mb (int): Size of the test array in MiB.
        iterations (int): Number of times to read the full array.

    Returns:
        tuple: (throughput_gb_s, total_time_s, avg_latency_ns, per_iteration_latencies)
    """
    size = size_mb * 1024 * 1024 // 8  # éléments float64 (8 bytes)
    src = np.random.rand(size)
    
    latencies = []
    t_start = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        _ = src.sum()  
        t1 = time.perf_counter_ns()
        latencies.append((t1 - t0)/len(src))
    t_end = time.perf_counter()
    bytes_processed = size_mb * 1024 * 1024 * iterations
    gb_s = bytes_processed / (t_end - t_start) / (1024**3)
    avg_latency_ns = sum(latencies)/len(latencies)
    return gb_s, t_end - t_start , avg_latency_ns, latencies



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
    return ops / duration_s, avg_latency_ns, latencies

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
    latencies = []

    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, batch)
        t0 = time.perf_counter_ns()
        arr[idx] = np.random.rand(batch)
        t1 = time.perf_counter_ns()
        ops += batch
        latencies.append((t1 - t0) / batch)

    avg_latency_ns = sum(latencies) / len(latencies)
    return ops / duration_s , avg_latency_ns, latencies
    


def stride_test(size_mb, duration_s, stride_bytes=4096):
    # Test TLB (Saut variable)
    # size_mb : taille du tableau global
    # stride_bytes : taille du saut en octets
    
    # On convertit les octets en indices float64 (8 bytes)
    stride_idx = stride_bytes // 8
    if stride_idx < 1: stride_idx = 1
    
    size = size_mb * 1024 * 1024 // 8
    arr = np.random.rand(size)
    
    start = time.time()
    ops = 0
    while time.time() - start < duration_s:
        # Lecture linéaire avec sauts
        _ = arr[::stride_idx].sum() 
        ops += (size // stride_idx)
    return ops / duration_s

# -------------------------------------------------------------------
# 5. Worker for Parallel Mode (rand_multi)
# -------------------------------------------------------------------
#def worker_random(args):
    #"""
    #Wrapper function to execute random_access_test_v2 in multiprocessing mode.

    #Args:
        #args (Namespace): Object containing parser arguments (size_mb, duration, batch).

    #Returns:
        #tuple: The result of random_access_test_v2 (ops/s, latency ns).
    #"""
    #return random_access_test_v2(args.size_mb, args.duration, args.batch)


#def worker_copy(args):
    #"""
    #Wrapper function to execute copy_test in multiprocessing mode.

    #Args:
        #args (Namespace): Object containing parser arguments (size_mb, iters).

    #Returns:
        #tuple: The result of copy_test (GB/s, total_time_s).
    #"""
    #return copy_test(args.size_mb, args.iters)

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",
                        choices=["copy", "sequential_read", "rand_v2", "rand_write", "stride"],
                        default="copy")
    parser.add_argument("--size-mb", type=int, default=1024)
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--procs", type=int, default=1)
    parser.add_argument("--batch", type=int, default=50000)
    parser.add_argument("--stride-bytes", type=int, default=4096)
    args = parser.parse_args()

    # MULTIPROCESSING
    #if args.mode == "rand_multi":
        #pool = mp.Pool(args.procs)
        #results = pool.map(worker_random, [args] * args.procs)
        #print("\nRESULTATS PAR PROCESS (ops/s, latence ns) :")
        #for r in results:
            #print(r)
        #exit(0)

    # MODES SIMPLES
    if args.mode == "copy":
        bw, dur, lat, _ = copy_test(args.size_mb, args.iters)
        print(f"Copy {args.size_mb} MiB x {args.iters} => {bw:.2f} GB/s in {dur:.2f}s, latence: {lat:.1f} ns")

    if args.mode == "sequential_read":
        bw, dur, lat , _= sequential_read(args.size_mb, args.iters)
        print(f"sequential_read {args.size_mb} MiB x {args.iters} => {bw:.2f} GB/s in {dur:.2f}s, latence: {lat:.1f} ns")

    #elif args.mode == "rand":
        #ops_s, lat, _ = random_access_test(args.size_mb, args.duration)
        #print(f"Random ops/s: {ops_s:.0f}, latence: {lat:.1f} ns")

    elif args.mode == "rand_v2":
        ops_s, lat, _ = random_access_test_v2(args.size_mb, args.duration, args.batch)
        print(f"Random v2 ops/s: {ops_s:.0f}, latence: {lat:.1f} ns")

    elif args.mode == "rand_write":
        ops_s, lat, _ = random_write_test(args.size_mb, args.duration, args.batch)
        print(f"Random WRITE ops/s: {ops_s:.0f} , latence: {lat:.1f} ns")
    
    # AJOUT DU BLOC STRIDE
    elif args.mode == "stride":
        ops_s = stride_test(args.size_mb, args.duration, args.stride_bytes)
        print(f"Stride ops/s: {ops_s:.0f}")