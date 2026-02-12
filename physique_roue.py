import numpy as np

# ==================== DIMENSIONS ET MASSE ====================
RAYON = 0.33                    # Rayon du pneu en mètres (18 pouces)
MASSE_VEHICULE = 798.0          # Masse totale F1 + pilote en kg
MASSE_ROUE = 12.0               # Masse d'une roue en kg
NOMBRE_ROUES = 4
CHARGE_ROUE = MASSE_VEHICULE / NOMBRE_ROUES
INERTIE = 1.5 * MASSE_ROUE * RAYON**2

# ==================== MODÈLE DE PACEJKA ====================
# Magic Formula pour calculer la force de traction selon le glissement
PAC_B = 12.0                    # Rigidité du pneu
PAC_C = 1.65                    # Forme de la courbe
PAC_E = 0.97                    # Courbure au pic

# ==================== FRICTION ET TEMPÉRATURE ====================
MU_0 = 1.8                      # Coefficient de friction max (pneu neuf)
TEMP_IDEALE = 100.0             # Température optimale en °C
PLAGE_TEMP = 25.0               # Fenêtre de température efficace

# Capacités thermiques (J/°C)
CAPACITE_SURFACE = 3000.0       # Gomme externe
CAPACITE_CARCASSE = 4000.0      # Structure interne

# Transferts thermiques (W/°C)
TRANSFERT_INTERNE = 50.0        # Entre surface et carcasse
TRANSFERT_AIR = 60.0            # Refroidissement par l'air
TEMP_AMBIANTE = 30.0            # Température de l'air

# ==================== AÉRODYNAMIQUE ====================
COEFF_APPUI = 3.3               # Downforce en kg/m²
COEFF_TRAINEE = 0.9             # Drag en kg/m²
COEFF_ROULEMENT = 0.008         # Résistance au roulement

# ==================== MOTEUR ET FREINS ====================
COUPLE_MOTEUR_MAX = 4000.0      # Couple total disponible (4 roues) en N.m
COUPLE_FREIN_MAX = 2000.0       # Couple de freinage par roue en N.m
PUISSANCE_MAX = 1000000.0       # Limite de puissance en W (1000 kW)

# ==================== SEUILS ET LIMITES ====================
VITESSE_MIN_DYNAMIQUE = 0.5     # Seuil pour passer au modèle dynamique
VITESSE_MIN_MOUVEMENT = 0.02    # Seuil pour détecter l'arrêt complet
VITESSE_MIN_ROTATION = 0.01     # Seuil pour rotation de roue
VITESSE_MIN_REFERENCE = 0.5     # Vitesse de référence min pour kappa
SEUIL_USURE = 0.05              # Glissement min pour causer de l'usure
FACTEUR_USURE = 100.0           # Diviseur pour le calcul d'usure

# ==================== GRAVITÉ ====================
GRAVITE = 9.81                  # Accélération gravitationnelle en m/s²

# État initial: [vitesse_x, vitesse_angulaire, temp_surface, temp_carcasse, usure]
ETAT_INITIAL = [0.0, 0.0, 95.0, 85.0, 0.0]


def get_couple_moteur(pourcentage):
    """
    Convertit un pourcentage d'accélération en couple moteur.
    
    Args:
        pourcentage: Valeur entre 0 et 1 (0% à 100%)
    Returns:
        Couple en N.m
    """
    return pourcentage * COUPLE_MOTEUR_MAX


def get_couple_frein(pourcentage):
    """
    Convertit un pourcentage de freinage en couple de frein.
    
    Args:
        pourcentage: Valeur entre 0 et 1 (0% à 100%)
    Returns:
        Couple en N.m
    """
    return pourcentage * COUPLE_FREIN_MAX


