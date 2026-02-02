import matplotlib.pyplot as plt
import mem_stress 
import numpy as np  
import os


def run_comparison():
    print("=== Analyse Complète : 4 Modes x  Tailles ===")
    
    # Vos tailles cibles
    target_sizes = [2, 8, 64, 128, 512, 1024, 2048]
    output_dir = "../results"

    # Structure : 'mode': {'mean': [], 'std': []}
    data = {
        'Seq Read':   {'x': [], 'y': [], 'yerr': [], 'c': '#1f77b4', 'fmt': 'o'}, # Bleu
        'Seq Write':  {'x': [], 'y': [], 'yerr': [], 'c': '#d62728', 'fmt': 'o'}, # Rouge
        'Rand Read':  {'x': [], 'y': [], 'yerr': [], 'c': '#ff7f0e', 'fmt': 'o'}, # Orange
        'Rand Write': {'x': [], 'y': [], 'yerr': [], 'c': '#2ca02c', 'fmt': 'o'}  # Vert
    }
    
    # Paramètres de test
    ITERS_SEQ = 50       
    DURATION_RAND = 5   
    BATCH_SIZE = 50000   # Taille standard du batch

    for size_mb in target_sizes:
        print(f"--- Test en cours pour taille : {size_mb} MB ---")
        
        # 1. SEQUENTIAL READ (Bleu)
        # Rappel return: gb_s, time, AVG_LAT, list_lat
        _, _, lat, lst = mem_stress.sequential_read(size_mb, ITERS_SEQ)
        data['Seq Read']['x'].append(size_mb)
        data['Seq Read']['y'].append(lat)
        data['Seq Read']['yerr'].append(np.std(lst))
        
        # 2. SEQUENTIAL WRITE ()
        # Rappel return: gb_s, time, AVG_LAT, list_lat
        _, _, lat, lst = mem_stress.sequential_write(size_mb, ITERS_SEQ)
        data['Seq Write']['x'].append(size_mb)
        data['Seq Write']['y'].append(lat)
        data['Seq Write']['yerr'].append(np.std(lst))


        # 2. RANDOM READ (Orange)
        # Rappel return: ops, AVG_LAT, list_lat

        _, lat, lst = mem_stress.random_access_test(size_mb, DURATION_RAND, batch=BATCH_SIZE)
        data['Rand Read']['x'].append(size_mb)
        data['Rand Read']['y'].append(lat)
        data['Rand Read']['yerr'].append(np.std(lst))

        # 3. RANDOM WRITE (Vert)
        # Rappel return: ops, AVG_LAT, list_lat
        _, lat, lst = mem_stress.random_write_test(size_mb, DURATION_RAND, batch=BATCH_SIZE)
        data['Rand Write']['x'].append(size_mb)
        data['Rand Write']['y'].append(lat)
        data['Rand Write']['yerr'].append(np.std(lst))

    # --- Tracé du Graphique ---
    plt.figure(figsize=(10, 7))
    
    for label, d in data.items():
        # plt.errorbar est LA fonction pour les errors bars
        # x, y : coordonnées
        # yerr : taille des barres d'erreur (Standard Deviation)
        # capsize : petite barre horizontale au bout de l'erreur
        plt.errorbar(
            d['x'], d['y'], yerr=d['yerr'], 
            label=label, color=d['c'], fmt=d['fmt'], 
            linewidth=2, markersize=6, capsize=4, alpha=0.9
        )

    # --- Mise en forme ---
    plt.xscale('log')
    #plt.yscale('log')

    plt.xticks(
        ticks=target_sizes, 
        labels=[str(s) for s in target_sizes], 
    )

    # Axes et Titres
    plt.xlabel('Taille du Bloc Mémoire (Mo)', fontsize=12, fontweight='bold')
    plt.ylabel('Latence par accès (ns)', fontsize=12, fontweight='bold')
    plt.title('Hiérarchie Mémoire : Évolution de la Latence & Stabilité', fontsize=14)

    # Grille fine pour lecture log
    plt.grid(True, which="major", ls="-", alpha=0.6)
    plt.grid(True, which="minor", ls=":", alpha=0.3)

    # Légende
    plt.legend(fontsize=11, loc='upper left', frameon=True, shadow=True)


    save_path = os.path.join(output_dir, "comparaison_std2.png")
    plt.savefig(save_path)
    print(f"\n[OK] Graphique généré : {save_path}")
    plt.show()

if __name__ == "__main__":
    run_comparison()