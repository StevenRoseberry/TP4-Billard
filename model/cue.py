import pymunk
import math


class Cue:
    def __init__(self, space):
        self.length = 200
        self.width = 8
        self.angle = 0
        self.distance = 100
        self.power = 0
        self.locked = False

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.shape = pymunk.Segment(self.body, (0, 0), (self.length, 0), self.width // 2)
        self.shape.sensor = True
        space.add(self.body, self.shape)

    def get_render_coords(self, ball_pos, ball_radius):
        aim_vec = pymunk.Vec2d(math.cos(self.angle), math.sin(self.angle))
        start = ball_pos - aim_vec * (ball_radius + self.distance)
        end = start - aim_vec * self.length
        return (start.x, start.y), (end.x, end.y)