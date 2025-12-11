import math
from PyQt6.QtCore import QTimer

class MainController:
    def __init__(self, model, view):
        self.__model = model
        self.__view = view

        # initialisation de la ListView
        self.__view.listView.setModel(self.__model.getListModel())

        # interaction avec la listView
        self.__view.listView.selectionModel().selectionChanged.connect(self.__view.update_spin_box)

        self.physics_timer = QTimer()
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16)

        #Todo : Steven faut qu'on parle de ça la vue n'est pas supposé connaitre le model directement
        self.__view.set_model(model)

        #connection de tout les élément Qt de la MainWindow
        self.__view.createButton.clicked.connect(self.__model.reset)
        self.__view.deleteButton.clicked.connect(self.__model.undo_last_shot)

        #Todo : stocker les éléments pymunk dans le model
        # self.__view.pushButton.pressed.connect(self.__view.on_shoot_pressed)
        # self.__view.pushButton.released.connect(self.__view.on_shoot_released)

        #Todo :fix this
        # self.__view.progressBar.setValue(0)
        # self.__view.power_timer = QTimer()
        # self.__view.power_timer.timeout.connect(self.increase_power)
        # self.__view.power_accumulation = 0



        #dockWidget
        self.__view.ajouterPushButton.clicked.connect(self.ajouter_balle_liste)
        self.__view.supprimerPushButton.clicked.connect(self.supprimer_balle_liste)

    def update_physics(self):
        self.__model.update(1 / 60.0)

    def on_mouse_move(self, x: int, y: int):
        # Si verrouillé ou pas en mode visée, est "locked"
        if not self.__model.is_aiming or self.__model.cue_locked:
            return

        ball_pos = self.__model.cue_ball.body.position
        dx = x - ball_pos.x
        dy = y - ball_pos.y
        angle = math.atan2(dy, dx)
        self.__model.set_cue_angle(angle)

    def on_mouse_press(self):
        pass

    def on_mouse_release(self):
        pass

    def on_toggle_lock(self):
        self.__model.toggle_cue_lock()

    def set_power(self, power: float):
        self.__model.set_power(power)

    def shoot(self):
        self.__model.shoot()

    def ajouter_balle_liste(self):
        self.__model.ajouter_balle_liste(self.__view.balleSpinBox.value())

    def supprimer_balle_liste(self):
        self.__model.supprimer_balle_liste(self.__view.balleSpinBox.value())
