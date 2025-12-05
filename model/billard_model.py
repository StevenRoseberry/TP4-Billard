import pymunk
from dataclasses import dataclass
from typing import List, Tuple
import math
import random


@dataclass
class BallState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    angular_velocity: float


# La physique des boules a été adapté par Gemini à l'aide d'un projet de billard déjà fait sur Github :
# Source : https://github.com/iwarshavsky/Pool-Simulation/blob/main/utils/ball.py
class BillardModel:
    def __init__(self, width: int = 1600, height: int = 800):
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        # 1.0 ou très proche, car le PivotJoint va gérer le freinage
        self.space.damping = 1.0

        # Paramètres pour que les boules s'arrêtent net quand elles sont très lentes
        self.space.sleep_time_threshold = 0.3
        self.space.idle_speed_threshold = 10

        self.ball_radius = 15

        # Ajustement pour la nouvelle masse (3x plus lourde) et la friction linéaire
        self.max_power = 8000

        self.cue_length = 200
        self.cue_width = 8

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
        static_body = self.space.static_body
        thickness = 40

        self._add_wall((20, 0), (20, self.height), thickness)
        self._add_wall((self.width - 20, 0), (self.width - 20, self.height), thickness)
        self._add_wall((0, 20), (self.width, 20), thickness)
        self._add_wall((0, self.height - 20), (self.width, self.height - 20), thickness)

    def _add_wall(self, a, b, radius):
        wall = pymunk.Segment(self.space.static_body, a, b, radius)
        wall.elasticity = 0.8  # Rebond des bandes
        wall.friction = 0.5
        self.space.add(wall)

    def _create_balls(self):
        self.cue_ball = self._create_single_ball((self.width // 4, self.height // 2), (255, 255, 255))

        start_x = self.width * 0.75
        start_y = self.height / 2
        rows = 5
        offset_x = self.ball_radius * 1.75
        offset_y = self.ball_radius * 2.05

        colors = [
            (255, 215, 0), (0, 0, 255), (255, 0, 0), (128, 0, 128), (255, 165, 0),
            (34, 139, 34), (128, 0, 0), (0, 0, 0), (255, 255, 0), (0, 0, 255),
            (255, 0, 255), (0, 255, 255), (139, 69, 19), (255, 192, 203), (128, 128, 0)
        ]

        col_index = 0
        for col in range(rows):
            x = start_x + (col * offset_x)
            start_col_y = start_y - (col * offset_y) / 2
            for row in range(col + 1):
                y = start_col_y + (row * offset_y)
                if col == 2 and row == 1:
                    color = (0, 0, 0)
                else:
                    color = colors[col_index % len(colors)]
                    col_index += 1
                self._create_single_ball((x, y), color)

    def _create_single_ball(self, position, color_rgb):
        mass = 3  # Masse plus lourde comme dans ton exemple
        moment = pymunk.moment_for_circle(mass, 0, self.ball_radius)
        body = pymunk.Body(mass, moment)
        body.position = position

        shape = pymunk.Circle(body, self.ball_radius)
        shape.elasticity = 0.8  # Un peu moins élastique (plus réaliste)
        shape.friction = 1.0  # Friction élevée entre les boules
        shape.color = color_rgb + (255,)

        pivot = pymunk.PivotJoint(self.space.static_body, body, (0, 0), (0, 0))
        pivot.max_bias = 0  # Désactive la correction de position (important)
        pivot.max_force = 100  # Force de friction (Ajuste ça si le tapis est trop lent/rapide)

        self.space.add(body, shape, pivot)
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
            steps = 2
            for _ in range(steps):
                self.space.step(dt / steps)

            if self._all_balls_stopped():
                self.is_aiming = True
                self.cue_locked = False

    def _all_balls_stopped(self, threshold: float = 5.0) -> bool:
        for body in self.space.bodies:
            if body.body_type == pymunk.Body.DYNAMIC:
                if body.velocity.length > threshold:
                    return False
        return True

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

        balls = [s for s in self.space.shapes if isinstance(s, pymunk.Circle)]

        for i, shape in enumerate(balls):
            if i < len(state):
                b = state[i]
                shape.body.position = b.position
                shape.body.velocity = b.velocity
                shape.body.angular_velocity = b.angular_velocity
                # Réveiller le body s'il dormait
                shape.body.activate()

    def reset(self):
        for body in list(self.space.bodies):
            if body.body_type == pymunk.Body.DYNAMIC:
                self.space.remove(body)

        for shape in list(self.space.shapes):
            if isinstance(shape, pymunk.Circle):
                self.space.remove(shape)

        for constraint in list(self.space.constraints):
            self.space.remove(constraint)

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