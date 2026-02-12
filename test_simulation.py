import physique_roue as phys
from scipy.integrate import solve_ivp
import numpy as np

# Paramètres de simulation
temps_simulation = 10.0
intervalle_temps = (0, temps_simulation)
t_eval = np.linspace(0, temps_simulation, 1000)

# État initial
etat_initial = phys.ETAT_INITIAL

# Pourcentages des pédales (entre 0 et 1)
pourcentage_accel = 1.0
pourcentage_frein = 0.0


def wrapper_derivee(t, X):
    X_corrige = list(X)
    X_corrige[4] = max(0, min(1, abs(X_corrige[4])))
    
    accel = phys.get_couple_moteur(pourcentage_accel)
    frein = phys.get_couple_frein(pourcentage_frein)
    
    return phys.derivee(t, X_corrige, accel, frein)


# Résolution
solution = solve_ivp(
    wrapper_derivee,
    intervalle_temps,
    etat_initial,
    method='RK45',
    t_eval=t_eval,
    max_step=0.01
)

# Résultats
if solution.success:
    print("✓ Simulation réussie!")
    print(f"\nRésultats après {temps_simulation}s:")
    print(f"  Vitesse véhicule: {solution.y[0][-1]*3.6:.1f} km/h")
    print(f"  Vitesse angulaire: {solution.y[1][-1]:.2f} rad/s")
    print(f"  Température surface: {solution.y[2][-1]:.1f}°C")
    print(f"  Température carcasse: {solution.y[3][-1]:.1f}°C")
    print(f"  Usure pneu: {abs(solution.y[4][-1])*100:.2f}%")
else:
    print("✗ Échec de la simulation:", solution.message)
