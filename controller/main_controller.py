import math
from PyQt6.QtCore import QTimer


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # Timer pour la mise à jour physique
        self.physics_timer = QTimer()
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16)  # ~60 FPS

        # Connecter le modèle à la vue
        self.view.set_model(model)
        self.view.set_controller(self)

    def update_physics(self):
        """Mettre à jour la physique du jeu"""
        self.model.update(1 / 60.0)

    def on_mouse_move(self, x: int, y: int):
        """Gérer le mouvement de la souris pour viser"""
        if not self.model.is_aiming:
            return

        # Calculer l'angle entre la boule et la souris
        ball_pos = self.model.cue_ball.body.position

        dx = x - ball_pos.x
        dy = y - ball_pos.y

        angle = math.atan2(dy, dx)
        self.model.set_cue_angle(angle)

    def on_mouse_press(self):
        """Début du maintien pour ajuster la puissance"""
        # La puissance est gérée par le timer dans la vue
        pass

    def on_mouse_release(self):
        """Relâchement pour tirer"""
        # Le tir est déclenché par la vue
        pass

    def set_power(self, power: float):
        """Définir la puissance du tir"""
        self.model.set_power(power)

    def shoot(self):
        """Tirer la boule"""
        self.model.shoot()

    def reset_game(self):
        """Réinitialiser le jeu"""
        self.model.reset()

    def undo_shot(self):
        """Annuler le dernier coup"""
        self.model.undo_last_shot()