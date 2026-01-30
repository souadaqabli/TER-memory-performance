import mem_stress  # On importe le fichier des tests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Configuration du test de stabilité
SIZE_MB = 1024       # On teste la RAM (grand tableau)
ITERATIONS = 5000      # Nombre d'itérations pour sequential read (pour voir la stabilité sur le long terme)
DURATION = 5         # Durée pour random (secondes)

data_points = []

print("=== Lancement de l'analyse de stabilité ===")

# 1. Test Copy
print(f"sequential_read({SIZE_MB} MB, {ITERATIONS} iters)...")
# On récupère la liste raw_latencies
_, _, _, raw_latencies = mem_stress.sequential_read(SIZE_MB, ITERATIONS)

for i, val in enumerate(raw_latencies):
    data_points.append({
        "Iteration": i,
        "Latence_ns": val,
        "Pattern": "sequential_read"
    })

# 2. Test Random Read
print(f"Test RANDOM READ ({SIZE_MB} MB)...")
# On récupère la liste raw_latencies
_, _, raw_latencies = mem_stress.random_access_test_v2(SIZE_MB, DURATION, batch=50000)

for i, val in enumerate(raw_latencies):
    data_points.append({
        "Iteration": i,
        "Latence_ns": val,
        "Pattern": "Random Read"
    })

# 3. Test Random Write
print(f"Test RANDOM WRITE ({SIZE_MB} MB)...")
_, _, raw_latencies = mem_stress.random_write_test(SIZE_MB, DURATION, batch=50000)

for i, val in enumerate(raw_latencies):
    data_points.append({
        "Iteration": i,
        "Latence_ns": val,
        "Pattern": "Random Write"
    })

# --- Visualisation ---
df = pd.DataFrame(data_points)

# Sauvegarde CSV pour trace
output_dir = "../results"
if not os.path.exists(output_dir): os.makedirs(output_dir)
df.to_csv(os.path.join(output_dir, "stability_trace.csv"), index=False)

# Création du graphique
plt.figure(figsize=(12, 6))
sns.set_theme(style="whitegrid")

# Lineplot pour voir l'évolution temporelle
sns.lineplot(data=df, x="Iteration", y="Latence_ns", hue="Pattern")

plt.title(f"Stabilité des accès mémoire (Taille: {SIZE_MB} MB)", fontsize=16)
plt.ylabel("Latence par batch/itération (ns)", fontsize=12)
plt.xlabel("Iterations", fontsize=12)
plt.yscale("log")
plt.grid(True, which="minor", ls="--", alpha=0.3)

save_path = os.path.join(output_dir, "graphique_stabilite.png")
plt.savefig(save_path)
print(f"\n[OK] Graphique généré : {save_path}")
plt.show()