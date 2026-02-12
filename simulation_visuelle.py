import pygame
import sys
import math
import random
import physique_roue as phys
from scipy.integrate import solve_ivp

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ========== CONFIG ==========
LARGEUR = 800
HAUTEUR = 620
FPS = 30

screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Simulation Roue F1")

# ========== COULEURS ==========
BLANC      = (255, 255, 255)
NOIR       = (0, 0, 0)
GRIS       = (150, 150, 150)
GRIS_FONCE = (80, 80, 80)
GRIS_CLAIR = (240, 240, 240)
VERT       = (50, 200, 50)
ROUGE      = (200, 50, 50)
BLEU       = (50, 150, 255)
ORANGE     = (255, 140, 0)

# ========== POLICES ==========
font       = pygame.font.SysFont("Arial", 20, bold=True)
font_small = pygame.font.SysFont("Arial", 16)

# ========== PARAMÈTRES ==========
RAYON_ROUE      = 100
NOMBRE_RAYONS   = 6
EPAISSEUR_PNEU  = 12
SEUIL_GLISS     = 0.08
SEUIL_GLISS_COL = 0.10
INTENSITE_GLISS = 3.0
VITESSE_LISSAGE = 0.10

LARGEUR_JAUGE = 220
HAUTEUR_JAUGE = 22
LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 55
RAYON_ARRONDI  = 10


