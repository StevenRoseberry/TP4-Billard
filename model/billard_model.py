import pymunk
from dataclasses import dataclass
from typing import List, Tuple
import math
import random

# --- AJOUT: Définition des couleurs standards du billard (RGB) ---
BALL_COLORS = {
    1: (255, 215, 0),  # Jaune (1 et 9)
    2: (0, 0, 255),  # Bleu (2 et 10)
    3: (255, 0, 0),  # Rouge (3 et 11)
    4: (128, 0, 128),  # Violet (4 et 12)
    5: (255, 165, 0),  # Orange (5 et 13)
    6: (34, 139, 34),  # Vert (6 et 14)
    7: (128, 0, 0),  # Marron (7 et 15)
    8: (0, 0, 0),  # Noir (8)
}


# -----------------------------------------------------------------

@dataclass
class BallState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    angular_velocity: float


class BillardModel:
    def __init__(self, width: int = 1200, height: int = 600):
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        # Légère augmentation de la friction pour que ça roule moins "sur la glace"
        self.space.damping = 0.98

        self.ball_radius = 15
        self.cue_length = 200
        self.cue_width = 8
        self.max_power = 2500

        self.cue_ball = None
        self.cue_stick = None

        self.is_aiming = True
        self.cue_locked = False
        self.cue_angle = 0
        self.cue_distance = 100
        self.power = 0

        self.history: List[List[BallState]] = []

        self._create_table()
        self._create_balls()
        self._create_cue_stick()

    def _create_table(self):
        # Murs physiques placés exactement sur les bords
        # L'épaisseur repousse la balle vers l'intérieur
        thickness = 40

        # Mur Gauche
        self._add_wall((20, 0), (20, self.height), thickness)
        # Mur Droit
        self._add_wall((self.width - 20, 0), (self.width - 20, self.height), thickness)
        # Mur Haut (Pymunk 0 est en bas, donc c'est le "bas" visuel si Qt n'est pas inversé)
        self._add_wall((0, 20), (self.width, 20), thickness)
        # Mur Bas
        self._add_wall((0, self.height - 20), (self.width, self.height - 20), thickness)

    def _add_wall(self, a, b, radius):
        wall = pymunk.Segment(self.space.static_body, a, b, radius)
        wall.elasticity = 0.8
        wall.friction = 0.5
        self.space.add(wall)

    def _create_balls(self):
        # 1. La boule blanche (Numéro 0 par convention ici)
        # On la place un peu plus à gauche pour le "break"
        cue_ball_pos = (self.width * 0.25, self.height / 2)
        self.cue_ball = self._create_single_ball(cue_ball_pos, number=0)

        # 2. Le rack de boules colorées (Triangle)
        start_x = self.width * 0.75
        start_y = self.height / 2

        rows = 5
        offset_x = self.ball_radius * 1.75
        offset_y = self.ball_radius * 2.05

        # On prépare les numéros disponibles (tous sauf la 8 et la blanche)
        available_numbers = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        random.shuffle(available_numbers)  # On mélange pour que ce soit différent à chaque partie
        # -----------------------------------------------

        for col in range(rows):
            x = start_x + (col * offset_x)
            start_col_y = start_y - (col * offset_y) / 2

            for row in range(col + 1):
                y = start_col_y + (row * offset_y)

                # La noire (8) doit être au milieu de la 3ème colonne (index col=2, row=1)
                if col == 2 and row == 1:
                    ball_number = 8
                else:
                    # On prend un numéro au hasard dans le sac
                    ball_number = available_numbers.pop()

                self._create_single_ball((x, y), ball_number)

    # Prend en fonction le numéro de la balle
    def _create_single_ball(self, position, number):
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, self.ball_radius)
        body = pymunk.Body(mass, moment)
        body.position = position

        shape = pymunk.Circle(body, self.ball_radius)
        shape.elasticity = 0.95
        shape.friction = 0.5

        if number == 0:
            # Blanche
            color_rgb = (255, 255, 255)
            is_stripe = False
        elif number == 8:
            # Noire
            color_rgb = BALL_COLORS[8]
            is_stripe = False
        else:
            # Autres balles
            is_stripe = number > 8
            # Si c'est > 8 (ex: 9), la couleur de base est 9-8 = 1 (Jaune)
            base_color_index = number if number <= 8 else number - 8
            color_rgb = BALL_COLORS[base_color_index]

        # Info stocké directement sur l'objet shape de Pymunk que la vue peut lire
        shape.color = color_rgb
        shape.number = number
        shape.is_stripe = is_stripe
        # -----------------------------------------------------------

        self.space.add(body, shape)
        return shape

    def _create_cue_stick(self):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = self.cue_ball.body.position
        shape = pymunk.Segment(body, (0, 0), (self.cue_length, 0), self.cue_width // 2)
        shape.sensor = True
        shape.color = (139, 69, 19, 255)
        self.cue_stick = shape

    def update(self, dt: float):
        if not self.is_aiming:
            # On utilise une sous-étape plus fine pour une meilleure physique
            steps = 2
            for _ in range(steps):
                self.space.step(dt / steps)

            if self._all_balls_stopped():
                self.is_aiming = True
                self.cue_locked = False

    def _all_balls_stopped(self, threshold: float = 2.0) -> bool:
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                if shape.body.velocity.length > threshold:
                    return False
        return True

    # ... (Le reste des méthodes set_cue_angle, shoot, reset, etc. reste identique) ...
    def set_cue_angle(self, angle: float):
        if self.is_aiming and not self.cue_locked:
            self.cue_angle = angle

    def set_cue_distance(self, distance: float):
        if self.is_aiming:
            self.cue_distance = max(50, min(distance, 150))

    def set_power(self, power: float):
        self.power = max(0, min(power, 1))

    def toggle_cue_lock(self):
        if self.is_aiming:
            self.cue_locked = not self.cue_locked

    def shoot(self):
        if not self.is_aiming or not self._all_balls_stopped():
            return

        self._save_state()
        force = self.power * self.max_power
        impulse_x = force * math.cos(self.cue_angle)
        impulse_y = force * math.sin(self.cue_angle)

        self.cue_ball.body.apply_impulse_at_world_point(
            (impulse_x, impulse_y), self.cue_ball.body.position
        )
        self.is_aiming = False
        self.cue_locked = False
        self.power = 0

    def _save_state(self):
        state = []
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                state.append(BallState(
                    position=tuple(shape.body.position),
                    velocity=tuple(shape.body.velocity),
                    angular_velocity=shape.body.angular_velocity
                ))
        self.history.append(state)
        if len(self.history) > 10: self.history.pop(0)

    def undo_last_shot(self):
        if not self.history or not self.is_aiming: return
        state = self.history.pop()
        i = 0
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle) and i < len(state):
                b = state[i]
                shape.body.position = b.position
                shape.body.velocity = b.velocity
                shape.body.angular_velocity = b.angular_velocity
                i += 1

    def reset(self):
        for shape in list(self.space.shapes):
            if isinstance(shape, pymunk.Circle):
                self.space.remove(shape, shape.body)

        self._create_balls()
        self.is_aiming = True
        self.cue_locked = False
        self.power = 0
        self.history.clear()

    def get_cue_position(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        ball_pos = self.cue_ball.body.position
        start_x = ball_pos.x - (self.ball_radius + self.cue_distance) * math.cos(self.cue_angle)
        start_y = ball_pos.y - (self.ball_radius + self.cue_distance) * math.sin(self.cue_angle)
        end_x = start_x - self.cue_length * math.cos(self.cue_angle)
        end_y = start_y - self.cue_length * math.sin(self.cue_angle)
        return ((start_x, start_y), (end_x, end_y))