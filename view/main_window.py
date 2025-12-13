import math
import random
from typing import TYPE_CHECKING, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMainWindow, QSizePolicy, QDockWidget,
    QListView, QPushButton, QSpinBox, QProgressBar, QFrame
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QAction
from PyQt6.uic import loadUi
import pymunk

from model.ball_state import BallState

if TYPE_CHECKING:
    from controller.main_controller import MainController

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

class PymunkWidget(QWidget):
    mouse_moved = pyqtSignal(int, int)
    mouse_pressed = pyqtSignal()
    mouse_released = pyqtSignal()
    lock_toggled = pyqtSignal()

    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.w_attr = width
        self.h_attr = height

        self.setFixedSize(width, height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.setMouseTracking(True)
        self.mouse_pressed_flag = False

        # --- Initialisation Pymunk ---
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.damping = 0.98
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
        self.cue_angle = 0.0
        self.cue_distance = 100

        self.history: List[List[BallState]] = []

        self._create_table()
        self._create_balls()
        self._create_cue_stick()

        # --- Timer Physique & Animation ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(16)

    def _pymunk_to_qt(self, x, y):
        return x, self.height() - y

    def _qt_to_pymunk(self, x, y):
        return x, self.height() - y

    def _create_table(self):
        static_body = self.space.static_body
        thickness = 40
        hole = 120
        half_width = int(self.width() / 2 - hole * 0.75)

        spacer = thickness / 2
        tri_margin = hole - spacer
        mid_tri = half_width + spacer

        # Murs
        self._add_wall((20, hole), (20, self.height() - hole), thickness)
        self._add_wall((self.width() - 20, hole), (self.width() - 20, self.height() - hole), thickness)
        self._add_wall((hole, 20), (half_width, 20), thickness)
        self._add_wall((hole, self.height() - 20), (half_width, self.height() - 20), thickness)
        self._add_wall((self.width() - hole, self.height() - 20),
                       (self.width() - half_width, self.height() - 20), thickness)
        self._add_wall((self.width() - hole, 20), (self.width() - half_width, 20), thickness)

        liste_triangle_rectangle = [
            [(spacer, tri_margin), 1, -1],
            [(spacer, self.height() - tri_margin), 1, 1],
            [(self.width() - spacer, tri_margin), -1, -1],
            [(self.width() - spacer, self.height() - tri_margin), -1, 1],
            [(tri_margin, spacer), -1, 1],
            [(tri_margin, self.height() - spacer), -1, -1],
            [(self.width() - tri_margin, spacer), 1, 1],
            [(self.width() - tri_margin, self.height() - spacer), 1, -1],
            [(mid_tri, self.height() - spacer), 1, -1],
            [(self.width() - mid_tri, self.height() - spacer), -1, -1],
            [(mid_tri, spacer), 1, 1],
            [(self.width() - mid_tri, spacer), -1, 1],
        ]
        self._add_triangle(liste_triangle_rectangle, thickness)

    def _add_triangle(self, list_coords, thickness):
        for coor in list_coords:
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
        self.cue_ball = self._create_single_ball((self.width() // 4, self.height() // 2), 0)

        start_x = self.width() * 0.75
        start_y = self.height() / 2
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
            color_rgb = BALL_COLORS[8]
            is_stripe = False
        else:
            is_stripe = number > 8
            base_index = number if number <= 8 else number - 8
            color_rgb = BALL_COLORS[base_index]

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

    def update_simulation(self):
        steps = 2
        dt = 1 / 60.0
        if not self.is_aiming:
            for _ in range(steps):
                self.space.step(dt / steps)

            if self._all_balls_stopped():
                self.is_aiming = True
                self.cue_locked = False
                self._stop_rotation()

        self.update()

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

    def shoot(self, power_percentage):
        if not self.is_aiming or not self._all_balls_stopped():
            return

        self._save_state()
        force = power_percentage * self.max_power
        impulse_x = force * math.cos(self.cue_angle)
        impulse_y = force * math.sin(self.cue_angle)

        self.cue_ball.body.apply_impulse_at_world_point(
            (impulse_x, impulse_y), self.cue_ball.body.position
        )
        self.is_aiming = False
        self.cue_locked = False

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
        self.history.clear()

    def _save_state(self):
        state = []
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                state.append(BallState(position=tuple(shape.body.position),
                                       velocity=tuple(shape.body.velocity),
                                       angular_velocity=shape.body.angular_velocity))
        self.history.append(state)
        if len(self.history) > 10:
            self.history.pop(0)

    def undo_last_shot(self):
        if not self.history or not self.is_aiming:
            return
        state = self.history.pop()
        balls = [s for s in self.space.shapes if isinstance(s, pymunk.Circle)]
        for i, shape in enumerate(balls):
            if i < len(state):
                b = state[i]
                shape.body.position = b.position
                shape.body.velocity = b.velocity
                shape.body.angular_velocity = b.angular_velocity
                shape.body.activate()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(25, 150, 60))

        if self.space is None:
            return

        self._draw_walls(painter)
        self._draw_balls(painter)

        if self.is_aiming:
            self._draw_aim_line(painter)
            self._draw_cue_stick(painter)

    def _draw_walls(self, painter):
        wall_color = QColor(75, 37, 14)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(wall_color, 40)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        margin = 40
        hole = margin * 3
        half_width = int(self.width() / 2 - hole * 0.75)
        spacer = margin / 2
        tri_margin = hole - spacer
        mid_tri = half_width + spacer

        painter.drawLine(margin, hole, margin, self.height() - hole)
        painter.drawLine(self.width() - margin, hole, self.width() - margin, self.height() - hole)
        painter.drawLine(hole, margin, half_width, margin)
        painter.drawLine(hole, self.height() - margin, half_width, self.height() - margin)
        painter.drawLine(self.width() - hole, margin, self.width() - half_width, margin)
        painter.drawLine(self.width() - hole, self.height() - margin, self.width() - half_width, self.height() - margin)

        painter.setBrush(QBrush(QColor("red")))
        painter.setPen(Qt.PenStyle.NoPen)

        liste_triangle_rectangle = [
            [(spacer, tri_margin), 1, -1], [(spacer, self.height() - tri_margin), 1, 1],
            [(self.width() - spacer, tri_margin), -1, -1],
            [(self.width() - spacer, self.height() - tri_margin), -1, 1],
            [(tri_margin, spacer), -1, 1], [(tri_margin, self.height() - spacer), -1, -1],
            [(self.width() - tri_margin, spacer), 1, 1],
            [(self.width() - tri_margin, self.height() - spacer), 1, -1],
            [(mid_tri, self.height() - spacer), 1, -1], [(self.width() - mid_tri, self.height() - spacer), -1, -1],
            [(mid_tri, spacer), 1, 1], [(self.width() - mid_tri, spacer), -1, 1],
        ]

        for coor in liste_triangle_rectangle:
            tri = [QPointF(coor[0][0], coor[0][1]),
                   QPointF(coor[0][0] + margin * coor[1], coor[0][1]),
                   QPointF(coor[0][0], coor[0][1] + margin * coor[2])]
            painter.drawPolygon(tri)

    def _draw_balls(self, painter):
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos = shape.body.position
                qt_x, qt_y = self._pymunk_to_qt(pos.x, pos.y)
                radius = shape.radius
                color_tuple = getattr(shape, 'color', (255, 255, 255))
                is_stripe = getattr(shape, 'is_stripe', False)
                base_color = QColor(*color_tuple[:3])

                painter.save()
                painter.translate(qt_x, qt_y)
                angle_deg = math.degrees(shape.body.angle)
                painter.rotate(angle_deg)

                path = QPainterPath()
                path.addEllipse(QPointF(0, 0), radius, radius)
                painter.setClipPath(path)

                if is_stripe:
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(0, 0), radius, radius)
                    stripe_height = radius * 1.1
                    painter.setBrush(QBrush(base_color))
                    painter.drawRect(QRectF(-radius, -stripe_height / 2, radius * 2, stripe_height))
                else:
                    painter.setBrush(QBrush(base_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QPointF(0, 0), radius, radius)

                painter.setClipping(False)
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(0, 0), radius, radius)

                painter.rotate(-angle_deg)
                painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(-radius / 3, -radius / 3), radius / 3, radius / 3)
                painter.restore()

    def _draw_cue_stick(self, painter):
        start, end = self._get_cue_position()
        start_qt = self._pymunk_to_qt(start[0], start[1])
        end_qt = self._pymunk_to_qt(end[0], end[1])

        pen = QPen(QColor(160, 82, 45), self.cue_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(start_qt[0]), int(start_qt[1]), int(end_qt[0]), int(end_qt[1]))

    def _draw_aim_line(self, painter):
        ball_pos = self.cue_ball.body.position
        ball_qt = self._pymunk_to_qt(ball_pos.x, ball_pos.y)

        end_x = ball_pos.x + 200 * math.cos(self.cue_angle)
        end_y = ball_pos.y + 200 * math.sin(self.cue_angle)
        end_qt = self._pymunk_to_qt(end_x, end_y)

        color = QColor(255, 0, 0, 200) if self.cue_locked else QColor(255, 255, 255, 150)
        pen = QPen(color, 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(ball_qt[0]), int(ball_qt[1]), int(end_qt[0]), int(end_qt[1]))

    def _get_cue_position(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        ball_pos = self.cue_ball.body.position
        start_x = ball_pos.x - (self.ball_radius + self.cue_distance) * math.cos(self.cue_angle)
        start_y = ball_pos.y - (self.ball_radius + self.cue_distance) * math.sin(self.cue_angle)
        end_x = start_x - self.cue_length * math.cos(self.cue_angle)
        end_y = start_y - self.cue_length * math.sin(self.cue_angle)
        return (start_x, start_y), (end_x, end_y)

    def mouseMoveEvent(self, event):
        qt_x = event.pos().x()
        qt_y = event.pos().y()
        pymunk_x, pymunk_y = self._qt_to_pymunk(qt_x, qt_y)

        if self.is_aiming and not self.cue_locked and self.cue_ball:
            dx = pymunk_x - self.cue_ball.body.position.x
            dy = pymunk_y - self.cue_ball.body.position.y
            self.cue_angle = math.atan2(dy, dx)
            self.update()

        self.mouse_moved.emit(int(pymunk_x), int(pymunk_y))
        if self.mouse_pressed_flag:
            self.mouse_pressed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = True
            self.mouse_pressed.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            if self.is_aiming:
                self.cue_locked = not self.cue_locked
                self.update()
            self.lock_toggled.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = False
            self.mouse_released.emit()


class MainWindow(QMainWindow):
    # Annotations de type pour les widgets chargés via loadUi
    actionAfficher_graphiques: QAction
    dockWidget: QDockWidget
    listView: QListView
    ajouterPushButton: QPushButton
    balleSpinBox: QSpinBox
    supprimerPushButton: QPushButton
    toutAjouterPushButton: QPushButton
    toutSupprimerPushButton: QPushButton
    progressBar: QProgressBar
    pushButton: QPushButton
    createButton: QPushButton
    deleteButton: QPushButton
    graphFrame: QFrame

    # Annotation de type pour le contrôleur (peut être None au départ)
    __controller: Optional['MainController'] = None

    def __init__(self):
        super().__init__()
        loadUi('view/ui/main_window.ui', self)

        self.pymunk_widget = PymunkWidget(1200, 600)

        existing_layout = self.graphFrame.layout()
        if existing_layout is not None:
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            existing_layout.addWidget(self.pymunk_widget)
            existing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            layout = QVBoxLayout()
            layout.addWidget(self.pymunk_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.graphFrame.setLayout(layout)

        self.pushButton.pressed.connect(self.on_shoot_pressed)
        self.pushButton.released.connect(self.on_shoot_released)

        self.progressBar.setValue(0)
        self.power_timer = QTimer()
        self.power_timer.timeout.connect(self.increase_power)
        self.power_accumulation = 0

        self.actionAfficher_graphiques.toggled.connect(self.dock_widget_visibility)
        self.dockWidget.visibilityChanged.connect(self.uncheck_action)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            # Vérification de sécurité avant d'utiliser le contrôleur
            if self.__controller:
                self.__controller.supprimer_balle_liste()

    def set_controller(self, controller: 'MainController'):
        self.__controller = controller

    def on_shoot_pressed(self):
        self.power_accumulation = 0
        self.power_timer.start(50)

    def on_shoot_released(self):
        self.power_timer.stop()
        # Vérification de sécurité
        if self.__controller:
            self.__controller.shoot()
        self.power_accumulation = 0
        self.progressBar.setValue(0)

    def increase_power(self):
        self.power_accumulation = min(100, self.power_accumulation + 4)
        self.progressBar.setValue(self.power_accumulation)

    def dock_widget_visibility(self):
        self.dockWidget.setVisible(self.actionAfficher_graphiques.isChecked())

    def uncheck_action(self, visible):
        self.actionAfficher_graphiques.setChecked(self.dockWidget.isVisible())

    def update_spin_box(self, _):
        index = self.listView.currentIndex()
        if not index.isValid():
            return
        text = index.data(Qt.ItemDataRole.DisplayRole)
        try:
            # Utilisation safe de split et conversion
            number = int(text.split()[-1])
            self.balleSpinBox.setValue(number)
        except (ValueError, IndexError):
            pass