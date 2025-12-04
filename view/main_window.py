import sys
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.uic import loadUi
import pymunk


class PymunkWidget(QWidget):
    """Widget qui dessine Pymunk avec QPainter"""
    mouse_moved = pyqtSignal(int, int)
    mouse_pressed = pyqtSignal()
    mouse_released = pyqtSignal()

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.setMinimumSize(width, height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Timer pour le rendu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS

        self.space = None
        self.model = None

        # Tracking de la souris
        self.setMouseTracking(True)
        self.mouse_pressed_flag = False

    def set_model(self, model):
        """Associer le modèle"""
        self.model = model
        self.space = model.space

    def _pymunk_to_qt(self, x, y):
        """Convertir les coordonnées Pymunk (origine bas-gauche) en Qt (origine haut-gauche)"""
        return (x, self.height - y)

    def _qt_to_pymunk(self, x, y):
        """Convertir les coordonnées Qt en Pymunk"""
        return (x, self.height - y)

    def paintEvent(self, event):
        """Dessiner la scène avec QPainter"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fond vert billard
        painter.fillRect(0, 0, self.width, self.height, QColor(34, 139, 34))

        # Debug: dessiner un cercle de test
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.drawEllipse(QPointF(100, 100), 50, 50)
        painter.drawText(100, 150, "TEST")

        if self.space is None:
            painter.drawText(200, 200, "SPACE IS NONE!")
            return

        painter.drawText(200, 200, f"Shapes: {len(self.space.shapes)}")

        # Dessiner les bords de la table
        self._draw_walls(painter)

        # Dessiner les balles
        self._draw_balls(painter)

        # Dessiner le bâton si en mode visée
        if self.model and self.model.is_aiming:
            painter.drawText(200, 250, "AIMING MODE")
            self._draw_aim_line(painter)
            self._draw_cue_stick(painter)

    def _draw_walls(self, painter):
        """Dessiner les murs de la table"""
        pen = QPen(QColor(139, 69, 19), 10)
        painter.setPen(pen)

        # Rectangle de la table
        painter.drawRect(20, 20, self.width - 40, self.height - 40)

    def _draw_balls(self, painter):
        """Dessiner toutes les balles"""
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos = shape.body.position
                qt_x, qt_y = self._pymunk_to_qt(pos.x, pos.y)
                radius = shape.radius

                # Ombre
                shadow_brush = QBrush(QColor(0, 0, 0, 50))
                painter.setBrush(shadow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(qt_x + 3, qt_y + 3), radius, radius)

                # Boule blanche
                ball_brush = QBrush(QColor(255, 255, 255))
                painter.setBrush(ball_brush)
                pen = QPen(QColor(200, 200, 200), 2)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(qt_x, qt_y), radius, radius)

                # Reflet
                highlight_brush = QBrush(QColor(255, 255, 255, 120))
                painter.setBrush(highlight_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(qt_x - radius / 3, qt_y - radius / 3), radius / 3, radius / 3)

    def _draw_cue_stick(self, painter):
        """Dessiner le bâton de billard"""
        if not self.model:
            return

        start, end = self.model.get_cue_position()
        start_qt = self._pymunk_to_qt(start[0], start[1])
        end_qt = self._pymunk_to_qt(end[0], end[1])

        # Bâton principal (brun)
        pen = QPen(QColor(139, 69, 19), self.model.cue_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(start_qt[0]), int(start_qt[1]), int(end_qt[0]), int(end_qt[1]))

        # Embout doré
        painter.setBrush(QBrush(QColor(255, 215, 0)))
        painter.setPen(QPen(QColor(200, 170, 0), 2))
        painter.drawEllipse(QPointF(end_qt[0], end_qt[1]), 6, 6)

    def _draw_aim_line(self, painter):
        """Dessiner la ligne de visée"""
        if not self.model:
            return

        ball_pos = self.model.cue_ball.body.position
        ball_qt = self._pymunk_to_qt(ball_pos.x, ball_pos.y)

        # Ligne de visée devant la balle
        end_x = ball_pos.x + 200 * math.cos(self.model.cue_angle)
        end_y = ball_pos.y + 200 * math.sin(self.model.cue_angle)
        end_qt = self._pymunk_to_qt(end_x, end_y)

        # Ligne pointillée
        pen = QPen(QColor(255, 255, 0, 180), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        painter.drawLine(int(ball_qt[0]), int(ball_qt[1]), int(end_qt[0]), int(end_qt[1]))

    def mouseMoveEvent(self, event):
        """Gérer le mouvement de la souris"""
        qt_x = event.pos().x()
        qt_y = event.pos().y()

        # Convertir en coordonnées Pymunk
        pymunk_x, pymunk_y = self._qt_to_pymunk(qt_x, qt_y)

        self.mouse_moved.emit(int(pymunk_x), int(pymunk_y))

        # Si bouton maintenu, ajuster la distance
        if self.mouse_pressed_flag:
            self.mouse_pressed.emit()

    def mousePressEvent(self, event):
        """Gérer le clic de souris"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = True
            self.mouse_pressed.emit()

    def mouseReleaseEvent(self, event):
        """Gérer le relâchement de souris"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = False
            self.mouse_released.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Charger l'UI
        loadUi('view/ui/main_window.ui', self)

        # Forcer le graphFrame à prendre de l'espace
        self.graphFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.graphFrame.setMinimumHeight(500)

        # Créer le widget Pymunk
        self.pymunk_widget = PymunkWidget(1200, 500)
        self.pymunk_widget.setStyleSheet("background-color: rgb(34, 139, 34);")

        # Nettoyer le layout existant du graphFrame s'il y en a un
        old_layout = self.graphFrame.layout()
        if old_layout:
            QWidget().setLayout(old_layout)

        # Ajouter au layout du graphFrame
        layout = QVBoxLayout()
        layout.addWidget(self.pymunk_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        self.graphFrame.setLayout(layout)

        print(f"Widget créé: {self.pymunk_widget.size()}")
        print(f"GraphFrame size: {self.graphFrame.size()}")

        # Connecter les signaux
        self.createButton.clicked.connect(self.on_reset)
        self.deleteButton.clicked.connect(self.on_undo)

        # Bouton tirer
        self.pushButton.pressed.connect(self.on_shoot_pressed)
        self.pushButton.released.connect(self.on_shoot_released)

        # Progress bar pour la puissance
        self.progressBar.setValue(0)

        # Timer pour augmenter la puissance
        self.power_timer = QTimer()
        self.power_timer.timeout.connect(self.increase_power)
        self.power_accumulation = 0

    def set_controller(self, controller):
        """Associer le contrôleur"""
        self.controller = controller

        # Connecter les signaux de la souris
        self.pymunk_widget.mouse_moved.connect(controller.on_mouse_move)
        self.pymunk_widget.mouse_pressed.connect(controller.on_mouse_press)
        self.pymunk_widget.mouse_released.connect(controller.on_mouse_release)

    def set_model(self, model):
        """Associer le modèle au widget"""
        self.pymunk_widget.set_model(model)
        print(f"Model set! Ball position: {model.cue_ball.body.position}")

    def on_reset(self):
        """Bouton réinitialiser"""
        if hasattr(self, 'controller'):
            self.controller.reset_game()

    def on_undo(self):
        """Bouton annuler"""
        if hasattr(self, 'controller'):
            self.controller.undo_shot()

    def on_shoot_pressed(self):
        """Début du tir (bouton maintenu)"""
        self.power_accumulation = 0
        self.power_timer.start(50)  # Augmenter toutes les 50ms

    def on_shoot_released(self):
        """Fin du tir (bouton relâché)"""
        self.power_timer.stop()
        if hasattr(self, 'controller'):
            self.controller.shoot()
        self.power_accumulation = 0
        self.progressBar.setValue(0)

    def increase_power(self):
        """Augmenter la puissance progressivement"""
        self.power_accumulation = min(100, self.power_accumulation + 2)
        self.progressBar.setValue(self.power_accumulation)

        if hasattr(self, 'controller'):
            self.controller.set_power(self.power_accumulation / 100.0)

    def update_power_display(self, power: float):
        """Mettre à jour l'affichage de la puissance"""
        self.progressBar.setValue(int(power * 100))