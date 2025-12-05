import math
from PyQt6.QtCore import QTimer


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.physics_timer = QTimer()
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16)

        self.view.set_model(model)
        self.view.set_controller(self)

    def update_physics(self):
        self.model.update(1 / 60.0)

    def on_mouse_move(self, x: int, y: int):
        # Si verrouillé ou pas en mode visée, on ne bouge pas
        if not self.model.is_aiming or self.model.cue_locked:
            return

        ball_pos = self.model.cue_ball.body.position
        dx = x - ball_pos.x
        dy = y - ball_pos.y
        angle = math.atan2(dy, dx)
        self.model.set_cue_angle(angle)

    def on_mouse_press(self):
        pass

    def on_mouse_release(self):
        pass

    def on_toggle_lock(self):
        self.model.toggle_cue_lock()

    def set_power(self, power: float):
        self.model.set_power(power)

    def shoot(self):
        self.model.shoot()

    def reset_game(self):
        self.model.reset()

    def undo_shot(self):
        self.model.undo_last_shot()