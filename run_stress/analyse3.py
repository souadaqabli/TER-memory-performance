import matplotlib.pyplot as plt
import mem_stress2
import numpy as np
import os

def run_comparison():
    print("=== Analyse Min/Max : Benchmark en KiloOctets (Ko) ===")
    
    # LISTE EN KILO-OCTETS (Ko)
    # 32 Ko = L1 typique
    # 256 Ko - 1024 Ko = L2 typique
    # 1024 Ko (1 Mo) et plus = L3 puis RAM
    target_sizes_kb = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 65536]
    
    output_dir = "../results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data = {
        'Seq Read':   {'x': [], 'y': [], 'y_err_low': [], 'y_err_high': [], 'c': '#1f77b4'},
        'Rand Read':  {'x': [], 'y': [], 'y_err_low': [], 'y_err_high': [], 'c': '#ff7f0e'},
        'Rand Write': {'x': [], 'y': [], 'y_err_low': [], 'y_err_high': [], 'c': '#2ca02c'}
    }
    
    ITERS_SEQ = 100      # Un peu plus d'itérations pour les petites tailles
    DURATION_RAND = 10 # Rapide
    BATCH_SIZE = 50000 

    for size_kb in target_sizes_kb:
        # Affichage pour suivre
        if size_kb < 1024:
            print(f"--- Benchmarking : {size_kb} Ko ---")
        else:
            print(f"--- Benchmarking : {size_kb/1024:.1f} Mo ---")
        
        # --- CONVERSION : Kilo -> Bytes ---
        real_size_bytes = int(size_kb * 1024)
        
        # 1. SEQUENTIAL READ
        _, _, avg, mini, maxi = mem_stress2.sequential_read(real_size_bytes, ITERS_SEQ)
        
        data['Seq Read']['x'].append(size_kb) # Axe X en Ko
        data['Seq Read']['y'].append(avg)
        data['Seq Read']['y_err_low'].append(avg - mini) 
        data['Seq Read']['y_err_high'].append(maxi - avg)
        
        # 2. RANDOM READ
        _, avg, mini, maxi = mem_stress2.random_access_test(real_size_bytes, DURATION_RAND, batch=BATCH_SIZE)
        
        data['Rand Read']['x'].append(size_kb)
        data['Rand Read']['y'].append(avg)
        data['Rand Read']['y_err_low'].append(avg - mini)
        data['Rand Read']['y_err_high'].append(maxi - avg)

        # 3. RANDOM WRITE
        _, avg, mini, maxi = mem_stress2.random_write_test(real_size_bytes, DURATION_RAND, batch=BATCH_SIZE)
        
        data['Rand Write']['x'].append(size_kb)
        data['Rand Write']['y'].append(avg)
        data['Rand Write']['y_err_low'].append(avg - mini)
        data['Rand Write']['y_err_high'].append(maxi - avg)

    # --- Tracé ---
    print("\n[INFO] Génération du graphique...")
    plt.figure(figsize=(12, 8))
    
    for label, d in data.items():
        asymmetric_error = [d['y_err_low'], d['y_err_high']]
        
        plt.errorbar(
            d['x'], d['y'], 
            yerr=asymmetric_error, 
            label=label, color=d['c'], fmt='o', 
            linewidth=2, markersize=5, capsize=4, alpha=0.9, ecolor=d['c']
        )

    plt.xscale('log')
    plt.yscale('log')

    # On force l'affichage des ticks pour toutes nos tailles
    plt.xticks(
        ticks=target_sizes_kb, 
        labels=[str(s) for s in target_sizes_kb], 
        rotation=45
    )

    plt.xlabel('Taille du Bloc Mémoire (Ko)', fontsize=12, fontweight='bold')
    plt.ylabel('Latence moyenne par element(ns)', fontsize=12, fontweight='bold')
    plt.title('Performance Mémoire : L1 -> L2 -> RAM (Échelle Ko)', fontsize=14)

    plt.grid(True, which="major", ls="-", alpha=0.6)
    plt.legend(fontsize=11, loc='upper left')

    save_path = os.path.join(output_dir, "comparaison_min_max.png")
    plt.savefig(save_path)
    print(f"[OK] Graphique sauvegardé : {save_path}")
    plt.show()

if __name__ == "__main__":
    run_comparison()