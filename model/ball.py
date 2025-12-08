import pymunk
from model.config import *


class Ball:
    def __init__(self, space, position, number):
        self.number = number
        self.radius = BALL_RADIUS

        # Physique
        moment = pymunk.moment_for_circle(BALL_MASS, 0, self.radius)
        self.body = pymunk.Body(BALL_MASS, moment)
        self.body.position = position

        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 0.9
        self.shape.friction = 0.8

        # Apparence
        self.is_stripe = number > 8
        c_idx = 8 if number == 8 else (number if number <= 8 else number - 8)
        self.color_rgb = BALL_COLORS.get(number, BALL_COLORS[c_idx])

        # Frottement (PivotJoint)
        self.pivot = pymunk.PivotJoint(space.static_body, self.body, (0, 0), (0, 0))
        self.pivot.max_bias = 0
        self.pivot.max_force = FRICTION_TABLE

        self.gear = pymunk.SimpleMotor(space.static_body, self.body, 0)
        self.gear.max_force = FRICTION_TABLE / 2

        space.add(self.body, self.shape, self.pivot, self.gear)

    def stop(self):
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0

    def is_moving(self):
        return self.body.velocity.length > 2.0

    def remove_from(self, space):
        space.remove(self.body, self.shape, self.pivot, self.gear)