# ──────────────────────────────────────────────
class Particule:
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.vx  = direction * random.uniform(1.0, 3.0)
        self.vy  = random.uniform(-2.0, -0.5)
        self.vie = random.randint(20, 40)
        self.vie_max = self.vie
        self.taille  = random.randint(3, 8)

    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.05
        self.vie -= 1; self.taille = max(1, self.taille - 0.1)
        return self.vie > 0

    def draw(self, surface):
        a = int(255 * self.vie / self.vie_max)
        s = pygame.Surface((self.taille*2+2, self.taille*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (120, 120, 120, a),
                           (int(self.taille)+1, int(self.taille)+1), int(self.taille))
        surface.blit(s, (int(self.x - self.taille), int(self.y - self.taille)))


particules = []


# ──────────────────────────────────────────────
class Slider:
    """Slider pour fixer un % de pédale permanent."""
    R = 10
    H = 8

    def __init__(self, x, y, largeur, val=0.5, couleur=VERT, label=""):
        self.x = x; self.y = y; self.largeur = largeur
        self.val = val; self.couleur = couleur; self.label = label
        self.drag = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hx = self.x + int(self.val * self.largeur)
            if math.hypot(event.pos[0] - hx, event.pos[1] - self.y) < self.R + 6:
                self.drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self.val = max(0.0, min(1.0, (event.pos[0] - self.x) / self.largeur))

    def draw(self, surface):
        lbl = font_small.render(f"{self.label} : {int(self.val*100)} %", True, NOIR)
        surface.blit(lbl, (self.x, self.y - 22))

        pygame.draw.rect(surface, GRIS,
                         (self.x, self.y - self.H//2, self.largeur, self.H))
        if self.val > 0:
            pygame.draw.rect(surface, self.couleur,
                             (self.x, self.y - self.H//2,
                              int(self.val * self.largeur), self.H))
        pygame.draw.rect(surface, GRIS_FONCE,
                         (self.x, self.y - self.H//2, self.largeur, self.H), 1)

        hx = self.x + int(self.val * self.largeur)
        pygame.draw.circle(surface, BLANC,        (hx, self.y), self.R)
        pygame.draw.circle(surface, self.couleur, (hx, self.y), self.R - 3)
        pygame.draw.circle(surface, GRIS_FONCE,   (hx, self.y), self.R, 2)


# ──────────────────────────────────────────────
def dessiner_jauge(x, y, largeur, hauteur, valeur, couleur, titre):
    pygame.draw.rect(screen, GRIS, (x, y, largeur, hauteur), border_radius=5)
    pygame.draw.rect(screen, couleur, (x, y, int(largeur * valeur), hauteur), border_radius=5)
    pygame.draw.rect(screen, NOIR, (x, y, largeur, hauteur), 2, border_radius=5)
    screen.blit(font_small.render(titre, True, NOIR), (x, y - 20))


def dessiner_info_box(x, y, largeur, textes):
    hauteur = len(textes) * 30 + 20
    pygame.draw.rect(screen, GRIS_CLAIR, (x, y, largeur, hauteur), border_radius=10)
    pygame.draw.rect(screen, NOIR, (x, y, largeur, hauteur), 2, border_radius=10)
    for i, (label, valeur, couleur) in enumerate(textes):
        t = font_small.render(f"{label}: {valeur}", True, couleur)
        screen.blit(t, (x + 15, y + 15 + i * 30))


def get_couleur_temp(temp, t_min, t_max, t_ideal):
    if temp > t_max:             return ORANGE
    if temp < t_min:             return ROUGE
    if abs(temp - t_ideal) < 10: return VERT
    return GRIS_FONCE


def dessiner_roue(centre, rayon, angle, kappa):
    cx, cy = centre
    col = GRIS_FONCE
    if abs(kappa) > SEUIL_GLISS_COL:
        t = min(1.0, abs(kappa) * INTENSITE_GLISS)
        col = (int(80 + 175*t), int(80 - 30*t), int(80 - 80*t))

    pygame.draw.circle(screen, col, centre, rayon, EPAISSEUR_PNEU)
    pygame.draw.circle(screen, GRIS, centre, rayon - 15)

    for i in range(NOMBRE_RAYONS):
        a  = angle + i * 2 * math.pi / NOMBRE_RAYONS
        fx = cx + (rayon - 20) * math.cos(a)
        fy = cy + (rayon - 20) * math.sin(a)
        pygame.draw.line(screen, GRIS_FONCE, centre, (int(fx), int(fy)), 5)

    pygame.draw.circle(screen, (180, 180, 180), centre, 15)
    pygame.draw.circle(screen, NOIR, centre, 15, 2)

    if abs(kappa) > SEUIL_GLISS:
        lw = min(60, int(abs(kappa) * 250))
        op = int(min(180, abs(kappa) * 600))
        tr = pygame.Surface((lw, 5), pygame.SRCALPHA)
        tr.fill((40, 40, 40, op))
        screen.blit(tr, (cx - lw//2, cy + rayon + 5))


# Centre de la zone roue (panneau droit, x 290-780 → cx=535, zone y 20-390 → cy=205)
CX, CY = 535, 210

def dessiner_interface(etat, kappa, accel_val, frein_val,
                        sl_accel, sl_frein,
                        btn_accel, btn_frein,
                        input_accel, input_frein,
                        w_reelle=None):
    screen.fill(BLANC)
    vx, _, temp_ext, temp_int, usure = etat

    # ── Info vitesse ───────────────────────────
    vr_str = f"{w_reelle * phys.RAYON * 3.6:.1f} km/h" if w_reelle is not None else "--"
    dessiner_info_box(20, 20, 250, [
        ("Vitesse véhicule", f"{vx*3.6:.1f} km/h", BLEU),
        ("Vitesse roue",     vr_str,                BLEU),
    ])

    # ── Info temp / usure ──────────────────────
    c_ext = get_couleur_temp(temp_ext, 80, 110, phys.TEMP_IDEALE)
    c_int = get_couleur_temp(temp_int, 70, 100, 90)
    c_usu = ROUGE if usure > 0.5 else ORANGE if usure > 0.2 else VERT
    dessiner_info_box(20, 115, 250, [
        ("Temp. surface",  f"{temp_ext:.1f} °C",  c_ext),
        ("Temp. carcasse", f"{temp_int:.1f} °C",  c_int),
        ("Usure pneu",     f"{usure*100:.1f} %",  c_usu),
    ])

    # ── Glissement ─────────────────────────────
    c_k = ORANGE if abs(kappa) > SEUIL_GLISS_COL else BLEU if kappa < -0.05 else GRIS_FONCE
    screen.blit(font.render(f"Glissement: {kappa*100:.1f} %", True, c_k), (20, 255))

    # ── Roue (centrée dans la moitié droite) ───
    dessiner_roue((CX, CY), RAYON_ROUE, etat[1], kappa)

    # ── Jauges ─────────────────────────────────
    dessiner_jauge(40,  490, LARGEUR_JAUGE, HAUTEUR_JAUGE, accel_val, VERT,  "Accélération")
    dessiner_jauge(520, 490, LARGEUR_JAUGE, HAUTEUR_JAUGE, frein_val, ROUGE, "Freinage")

    # ── Sliders ────────────────────────────────
    sl_accel.draw(screen)
    sl_frein.draw(screen)

    # ── Boutons ────────────────────────────────
    col_a = VERT  if accel_val > 0 else GRIS
    col_f = ROUGE if frein_val > 0 else GRIS
    pygame.draw.rect(screen, col_a, btn_accel, border_radius=RAYON_ARRONDI)
    pygame.draw.rect(screen, NOIR,  btn_accel, 3, border_radius=RAYON_ARRONDI)
    pygame.draw.rect(screen, col_f, btn_frein, border_radius=RAYON_ARRONDI)
    pygame.draw.rect(screen, NOIR,  btn_frein, 3, border_radius=RAYON_ARRONDI)
    screen.blit(font.render("ACCÉLÉRER", True, BLANC),
                (btn_accel.x + 52, btn_accel.y + 16))
    screen.blit(font.render("FREINER",   True, BLANC),
                (btn_frein.x  + 65, btn_frein.y  + 16))


# ──────────────────────────────────────────────
def main():
    clock = pygame.time.Clock()
    etat  = phys.ETAT_INITIAL.copy()

    accel_val    = 0.0
    frein_val    = 0.0
    input_accel  = False
    input_frein  = False
    angle_cumule = 0.0

    btn_accel = pygame.Rect(40,  540, LARGEUR_BOUTON, HAUTEUR_BOUTON)
    btn_frein = pygame.Rect(520, 540, LARGEUR_BOUTON, HAUTEUR_BOUTON)

    # Sliders positionnés au-dessus des boutons
    sl_accel = Slider(40,  510, LARGEUR_BOUTON, val=0.5, couleur=VERT,  label="Seuil gaz")
    sl_frein = Slider(520, 510, LARGEUR_BOUTON, val=0.5, couleur=ROUGE, label="Seuil frein")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            sl_accel.handle_event(event)
            sl_frein.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_accel.collidepoint(event.pos): input_accel = True
                if btn_frein.collidepoint(event.pos): input_frein = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                input_accel = False
                input_frein = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):   input_accel = True
                if event.key in (pygame.K_s, pygame.K_DOWN): input_frein = True
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_UP):   input_accel = False
                if event.key in (pygame.K_s, pygame.K_DOWN): input_frein = False

        # Cible = valeur du slider si bouton enfoncé, sinon 0
        cible_a = sl_accel.val if input_accel else 0.0
        cible_f = sl_frein.val if input_frein else 0.0
        accel_val += (cible_a - accel_val) * VITESSE_LISSAGE
        frein_val += (cible_f - frein_val) * VITESSE_LISSAGE

        # Physique
        m_a = phys.get_couple_moteur(accel_val)
        m_f = phys.get_couple_frein(frein_val)

        def wrapper(t, y):
            y[0] = max(0, y[0])
            y[4] = max(0, min(1, y[4]))
            return phys.derivee(t, y, m_a, m_f)

        try:
            sol = solve_ivp(wrapper, (0, dt), etat, method='RK45', max_step=dt/5)
            if sol.success:
                etat = sol.y[:, -1].tolist()
        except Exception:
            pass

        vx, w = etat[0], etat[1]
        v_ref = max(abs(vx), abs(phys.RAYON * w), 0.5)
        kappa = (phys.RAYON * w - vx) / v_ref
        angle_cumule += w * dt

        if abs(kappa) > SEUIL_GLISS:
            for _ in range(int(abs(kappa) * 5)):
                px = CX + random.randint(-15, 15)
                py = CY + RAYON_ROUE
                particules.append(Particule(px, py, -1 if kappa > 0 else 1))

        etat_aff    = etat.copy()
        etat_aff[1] = angle_cumule

        dessiner_interface(
            etat_aff, kappa,
            accel_val, frein_val,
            sl_accel, sl_frein,
            btn_accel, btn_frein,
            input_accel, input_frein,
            w_reelle=etat[1]
        )

        particules[:] = [p for p in particules if p.update()]
        for p in particules: p.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
