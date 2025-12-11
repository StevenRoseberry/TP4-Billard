import sys
import math
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QSizePolicy, QDockWidget, QListView, QPushButton, \
    QSpinBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QPainterPath, QAction
from PyQt6.uic import loadUi
import pymunk

if TYPE_CHECKING:
    from controller.main_controller import MainController


class PymunkWidget(QWidget):
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

        self.setFixedSize(width, height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

        self.space = None
        self.model = None

        self.setMouseTracking(True)
        self.mouse_pressed_flag = False

    def set_controller(self, controller):
        self.controller = controller

    def set_model(self, model):
        self.model = model
        self.space = model.space

    def _pymunk_to_qt(self, x, y):
        return (x, self.height() - y)

    def _qt_to_pymunk(self, x, y):
        return (x, self.height() - y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # COULEUR DU TAPIS DE JEU
        painter.fillRect(self.rect(), QColor(25, 150, 60))

        if self.space is None:
            return

        self._draw_walls(painter)
        self._draw_balls(painter)

        if self.model and self.model.is_aiming:
            self._draw_aim_line(painter)
            self._draw_cue_stick(painter)

    def _draw_walls(self, painter):
        wall_color = QColor(75, 37, 14)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen_width = 40
        pen = QPen(wall_color, pen_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        margin = 40
        painter.drawRect(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)


    # Gemini a ici fait les balles lignées
    def _draw_balls(self, painter):
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos = shape.body.position
                qt_x, qt_y = self._pymunk_to_qt(pos.x, pos.y)
                radius = shape.radius

                color_tuple = getattr(shape, 'color', (255, 255, 255))
                is_stripe = getattr(shape, 'is_stripe', False)
                base_color = QColor(*color_tuple)

                # Sauvegarde l'état du peintre pour appliquer la rotation locale
                painter.save()

                # 1. Déplacement au centre de la balle
                painter.translate(qt_x, qt_y)

                # 2. Rotation selon la physique (la balle tourne visuellement !)
                angle_deg = math.degrees(shape.body.angle)
                painter.rotate(angle_deg)

                # Création du cercle de découpe (pour ne pas dessiner hors de la balle)
                path = QPainterPath()
                path.addEllipse(QPointF(0, 0), radius, radius)
                painter.setClipPath(path)

                if is_stripe:
                    # Fond BLANC
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(0, 0), radius, radius)

                    # Bande COLORÉE au milieu
                    # On dessine un rectangle large au centre
                    stripe_height = radius * 1.1  # Épaisseur de la rayure
                    painter.setBrush(QBrush(base_color))
                    painter.drawRect(QRectF(-radius, -stripe_height / 2, radius * 2, stripe_height))
                else:
                    # Balle PLEINE
                    painter.setBrush(QBrush(base_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(0, 0), radius, radius)

                # On désactive le clipping pour dessiner le contour proprement
                painter.setClipping(False)

                # Contour
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(0, 0), radius, radius)

                # Reflet (Speculaire)
                # On annule la rotation pour que la lumière vienne toujours du même endroit (en haut à gauche)
                painter.rotate(-angle_deg)

                painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(-radius / 3, -radius / 3), radius / 3, radius / 3)

                painter.restore()

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



########################################################################



class MainWindow(QMainWindow):

    #déclaration des éléments Qt du DockWidget

    actionAfficher_graphiques = QAction
    dockWidget = QDockWidget
    listView = QListView
    ajouterPushButton = QPushButton
    balleSpinBox = QSpinBox
    supprimerPushButton = QPushButton

    def __init__(self):
        super().__init__()
        loadUi('view/ui/main_window.ui', self)

        self.pymunk_widget = PymunkWidget(1200, 600)

        existing_layout = self.graphFrame.layout()
        if existing_layout is not None:
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()
            existing_layout.addWidget(self.pymunk_widget)
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

        #DockWidget et graph
        self.actionAfficher_graphiques.toggled.connect(self.dock_widget_visibility)
        self.dockWidget.visibilityChanged.connect(self.uncheck_action)
        # self.ajouterPushButton.clicked.connect(self.ajou)

    def set_controller(self, controller):
        self.controller = controller
        self.pymunk_widget.mouse_moved.connect(controller.on_mouse_move)
        self.pymunk_widget.mouse_pressed.connect(controller.on_mouse_press)
        self.pymunk_widget.mouse_released.connect(controller.on_mouse_release)
        self.pymunk_widget.lock_toggled.connect(controller.on_toggle_lock)
        #initialisation de la ListView
        self.listView.setModel(self.controller.getListModel())

    def set_model(self, model):
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
        self.power_accumulation = min(100, self.power_accumulation + 4)
        self.progressBar.setValue(self.power_accumulation)
        if hasattr(self, 'controller'):
            self.controller.set_power(self.power_accumulation / 100.0)

    """Les deux méthodes ci-dessous servent à toggle le dockWidget"""

    def dock_widget_visibility(self):
        self.dockWidget.setVisible(self.actionAfficher_graphiques.isChecked())

    def uncheck_action(self,visible):
        if not visible:
            self.actionAfficher_graphiques.setChecked(visible)