def calculer_friction(temp_surface, usure):
    """
    Calcule le coefficient de friction selon la température et l'usure.
    La friction est maximale à la température idéale et diminue avec l'usure.
    
    Args:
        temp_surface: Température de la surface du pneu en °C
        usure: Niveau d'usure entre 0 (neuf) et 1 (mort)
    Returns:
        Coefficient de friction
    """
    degradation_usure = 1.0 - usure
    ecart_temp = (temp_surface - TEMP_IDEALE) ** 2
    degradation_temp = np.exp(-ecart_temp / (PLAGE_TEMP ** 2))
    
    return MU_0 * degradation_usure * degradation_temp


def calculer_glissement(vitesse_vehicule, vitesse_angulaire):
    """
    Calcule le taux de glissement (kappa) entre la roue et le sol.
    - kappa > 0 : La roue tourne plus vite que le sol (accélération)
    - kappa < 0 : La roue tourne moins vite que le sol (freinage)
    - kappa = 0 : Pas de glissement
    
    Args:
        vitesse_vehicule: Vitesse du véhicule en m/s
        vitesse_angulaire: Vitesse de rotation de la roue en rad/s
    Returns:
        Taux de glissement (kappa) entre -1 et 1
    """
    vitesse_roue = RAYON * vitesse_angulaire
    vitesse_reference = max(abs(vitesse_vehicule), abs(vitesse_roue), VITESSE_MIN_REFERENCE)
    
    kappa = (vitesse_roue - vitesse_vehicule) / vitesse_reference
    return max(-1.0, min(1.0, kappa))


def calculer_force_traction(kappa, charge_dynamique, friction):
    """
    Calcule la force de traction selon le modèle de Pacejka (Magic Formula).
    C'est une formule empirique qui reproduit bien le comportement des pneus.
    
    Args:
        kappa: Taux de glissement
        charge_dynamique: Charge sur la roue en kg
        friction: Coefficient de friction
    Returns:
        Force de traction en N
    """
    # D est le pic de force possible
    D = friction * charge_dynamique * GRAVITE
    
    # Magic Formula de Pacejka
    argument = PAC_B * kappa
    terme_atan = np.atan(argument)
    correction = PAC_E * (argument - terme_atan)
    
    force = D * np.sin(PAC_C * np.atan(argument - correction))
    
    return force


def regime_basse_vitesse(etat, moment_accel, moment_frein):
    """
    Modèle simplifié pour les très basses vitesses.
    Évite les divisions par zéro et gère l'arrêt complet.
    
    Args:
        etat: [vx, w, temp_ext, temp_int, usure]
        moment_accel: Couple moteur en N.m
        moment_frein: Couple de frein en N.m
    Returns:
        Liste des dérivées
    """
    vx, w, temp_ext, temp_int, usure = etat
    
    # Calcul de la friction disponible
    mu = calculer_friction(temp_ext, usure)
    force_friction_max = mu * CHARGE_ROUE * GRAVITE
    
    # Forces appliquées
    force_moteur = moment_accel / RAYON
    force_frein_total = (moment_frein / RAYON) * NOMBRE_ROUES
    force_resistance = COEFF_ROULEMENT * CHARGE_ROUE * GRAVITE * NOMBRE_ROUES
    
    # Bilan des forces (saturé par la friction max)
    force_nette = force_moteur - force_frein_total - force_resistance
    force_nette = max(-force_friction_max * NOMBRE_ROUES, 
                     min(force_friction_max * NOMBRE_ROUES, force_nette))
    
    # Accélérations (avec sécurités pour éviter les vitesses négatives)
    dvx = force_nette / MASSE_VEHICULE if (vx > VITESSE_MIN_MOUVEMENT or force_nette > 0) else 0
    dw = dvx / RAYON if vx > VITESSE_MIN_ROTATION else 0
    
    # Refroidissement simple (pas de friction = pas de chaleur générée)
    dt_ext = (-TRANSFERT_INTERNE * (temp_ext - temp_int) - 
              TRANSFERT_AIR * (temp_ext - TEMP_AMBIANTE)) / CAPACITE_SURFACE
    dt_int = (TRANSFERT_INTERNE * (temp_ext - temp_int) - 
              TRANSFERT_AIR * (temp_int - TEMP_AMBIANTE)) / CAPACITE_CARCASSE
    
    return [dvx, dw, dt_ext, dt_int, 0.0]


