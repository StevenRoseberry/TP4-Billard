import pymunk
import math
import random
from PyQt6.QtCore import QObject
from typing import List

from model.config import *
from model.ball import Ball
from model.table import Table
from model.cue import Cue


class BillardModel(QObject):
    def __init__(self, width=WIDTH, height=HEIGHT):
        super().__init__()
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.damping = 0.99
        self.space.sleep_time_threshold = 0.3
        self.space.idle_speed_threshold = 10

        self.table = None
        self.cue = None
        self.balls: List[Ball] = []
        self.cue_ball: Ball = None

        self.is_aiming = True
        self.pocketed_history: List[int] = []

        self.init_world()

    def init_world(self):
        self.table = Table(self.space, self.width, self.height)
        self._create_balls()
        self.cue = Cue(self.space)

    def _create_balls(self):
        self.cue_ball = Ball(self.space, (self.width // 4, self.height // 2), 0)
        self.balls.append(self.cue_ball)

        start_x = self.width * 0.75
        start_y = self.height / 2
        r = BALL_RADIUS
        offset_x, offset_y = r * 1.75, r * 2.05

        nums = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        random.shuffle(nums)

        for col in range(5):
            x = start_x + (col * offset_x)
            start_row_y = start_y - (col * offset_y) / 2
            for row in range(col + 1):
                y = start_row_y + (row * offset_y)
                num = 8 if (col == 2 and row == 1) else nums.pop()
                self.balls.append(Ball(self.space, (x, y), num))

    def update(self, dt: float):
        if not self.is_aiming:
            steps = 3
            for _ in range(steps):
                self.space.step(dt / steps)
                self._check_game_rules()

            if self._all_balls_stopped():
                self.is_aiming = True
                self.cue.locked = False
                for b in self.balls: b.stop()

    def _all_balls_stopped(self) -> bool:
        return all(not b.is_moving() for b in self.balls)

    def _check_game_rules(self):
        balls_to_remove = []
        for b in self.balls:
            pos = b.body.position
            in_pocket = False
            for px, py in self.table.pockets:
                if (pos.x - px) ** 2 + (pos.y - py) ** 2 < self.table.pocket_radius ** 2:
                    in_pocket = True
                    break

            if in_pocket or pos.x < -50 or pos.x > self.width + 50:
                balls_to_remove.append(b)

        for b in balls_to_remove:
            self._handle_ball_removal(b)

    def _handle_ball_removal(self, ball: Ball):
        if ball.number == 0:
            print("FAUTE ! La blanche est rentrée.")
            ball.body.position = (self.width // 4, self.height // 2)
            ball.stop()
        else:
            print(f"Balle {ball.number} rentrée !")
            self.pocketed_history.append(ball.number)
            ball.remove_from(self.space)
            self.balls.remove(ball)

    def set_cue_angle(self, angle):
        if not self.cue.locked: self.cue.angle = angle

    def set_cue_distance(self, d):
        self.cue.distance = max(50, min(d, 150))

    def set_power(self, p):
        self.cue.power = max(0, min(p, 1))

    def toggle_cue_lock(self):
        if self.is_aiming: self.cue.locked = not self.cue.locked

    def shoot(self):
        if not self.is_aiming: return
        f = self.cue.power * 6000
        impulse = (f * math.cos(self.cue.angle), f * math.sin(self.cue.angle))
        self.cue_ball.body.apply_impulse_at_world_point(impulse, self.cue_ball.body.position)
        self.is_aiming = False
        self.cue.locked = False
        self.cue.power = 0

    def reset(self):
        for x in list(self.space.bodies) + list(self.space.shapes) + list(self.space.constraints):
            self.space.remove(x)
        self.balls.clear()
        self.pocketed_history.clear()
        self.init_world()
        self.is_aiming = True
        self.cue.locked = False
        self.cue.power = 0

    def undo_last_shot(self):
        pass