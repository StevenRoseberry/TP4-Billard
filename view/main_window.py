import sys
import math
import traceback
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QPainterPath
from PyQt6.uic import loadUi

if TYPE_CHECKING:
    from controller.main_controller import MainController


class PymunkWidget(QWidget):
    mouse_moved = pyqtSignal(int, int)
    mouse_pressed = pyqtSignal()
    mouse_released = pyqtSignal()
    lock_toggled = pyqtSignal()

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.w_attr, self.h_attr = width, height
        # On fixe la taille pour éviter les calculs de redimensionnement constants
        self.setFixedSize(width, height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # 60 FPS

        self.space = None
        self.model = None

        # Dessin du mur stocké ici, pour éviter le générer 60 fois par seconde
        self.cached_wall_path = None

        self.setMouseTracking(True)
        self.mouse_pressed_flag = False

    def set_model(self, model):
        self.model = model
        self.space = model.space
        # Une fois le modèle connu, le mur est calculé UNE SEULE FOIS
        self._precalculate_walls()

    def _pymunk_to_qt(self, x, y):
        return (x, self.height() - y)

    def _qt_to_pymunk(self, x, y):
        return (x, self.height() - y)

    def _precalculate_walls(self):
        # Calcule le mur
        if not self.model: return

        path = QPainterPath()
        m = self.model.table.margin

        # Grand rectangle (Bois extérieur)
        outer = QRectF(m - 20, m - 20, self.width() - 2 * m + 40, self.height() - 2 * m + 40)
        path.addRect(outer)

        # Soustraire le rectangle intérieur (Tapis)
        inner = QRectF(m + 20, m + 20, self.width() - 2 * m - 40, self.height() - 2 * m - 40)
        path_inner = QPainterPath()
        path_inner.addRect(inner)
        path = path.subtracted(path_inner)

        # Soustraire les trous
        for px, py in self.model.table.pockets:
            qt_x, qt_y = self._pymunk_to_qt(px, py)
            path_hole = QPainterPath()
            r = self.model.table.pocket_radius
            path_hole.addEllipse(QPointF(qt_x, qt_y), r, r)
            path = path.subtracted(path_hole)

        self.cached_wall_path = path

    def paintEvent(self, event):
        try:
            # Sécurité pour éviter crash
            if self.space is None or self.model is None: return

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Tapis
            painter.fillRect(self.rect(), QColor(34, 139, 34))

            # Trous (Fond noir)
            self._draw_pockets(painter)

            # Murs
            self._draw_walls(painter)

            # Balles
            self._draw_balls(painter)

            # 5. Queue
            if self.model.is_aiming:
                self._draw_aim_line(painter)
                self._draw_cue_stick(painter)

        except Exception as e:
            # Évite crash
            print(f"Erreur rendu: {e}")
            traceback.print_exc()

    def _draw_pockets(self, p):
        p.setBrush(QBrush(QColor(0, 0, 0)));
        p.setPen(Qt.PenStyle.NoPen)
        for px, py in self.model.table.pockets:
            qt_x, qt_y = self._pymunk_to_qt(px, py)
            r = self.model.table.pocket_radius
            p.drawEllipse(QPointF(qt_x, qt_y), r, r)

    def _draw_walls(self, p):
        # Chemin pré-calculé
        if self.cached_wall_path:
            p.setBrush(QBrush(QColor(139, 69, 19)))
            p.setPen(QPen(QColor(100, 50, 10), 2))
            p.drawPath(self.cached_wall_path)

    def _draw_balls(self, p):
        if not hasattr(self.model, 'balls'): return

        for ball in self.model.balls:
            # Évite les crashs
            if not ball.body: continue

            pos = ball.body.position
            qt_x, qt_y = self._pymunk_to_qt(pos.x, pos.y)
            r = ball.radius

            p.save()
            p.translate(qt_x, qt_y)
            p.rotate(math.degrees(ball.body.angle))

            # Clipping
            path = QPainterPath();
            path.addEllipse(QPointF(0, 0), r, r)
            p.setClipPath(path)

            # Fond
            p.setBrush(QBrush(QColor(255, 255, 255)));
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(0, 0), r, r)

            base_color = QColor(*ball.color_rgb)
            if ball.is_stripe:
                p.setBrush(QBrush(base_color))
                stripe_h = r * 1.1
                p.drawRect(QRectF(-r, -stripe_h / 2, r * 2, stripe_h))
            else:
                p.setBrush(QBrush(base_color))
                p.drawEllipse(QPointF(0, 0), r, r)

            p.setClipping(False)

            # Contour et Reflet
            p.setPen(QPen(QColor(50, 50, 50), 1));
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(0, 0), r, r)

            p.rotate(-math.degrees(ball.body.angle))
            p.setBrush(QBrush(QColor(255, 255, 255, 80)));
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(-r / 3, -r / 3), r / 3, r / 3)

            p.restore()

    def _draw_cue_stick(self, p):
        if not self.model.cue_ball: return
        s, e = self.model.cue.get_render_coords(self.model.cue_ball.body.position, self.model.cue_ball.radius)
        sq, eq = self._pymunk_to_qt(*s), self._pymunk_to_qt(*e)
        pen = QPen(QColor(160, 82, 45), self.model.cue.width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(int(sq[0]), int(sq[1]), int(eq[0]), int(eq[1]))

    def _draw_aim_line(self, p):
        ball = self.model.cue_ball.body.position
        bq = self._pymunk_to_qt(ball.x, ball.y)
        angle = self.model.cue.angle
        ex = ball.x + 200 * math.cos(angle)
        ey = ball.y + 200 * math.sin(angle)
        eq = self._pymunk_to_qt(ex, ey)
        color = QColor(255, 0, 0, 200) if self.model.cue.locked else QColor(255, 255, 255, 150)
        pen = QPen(color, 2);
        pen.setStyle(Qt.PenStyle.DashLine);
        p.setPen(pen)
        p.drawLine(int(bq[0]), int(bq[1]), int(eq[0]), int(eq[1]))

    def mouseMoveEvent(self, e):
        qx, qy = e.pos().x(), e.pos().y()
        px, py = self._qt_to_pymunk(qx, qy)
        self.mouse_moved.emit(int(px), int(py))
        if self.mouse_pressed_flag: self.mouse_pressed.emit()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_flag = True; self.mouse_pressed.emit()
        elif e.button() == Qt.MouseButton.RightButton:
            self.lock_toggled.emit()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.mouse_pressed_flag = False; self.mouse_released.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('view/ui/main_window.ui', self)

        self.pymunk_widget = PymunkWidget(1200, 600)

        layout = self.graphFrame.layout()
        if layout is None:
            layout = QVBoxLayout()
            self.graphFrame.setLayout(layout)

        # Nettoyage du layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout.addWidget(self.pymunk_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.createButton.clicked.connect(self.on_reset)
        self.deleteButton.clicked.connect(self.on_undo)
        self.pushButton.pressed.connect(self.on_shoot_pressed)
        self.pushButton.released.connect(self.on_shoot_released)
        self.progressBar.setValue(0)
        self.power_timer = QTimer();
        self.power_timer.timeout.connect(self.increase_power);
        self.power_accumulation = 0

    def set_controller(self, c):
        self.controller = c
        self.pymunk_widget.mouse_moved.connect(c.on_mouse_move)
        self.pymunk_widget.mouse_pressed.connect(c.on_mouse_press)
        self.pymunk_widget.mouse_released.connect(c.on_mouse_release)
        self.pymunk_widget.lock_toggled.connect(c.on_toggle_lock)

    def set_model(self, m):
        self.pymunk_widget.w_attr, self.pymunk_widget.h_attr = m.width, m.height
        self.pymunk_widget.setFixedSize(m.width, m.height)
        self.pymunk_widget.set_model(m)

    def on_reset(self):
        self.controller.reset_game() if hasattr(self, 'controller') else None

    def on_undo(self):
        self.controller.undo_shot() if hasattr(self, 'controller') else None

    def on_shoot_pressed(self):
        self.power_accumulation = 0; self.power_timer.start(50)

    def on_shoot_released(self):
        self.power_timer.stop()
        if hasattr(self, 'controller'): self.controller.shoot()
        self.power_accumulation = 0;
        self.progressBar.setValue(0)

    def increase_power(self):
        self.power_accumulation = min(100, self.power_accumulation + 4)
        self.progressBar.setValue(self.power_accumulation)
        if hasattr(self, 'controller'): self.controller.set_power(self.power_accumulation / 100.0)