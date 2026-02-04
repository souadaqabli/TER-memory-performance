#!/usr/bin/env python3
# mem_stress.py -- various memory load patterns
import numpy as np
import time
import argparse
import multiprocessing as mp


#-------------------------------------------------
# 1. Sequential read  
#-------------------------------------------------
def sequential_read(size_bytes, iterations):
    """
    Benchmarks sequential memory read performance (linear access).
    """
    size = size_bytes // 8  # éléments float64 (8 bytes)
    src = np.ones(size, dtype=np.uint64)
    
    stat = np.zeros(3, dtype = np.uint64)
    stat[0] = np.iinfo(np.uint64).max
    
    t_start = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        _ = src.sum()  
        t1 = time.perf_counter_ns()
        
        lat = t1 - t0
        stat[0] = min(stat[0], lat)   # le minimum sur toutes les iterations
        stat[1] = max(stat[1], lat)   # le maximum sur toutes les iterations
        stat[2] = stat[2] + lat       # temps total passe a lire le tableau

    t_end = time.perf_counter()
    
    bytes_processed = size_bytes * iterations
    gb_s = bytes_processed / (t_end - t_start) / (1024**3)

    avg_lat_iter = (stat[2] / iterations)   # latence moyenne par iteration, le temps moyen qu'il faut pour lire une fois tout le bloc mémoire
    avg_lat_ns = (stat[2] / iterations) / len(src)          # latence moyenne par element 
    min_ns = stat[0] / len(src) # le temps pour acceder a un seul element dans la meilleure iteration
    max_ns = stat[1] / len(src)

    return gb_s, t_end - t_start , avg_lat_ns, min_ns, max_ns, avg_lat_iter, stat[0], stat[1] 


# -------------------------------------------------------------------
# 3-. SEQUENTIAL WRITE 
# -------------------------------------------------------------------
def sequential_write(size_bytes, iterations):
    """
    Benchmarks sequential memory write performance (linear fill).
    """
    size = size_bytes // 8 # float64
    arr = np.ones(size, dtype=np.uint64)
    
    stat = np.zeros(3, dtype = np.uint64)
    stat[0] = np.iinfo(np.uint64).max
    
    t_start = time.perf_counter()
    
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        arr[:] = 1 
        t1 = time.perf_counter_ns()
        
        lat = t1 - t0
        stat[0] = min(stat[0], lat)   # le minimum sur toutes les iterations
        stat[1] = max(stat[1], lat)   # le maximum sur toutes les iterations
        stat[2] = stat[2] + lat       # temps total passe a ecrire le tableau

    t_end = time.perf_counter()
    
    bytes_processed = size_bytes * iterations
    gb_s = bytes_processed / (t_end - t_start) / (1024**3)
    
    # Conversions
    avg_lat_iter = (stat[2] / iterations)   # latence moyenne par iteration, le temps moyen qu'il faut pour lire une fois tout le bloc mémoire
    avg_lat_ns = (stat[2] / iterations) / len(arr) # latence moyenne par element 
    min_ns = stat[0] / len(arr) # le temps pour ecrire un seul element dans la meilleure iteration
    max_ns = stat[1] / len(arr)
    
    return gb_s, t_end - t_start, avg_lat_ns, min_ns, max_ns, avg_lat_ns, min_ns, max_ns, avg_lat_iter, stat[0], stat[1] 


# -------------------------------------------------------------------
# 4. RANDOM read (random access + latency)
# -------------------------------------------------------------------
def random_access_test(size_bytes, duration_s, batch=50000):
    """
    Measures complex random read access operations and average latency.
    """
    np.random.seed(0)
    size = size_bytes // 8
    # Optimisation: on lit des 1 (ne change rien à la latence, mais init + rapide)
    arr = np.ones(size, dtype=np.uint64)
    
    stat = np.zeros(3, dtype=np.uint64)
    stat[0] = np.iinfo(np.uint64).max
    
    start = time.time()
    ops = 0
    count_batches = 0

    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, batch)
        
        t0 = time.perf_counter_ns()
        _ = arr[idx].sum()
        t1 = time.perf_counter_ns()
        
        lat = t1 - t0 # Temps pour traiter UN BATCH
        
        stat[0] = min(stat[0], lat)   # le minimum pour un batch
        stat[1] = max(stat[1], lat)   # le maximum pour un batch
        stat[2] = stat[2] + lat       # temps total cumulé
        
        ops += batch
        count_batches += 1

    ratio = size / batch
    # Conversions : Ici on divise par 'batch' car lat correspond à un lot de 'batch' accès
    avg_lat_iter = (stat[2] / count_batches) * ratio
    avg_lat_ns = (stat[2] / count_batches) / batch # latence moyenne par element
    min_ns = stat[0] / batch # le temps pour un element dans le meilleur batch
    max_ns = stat[1] / batch
    
    return ops / duration_s, avg_lat_ns, min_ns, max_ns, avg_lat_iter, stat[0] * ratio, stat[1] * ratio

