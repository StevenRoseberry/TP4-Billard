import pymunk
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class BallState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    angular_velocity: float


class BillardModel:
    def __init__(self, width: int = 1200, height: int = 600):
        self.width = width
        self.height = height

        # Créer l'espace physique
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # Pas de gravité pour le billard
        self.space.damping = 0.95  # Friction de l'air

        # Paramètres
        self.ball_radius = 15
        self.cue_length = 200
        self.cue_width = 8
        self.max_power = 2000

        # État du jeu
        self.cue_ball = None
        self.cue_stick = None
        self.is_aiming = True
        self.cue_angle = 0
        self.cue_distance = 100
        self.power = 0

        # Historique pour annulation
        self.history: List[List[BallState]] = []

        # Initialiser la table
        self._create_table()
        self._create_balls()
        self._create_cue_stick()

    def _create_table(self):
        """Créer les bords de la table"""
        static_body = self.space.static_body

        # Murs (gauche, droite, haut, bas)
        walls = [
            pymunk.Segment(static_body, (20, 20), (20, self.height - 20), 5),
            pymunk.Segment(static_body, (self.width - 20, 20), (self.width - 20, self.height - 20), 5),
            pymunk.Segment(static_body, (20, 20), (self.width - 20, 20), 5),
            pymunk.Segment(static_body, (20, self.height - 20), (self.width - 20, self.height - 20), 5),
        ]

        for wall in walls:
            wall.elasticity = 0.8
            wall.friction = 0.5
            self.space.add(wall)

    def _create_balls(self):
        """Créer la boule blanche"""
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, self.ball_radius)

        # Boule blanche
        body = pymunk.Body(mass, moment)
        body.position = (self.width // 4, self.height // 2)

        shape = pymunk.Circle(body, self.ball_radius)
        shape.elasticity = 0.95
        shape.friction = 0.5
        shape.color = (255, 255, 255, 255)

        self.space.add(body, shape)
        self.cue_ball = shape

    def _create_cue_stick(self):
        """Créer le bâton de billard (corps cinématique)"""
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = self.cue_ball.body.position

        # Le bâton est un segment
        shape = pymunk.Segment(body, (0, 0), (self.cue_length, 0), self.cue_width // 2)
        shape.sensor = True  # Ne pas interagir physiquement
        shape.color = (139, 69, 19, 255)

        self.cue_stick = shape

    def update(self, dt: float):
        """Mettre à jour la physique"""
        if not self.is_aiming:
            self.space.step(dt)

            # Vérifier si toutes les balles sont arrêtées
            if self._all_balls_stopped():
                self.is_aiming = True

    def _all_balls_stopped(self, threshold: float = 1.0) -> bool:
        """Vérifier si toutes les balles sont arrêtées"""
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                vel = shape.body.velocity
                if vel.length > threshold:
                    return False
        return True

    def set_cue_angle(self, angle: float):
        """Définir l'angle du bâton"""
        if self.is_aiming:
            self.cue_angle = angle

    def set_cue_distance(self, distance: float):
        """Définir la distance du bâton (pour la puissance)"""
        if self.is_aiming:
            self.cue_distance = max(50, min(distance, 150))

    def set_power(self, power: float):
        """Définir la puissance (0-1)"""
        self.power = max(0, min(power, 1))

    def shoot(self):
        """Frapper la boule"""
        if not self.is_aiming or not self._all_balls_stopped():
            return

        # Sauvegarder l'état pour annulation
        self._save_state()

        # Calculer la force
        import math
        force = self.power * self.max_power

        # Appliquer l'impulsion
        impulse_x = force * math.cos(self.cue_angle)
        impulse_y = force * math.sin(self.cue_angle)

        self.cue_ball.body.apply_impulse_at_world_point(
            (impulse_x, impulse_y),
            self.cue_ball.body.position
        )

        self.is_aiming = False
        self.power = 0

    def _save_state(self):
        """Sauvegarder l'état actuel"""
        state = []
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                state.append(BallState(
                    position=tuple(shape.body.position),
                    velocity=tuple(shape.body.velocity),
                    angular_velocity=shape.body.angular_velocity
                ))
        self.history.append(state)

        # Limiter l'historique
        if len(self.history) > 10:
            self.history.pop(0)

    def undo_last_shot(self):
        """Annuler le dernier coup"""
        if not self.history or not self.is_aiming:
            return

        state = self.history.pop()

        i = 0
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle) and i < len(state):
                ball_state = state[i]
                shape.body.position = ball_state.position
                shape.body.velocity = ball_state.velocity
                shape.body.angular_velocity = ball_state.angular_velocity
                i += 1

    def reset(self):
        """Réinitialiser le jeu"""
        # Retirer toutes les formes et corps dynamiques
        for shape in list(self.space.shapes):
            if isinstance(shape, pymunk.Circle):
                self.space.remove(shape, shape.body)

        # Recréer les balles
        self._create_balls()

        # Réinitialiser l'état
        self.is_aiming = True
        self.power = 0
        self.history.clear()

    def get_cue_position(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Obtenir les coordonnées du bâton"""
        import math

        ball_pos = self.cue_ball.body.position

        # Position de départ (derrière la balle)
        start_x = ball_pos.x - (self.ball_radius + self.cue_distance) * math.cos(self.cue_angle)
        start_y = ball_pos.y - (self.ball_radius + self.cue_distance) * math.sin(self.cue_angle)

        # Position de fin
        end_x = start_x - self.cue_length * math.cos(self.cue_angle)
        end_y = start_y - self.cue_length * math.sin(self.cue_angle)

        return ((start_x, start_y), (end_x, end_y))