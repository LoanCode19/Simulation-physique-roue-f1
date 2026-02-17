# Contenu complet du README
**Simulateur physique temps réel de la dynamique longitudinale et de la thermodynamique d'un pneumatique de Formule 1.**

Ce projet modélise le comportement non-linéaire d'une roue de F1 soumise à des contraintes extrêmes. Il couple un modèle de friction empirique (**Magic Formula**) à un système thermodynamique multicouche, le tout résolu numériquement via des équations différentielles.

---

## Fonctionnalités Principales

### 1. Modélisation Physique Avancée
* **Modèle de Pacejka (Magic Formula) :** Implémentation complète des coefficients $B, C, D, E$ calibrés pour la F1 afin de simuler la courbe de friction non-linéaire et la saturation de l'adhérence.
* **Résolution Numérique :** Utilisation de l'intégrateur **Runge-Kutta (RK45)** via `scipy.integrate` pour une précision temporelle élevée.
* **Aérodynamique :** Prise en compte de la charge verticale dynamique (*Downforce*) et de la traînée (*Drag*) quadratique.

### 2. Thermodynamique & Usure
* **Modèle à deux masses :** Simulation distincte de la température de **Surface** (gomme) et de la **Carcasse** (structure interne).
* **Flux Thermiques :** Calcul en temps réel des échanges :
    * *Friction → Surface* (Génération de chaleur par puissance de glissement)
    * *Surface ↔ Carcasse* (Conduction interne)
    * *Surface ↔ Air* (Convection/Refroidissement)
* **Dégradation :** L'usure du pneu impacte dynamiquement le coefficient de friction disponible.

### 3. Visualisation Interactive (Pygame)
* **Rendu dynamique :** Le pneu change de couleur selon sa température (Heatmap) et son glissement.
* **Système de particules :** Génération procédurale de fumée lors des blocages ou patinages excessifs.
* **Télémétrie :** Affichage en direct des courbes de vitesse, du glissement ($\kappa$) et des températures.

---

## Installation et Utilisation

### Prérequis
Ce projet nécessite **Python 3** et les bibliothèques suivantes :

```bash
pip install numpy scipy pygame
```

## Lancement

### Démarrer l'interface de simulation visuelle

```bash
python simulation_visuelle.py
```

### Lancer un test rapide en console (sans interface graphique)

```bash
python test_simulation.py
```

## Contrôles de la simulation

L'interface permet de contrôler l'accélérateur et le frein via des sliders  
(pour définir un seuil de puissance) et des touches clavier.

| Action    | Touche clavier | Interface graphique |
| :-------- | :------------- | :------------------ |
| Accélérer | W ou ↑         | Bouton **ACCÉLÉRER**|
| Freiner   | S ou ↓         | Bouton **FREINER** |
| Puissance | —              | Sliders...          |

## 🧮 Architecture technique

Le cœur de la simulation repose sur la résolution du système différentiel  
dans `physique_roue.py`.

Le vecteur d'état X évolue à chaque pas de temps selon les lois de la dynamique :

$$F_x = D sin(C arctan(B κ - E(B κ - arctan(B κ))))$$

Le système d'état est défini par :

```python
X = [
    vitesse_lineaire,    # Vitesse du véhicule (m/s)
    vitesse_angulaire,   # Rotation de la roue (rad/s)
    temp_surface,        # Température gomme externe (°C)
    temp_carcasse,       # Température structure interne (°C)
    usure_pneu           # État d'usure (0.0 à 1.0)
]
```

## Structure des fichiers

- physique_roue.py :
  Moteur physique.
  Contient les constantes F1, les formules de Pacejka
  et les équations différentielles (derivee).

- simulation_visuelle.py :
  Interface Pygame.
  Gère la boucle de rendu, les inputs utilisateur
  et le système de particules.

- test_simulation.py :
  Script headless.
  Permet de vérifier les calculs et la stabilité numérique
  sans lancer l'interface graphique.

Projet réalisé dans le cadre d'une étude personnelle
sur la simulation numérique appliquée au sport automobile.
