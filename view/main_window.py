import sys
import math
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.uic import loadUi
import pymunk

if TYPE_CHECKING:
    from controller.main_controller import MainController


class PymunkWidget(QWidget):
    """Widget qui dessine Pymunk avec QPainter"""
    mouse_moved = pyqtSignal(int, int)
    mouse_pressed = pyqtSignal()
    mouse_released = pyqtSignal()
    lock_toggled = pyqtSignal()

    if TYPE_CHECKING:
        controller: MainController | None

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.w_attr = width
        self.h_attr = height

        # CRUCIAL: On fixe la taille pour garantir que le visuel matche la physique
        self.setFixedSize(width, height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

        self.space = None
        self.model = None

        self.setMouseTracking(True)
        self.mouse_pressed_flag = False

    def set_controller(self,controller):
        self.controller = controller

    def set_model(self, model):
        self.model = model
        self.space = model.space

    def _pymunk_to_qt(self, x, y):
        # Conversion simple puisque la taille est fixe
        return (x, self.height() - y)

    def _qt_to_pymunk(self, x, y):
        return (x, self.height() - y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Tapis vert
        painter.fillRect(self.rect(), QColor(34, 139, 34))

        if self.space is None:
            return

        self._draw_walls(painter)
        self._draw_balls(painter)

        if self.model and self.model.is_aiming:
            self._draw_aim_line(painter)
            self._draw_cue_stick(painter)

    def _draw_walls(self, painter):
        # Dessine le cadre.
        # Physique: Mur à 20px du bord avec rayon 40 -> bord intérieur à 20+40 = 60px
        # Visuel: On dessine un rectangle brun épais pour représenter le bois

        wall_color = QColor(139, 69, 19)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Épaisseur visuelle du mur
        pen_width = 40
        pen = QPen(wall_color, pen_width)
        # On dessine "à cheval" sur la ligne, donc on déplace de moitié vers l'extérieur
        # pour que l'intérieur du trait corresponde à la physique
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        # Le rectangle visuel doit s'arrêter là où la balle rebondit
        # Dans le modèle: mur posé à 20, rayon 40. Le contact se fait à 20+40 = 60.
        # Donc le bord intérieur visuel doit être à 60.
        # Si on dessine un rect à 40 avec épaisseur 40, il va de 20 à 60. C'est parfait.

        margin = 40
        painter.drawRect(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

    def _draw_balls(self, painter):
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos = shape.body.position
                qt_x, qt_y = self._pymunk_to_qt(pos.x, pos.y)
                radius = shape.radius

                # Ombre
                painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(qt_x + 3, qt_y + 3), radius, radius)

                # Couleur de la balle (récupérée du modèle)
                if hasattr(shape, 'color'):
                    color = QColor(*shape.color)
                else:
                    color = QColor(255, 255, 255)

                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.drawEllipse(QPointF(qt_x, qt_y), radius, radius)

                # Petit reflet pour le style
                painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(qt_x - radius / 3, qt_y - radius / 3), radius / 2.5, radius / 2.5)

    def _draw_cue_stick(self, painter):
        if not self.model: return

        start, end = self.model.get_cue_position()
        start_qt = self._pymunk_to_qt(start[0], start[1])
        end_qt = self._pymunk_to_qt(end[0], end[1])

        pen = QPen(QColor(160, 82, 45), self.model.cue_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(start_qt[0]), int(start_qt[1]), int(end_qt[0]), int(end_qt[1]))

    def _draw_aim_line(self, painter):
        if not self.model: return

        ball_pos = self.model.cue_ball.body.position
        ball_qt = self._pymunk_to_qt(ball_pos.x, ball_pos.y)

        end_x = ball_pos.x + 200 * math.cos(self.model.cue_angle)
        end_y = ball_pos.y + 200 * math.sin(self.model.cue_angle)
        end_qt = self._pymunk_to_qt(end_x, end_y)

        color = QColor(255, 0, 0, 200) if self.model.cue_locked else QColor(255, 255, 255, 150)
        pen = QPen(color, 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(ball_qt[0]), int(ball_qt[1]), int(end_qt[0]), int(end_qt[1]))

    def mouseMoveEvent(self, event):
        qt_x = event.pos().x()
        qt_y = event.pos().y()
        pymunk_x, pymunk_y = self._qt_to_pymunk(qt_x, qt_y)
        self.mouse_moved.emit(int(pymunk_x), int(pymunk_y))
        if self.mouse_pressed_flag:
            self.mouse_pressed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = True
            self.mouse_pressed.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.lock_toggled.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = False
            self.mouse_released.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('view/ui/main_window.ui', self)

        # On laisse le layout gérer, mais on s'assure que le widget Pymunk a sa taille fixe
        # Le frame va s'adapter autour
        self.pymunk_widget = PymunkWidget(1200, 600)  # Taille du modèle par défaut

        existing_layout = self.graphFrame.layout()
        if existing_layout is not None:
            # On vide le layout s'il y a des trucs bizarres avant
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()
            existing_layout.addWidget(self.pymunk_widget)
            # Centrer le jeu dans la fenêtre
            existing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            layout = QVBoxLayout()
            layout.addWidget(self.pymunk_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.graphFrame.setLayout(layout)

        self.createButton.clicked.connect(self.on_reset)
        self.deleteButton.clicked.connect(self.on_undo)
        self.pushButton.pressed.connect(self.on_shoot_pressed)
        self.pushButton.released.connect(self.on_shoot_released)

        self.progressBar.setValue(0)
        self.power_timer = QTimer()
        self.power_timer.timeout.connect(self.increase_power)
        self.power_accumulation = 0

    def set_controller(self, controller):
        self.controller = controller
        self.pymunk_widget.mouse_moved.connect(controller.on_mouse_move)
        self.pymunk_widget.mouse_pressed.connect(controller.on_mouse_press)
        self.pymunk_widget.mouse_released.connect(controller.on_mouse_release)
        self.pymunk_widget.lock_toggled.connect(controller.on_toggle_lock)

    def set_model(self, model):
        # Important : on redimensionne le widget selon le modèle
        self.pymunk_widget.w_attr = model.width
        self.pymunk_widget.h_attr = model.height
        self.pymunk_widget.setFixedSize(model.width, model.height)
        self.pymunk_widget.set_model(model)

    def on_reset(self):
        if hasattr(self, 'controller'):
            self.controller.reset_game()

    def on_undo(self):
        if hasattr(self, 'controller'):
            self.controller.undo_shot()

    def on_shoot_pressed(self):
        self.power_accumulation = 0
        self.power_timer.start(50)

    def on_shoot_released(self):
        self.power_timer.stop()
        if hasattr(self, 'controller'):
            self.controller.shoot()
        self.power_accumulation = 0
        self.progressBar.setValue(0)

    def increase_power(self):
        self.power_accumulation = min(100, self.power_accumulation + 4)  # Un peu plus rapide
        self.progressBar.setValue(self.power_accumulation)
        if hasattr(self, 'controller'):
            self.controller.set_power(self.power_accumulation / 100.0)