# -------------------------------------------------------------------
# 5. RANDOM WRITE (Aggressive Random Writes)
# -------------------------------------------------------------------
def random_write_test(size_bytes, duration_s, batch=50000):
    """
    Measures the performance of aggressive random memory writes.
    """
    np.random.seed(0)
    size = size_bytes  // 8
    arr = np.ones(size, dtype=np.uint64)
    
    stat = np.zeros(3, dtype=np.uint64)
    stat[0] = np.iinfo(np.uint64).max
    
    start = time.time()
    ops = 0
    count_batches = 0

    while time.time() - start < duration_s:
        idx = np.random.randint(0, size, batch)
        #vals = np.random.rand(batch) # On écrit quand même du random pour le réalisme
        vals = np.random.randint(0, 100, batch, dtype=np.uint64)

        t0 = time.perf_counter_ns()
        arr[idx] = vals
        t1 = time.perf_counter_ns()
        
        lat = t1 - t0
        stat[0] = min(stat[0], lat)   # le minimum pour un batch
        stat[1] = max(stat[1], lat)   # le maximum pour un batch
        stat[2] = stat[2] + lat       # temps total cumulé
        
        ops += batch
        count_batches += 1

    # Conversions
    ratio = size / batch
    avg_lat_iter = (stat[2] / count_batches) * ratio
    avg_lat_ns = (stat[2] / count_batches) / batch # latence moyenne par element
    min_ns = stat[0] / batch # le temps pour un element dans le meilleur batch
    max_ns = stat[1] / batch
    
    return ops / duration_s , avg_lat_ns, min_ns, max_ns, avg_lat_iter, stat[0] * ratio, stat[1] * ratio
    

def stride_test(size_bytes, duration_s, stride_bytes=4096):
    # Test TLB (Saut variable)
    stride_idx = stride_bytes // 8
    if stride_idx < 1: stride_idx = 1
    
    size = size_bytes // 8
    arr = np.random.rand(size)
    
    start = time.time()
    ops = 0
    while time.time() - start < duration_s:
        # Lecture linéaire avec sauts
        _ = arr[::stride_idx].sum() 
        ops += (size // stride_idx)
    return ops / duration_s


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
if __name__ == "__main__":
    # GESTION UNIQUE DU SEED ICI (Global pour toutes les fonctions)
    np.random.seed(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",
                        choices=["sequential_read", "sequential_write", "random_read", "random_write", "stride"],
                        default="sequential_read")
    parser.add_argument("--size-bytes", type=int, default=1024*1024*1024) # 1 Go par défaut
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--procs", type=int, default=1)
    parser.add_argument("--batch", type=int, default=50000)
    parser.add_argument("--stride-bytes", type=int, default=4096)
    args = parser.parse_args()

    # NOTE : Mise à jour des prints pour afficher Avg (Moyenne), Min et Max.

    #if args.mode == "copy":
        #bw, dur, avg, mini, maxi = copy_test(args.size_bytes, args.iters)
        #print(f"Copy {args.size_bytes} MiB | BW: {bw:.2f} GB/s | Lat: {avg:.2f} ns (Min: {mini:.2f}, Max: {maxi:.2f})")

    if args.mode == "sequential_read":
        bw, dur, avg, mini, maxi = sequential_read(args.size_bytes, args.iters)
        print(f"Seq Read {args.size_bytes} MiB | BW: {bw:.2f} GB/s | Lat: {avg:.2f} ns (Min: {mini:.2f}, Max: {maxi:.2f})")

    if args.mode == "sequential_write":
        bw, dur, avg, mini, maxi = sequential_write(args.size_bytes, args.iters)
        print(f"Seq Write {args.size_bytes} MiB | BW: {bw:.2f} GB/s | Lat: {avg:.2f} ns (Min: {mini:.2f}, Max: {maxi:.2f})")

    elif args.mode == "random_read":
        ops_s, avg, mini, maxi = random_access_test(args.size_bytes, args.duration, args.batch)
        print(f"Rand Read {args.size_bytes} MiB | IOPS: {ops_s:.0f} | Lat: {avg:.2f} ns (Min: {mini:.2f}, Max: {maxi:.2f})")

    elif args.mode == "random_write":
        ops_s, avg, mini, maxi = random_write_test(args.size_bytes, args.duration, args.batch)
        print(f"Rand Write {args.size_bytes} MiB | IOPS: {ops_s:.0f} | Lat: {avg:.2f} ns (Min: {mini:.2f}, Max: {maxi:.2f})")
    
    elif args.mode == "stride":
        ops_s = stride_test(args.size_bytes, args.duration, args.stride_bytes)
        print(f"Stride ops/s: {ops_s:.0f}")