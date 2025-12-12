import pymunk
from dataclasses import dataclass
from typing import List, Tuple
import math
import random
from PyQt6.QtCore import QObject, pyqtSignal
from model.graph_model import BallsList


@dataclass
class BallState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    angular_velocity: float


# La méthode pour les boules (numéro, couleur, stripe) et la rotation des boules est généré par Gemini
class BillardModel(QObject):
    BALL_COLORS = {
        1: (255, 215, 0),
        2: (0, 0, 255),
        3: (255, 0, 0),
        4: (128, 0, 128),
        5: (255, 165, 0),
        6: (34, 139, 34),
        7: (128, 0, 0),
        8: (0, 0, 0),
    }

    # initialisation du QAbstractItemModel
    tracked_balls_list = BallsList()

    def __init__(self, width: int = 1200, height: int = 600):
        super().__init__()
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.damping = 1.0
        self.space.sleep_time_threshold = 0.3
        self.space.idle_speed_threshold = 10

        self.ball_radius = 15
        self.cue_length = 200
        self.cue_width = 8
        self.max_power = 8000

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
        hole = 120
        half_width = int(self.width / 2 - hole * 0.75)

        # pour les triangles
        spacer = thickness / 2
        tri_margin = hole - spacer
        mid_tri = half_width + spacer

        #walls
        self._add_wall((20, hole), (20, self.height - hole), thickness)
        self._add_wall((self.width - 20, hole), (self.width - 20, self.height - hole), thickness)
        self._add_wall((hole, 20), (half_width, 20), thickness)
        self._add_wall((hole, self.height - 20), (half_width, self.height - 20), thickness)
        self._add_wall((self.width - hole, self.height - 20), (self.width - half_width, self.height - 20), thickness)
        self._add_wall((self.width - hole, 20), (self.width - half_width, 20), thickness)
        #triangle
        """Liste des triangles à dessiner
                    Par Maxime grondin (j'en suis fier)

                    Pour générer un triangle rectangle isocèle, il faut ajouter à la liste (liste_triangle_rectangle)
                    [(x de l'origine,y de l'origine), +/- 1, +/- 1]

                    le +/- 1 dit à la boucle dans quelle axe les deux cathètes seront dessinées
                """
        liste_triangle_rectangle = [  # mur verticaux
            [(spacer, tri_margin), 1, -1],
            [(spacer, self.height - tri_margin), 1, 1],
            [(self.width - spacer, tri_margin), -1, -1],
            [(self.width - spacer, self.height - tri_margin), -1, 1],
            # mur horisontaux
            [(tri_margin, spacer), -1, 1],
            [(tri_margin, self.height - spacer), -1, -1],
            [(self.width - tri_margin, spacer), 1, 1],
            [(self.width - tri_margin, self.height - spacer), 1, -1],
            # poches du milieu
            [(mid_tri, self.height - spacer), 1, -1],
            [(self.width - mid_tri, self.height - spacer), -1, -1],
            [(mid_tri, spacer), 1, 1],
            [(self.width - mid_tri, spacer), -1, 1],
        ]
        self._add_tiangle(liste_triangle_rectangle,thickness)

    def _add_tiangle(self, list, thickness):
        for coor in list:
            tri = [(coor[0][0], coor[0][1]),
                   (coor[0][0] + thickness * coor[1], coor[0][1]),
                   (coor[0][0], coor[0][1] + thickness * coor[2])]

            triangle = pymunk.Poly(self.space.static_body, tri)
            triangle.elasticity = 0.8
            triangle.friction = 0.5
            self.space.add(triangle)


    def _add_wall(self, a, b, radius):
        wall = pymunk.Segment(self.space.static_body, a, b, radius)
        wall.elasticity = 0.8
        wall.friction = 0.5
        self.space.add(wall)

    def _create_balls(self):
        self.cue_ball = self._create_single_ball((self.width // 4, self.height // 2), 0)

        start_x = self.width * 0.75
        start_y = self.height / 2

        rows = 5
        offset_x = self.ball_radius * 1.75
        offset_y = self.ball_radius * 2.05

        available_numbers = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        random.shuffle(available_numbers)

        for col in range(rows):
            x = start_x + (col * offset_x)
            start_col_y = start_y - (col * offset_y) / 2

            for row in range(col + 1):
                y = start_col_y + (row * offset_y)

                if col == 2 and row == 1:
                    ball_number = 8
                else:
                    ball_number = available_numbers.pop()

                self._create_single_ball((x, y), ball_number)

    def _create_single_ball(self, position, number):
        mass = 3
        moment = pymunk.moment_for_circle(mass, 0, self.ball_radius)

        body = pymunk.Body(mass, moment)
        body.position = position

        shape = pymunk.Circle(body, self.ball_radius)
        shape.elasticity = 0.8
        shape.friction = 1.0

        if number == 0:
            color_rgb = (255, 255, 255)
            is_stripe = False
        elif number == 8:
            color_rgb = self.BALL_COLORS[8]
            is_stripe = False
        else:
            is_stripe = number > 8
            base_index = number if number <= 8 else number - 8
            color_rgb = self.BALL_COLORS[base_index]

        shape.color = color_rgb + (255,)
        shape.number = number
        shape.is_stripe = is_stripe

        pivot = pymunk.PivotJoint(self.space.static_body, body, (0, 0), (0, 0))
        pivot.max_bias = 0
        pivot.max_force = 100

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

            self.update_graph()

            steps = 2
            for _ in range(steps):
                self.space.step(dt / steps)

            if self._all_balls_stopped():
                self.is_aiming = True
                self.cue_locked = False
                self._stop_rotation()

    def _stop_rotation(self):
        for body in self.space.bodies:
            if body.body_type == pymunk.Body.DYNAMIC:
                body.angular_velocity = 0
                body.velocity = (0, 0)

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
                state.append(BallState(position=tuple(shape.body.position), velocity=tuple(shape.body.velocity),
                                       angular_velocity=shape.body.angular_velocity))
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

    """Graph et liste de balle"""

    def add_ball(self, number):
        self.tracked_balls_list.add_item(number)

    def update_graph(self):
        print("hello list")

    def getListModel(self):
        return self.tracked_balls_list

    def ajouter_balle_liste(self, balle):
        if balle is not None:
            self.tracked_balls_list.add_item(balle)

    def supprimer_balle_liste(self, balle):
        if balle is not None and self.tracked_balls_list.rowCount() > 0:
            self.tracked_balls_list.remove_item(balle)
