#!/bin/bash
# Script pour mesurer les performances mémoire avec perf

PATTERNS=("copy" "rand" "rand_v2" "rand_write")
SIZE_MB=1024
ITERS=10
DURATION=10
BATCH=50000

for MODE in "${PATTERNS[@]}"; do
    echo "======================="
    echo "Mode: $MODE"
    echo "======================="
    
    # Fichier de sortie
    OUTFILE="perf_${MODE}.txt"

    # Lancer perf stat
    perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses,stalled-cycles-backend \
    python3 mem_stress.py --mode $MODE --size-mb $SIZE_MB --iters $ITERS --duration $DURATION --batch $BATCH 2>&1 | tee $OUTFILE
done