def regime_dynamique(etat, moment_accel, moment_frein):
    """
    Modèle complet avec Pacejka pour les vitesses normales.
    Prend en compte l'aérodynamique, la thermique et l'usure.
    
    Args:
        etat: [vx, w, temp_ext, temp_int, usure]
        moment_accel: Couple moteur en N.m
        moment_frein: Couple de frein en N.m
    Returns:
        Liste des dérivées
    """
    vx, w, temp_ext, temp_int, usure = etat
    
    # Charge dynamique avec downforce aérodynamique
    force_appui = COEFF_APPUI * vx**2
    charge_dynamique = CHARGE_ROUE + force_appui / (NOMBRE_ROUES * GRAVITE)
    
    # Calcul du glissement
    kappa = calculer_glissement(vx, w)
    
    # Force de traction via Pacejka
    mu = calculer_friction(temp_ext, usure)
    force_traction = calculer_force_traction(kappa, charge_dynamique, mu)
    
    # Limitation de puissance à haute vitesse (P = C * omega)
    moment_effectif = moment_accel
    if w > VITESSE_MIN_ROTATION:
        moment_effectif = min(moment_accel, PUISSANCE_MAX / w)
    
    moment_par_roue = moment_effectif / NOMBRE_ROUES
    
    # Forces résistantes
    force_trainee = COEFF_TRAINEE * vx**2
    force_roulement = COEFF_ROULEMENT * charge_dynamique * GRAVITE * NOMBRE_ROUES
    
    # Accélérations
    # Véhicule: somme des 4 roues - traînée - roulement
    dvx = (NOMBRE_ROUES * force_traction - force_trainee - force_roulement) / MASSE_VEHICULE
    # Roue: couple moteur - frein - réaction du sol
    dw = (moment_par_roue - moment_frein - force_traction * RAYON) / INERTIE
    
    # Sécurités anti-vitesses négatives
    if w <= VITESSE_MIN_ROTATION and dw < 0:
        dw = 0.0
    if vx <= VITESSE_MIN_ROTATION and dvx < 0:
        dvx = 0.0
    
    # Équations thermiques
    # La puissance dissipée par friction chauffe le pneu
    puissance_friction = abs(force_traction * (RAYON * w - vx))
    
    dt_ext = (puissance_friction - 
              TRANSFERT_INTERNE * (temp_ext - temp_int) - 
              TRANSFERT_AIR * (temp_ext - TEMP_AMBIANTE)) / CAPACITE_SURFACE
    dt_int = (TRANSFERT_INTERNE * (temp_ext - temp_int) - 
              TRANSFERT_AIR * (temp_int - TEMP_AMBIANTE)) / CAPACITE_CARCASSE
    
    # Usure (proportionnelle au glissement au carré)
    dusure = (abs(kappa) ** 2) / FACTEUR_USURE if abs(kappa) > SEUIL_USURE else 0.0
    
    return [dvx, dw, dt_ext, dt_int, abs(dusure)]


def derivee(t, X, moment_accel, moment_frein):
    """
    Fonction principale appelée par le solveur différentiel.
    Choisit le régime approprié selon la vitesse.
    
    Args:
        t: Temps (non utilisé mais requis par solve_ivp)
        X: État [vx, w, temp_ext, temp_int, usure]
        moment_accel: Couple moteur
        moment_frein: Couple de frein
    Returns:
        Liste des dérivées temporelles
    """
    vx, w = X[0], X[1]
    
    # Choix du régime selon la vitesse
    if vx < VITESSE_MIN_DYNAMIQUE and RAYON * w < VITESSE_MIN_DYNAMIQUE:
        return regime_basse_vitesse(X, moment_accel, moment_frein)
    else:
        return regime_dynamique(X, moment_accel, moment_frein)

