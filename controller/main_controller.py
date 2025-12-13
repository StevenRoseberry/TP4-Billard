class MainController:
    def __init__(self, model, view):
        self.__model = model
        self.__view = view

        # initialisation de la ListView
        self.__view.listView.setModel(self.__model.getListModel())

        # interaction avec la listView
        self.__view.listView.selectionModel().selectionChanged.connect(self.__view.update_spin_box)

        # connection de tout les élément Qt de la MainWindow
        # Les actions physiques (reset, undo) sont redirigées directement vers le widget pymunk
        self.__view.createButton.clicked.connect(self.__view.pymunk_widget.reset)
        self.__view.deleteButton.clicked.connect(self.__view.pymunk_widget.undo_last_shot)

        # dockWidget
        self.__view.ajouterPushButton.clicked.connect(self.ajouter_balle_liste)
        self.__view.supprimerPushButton.clicked.connect(self.supprimer_balle_liste)

    def shoot(self):
        # Récupère la puissance de la vue et déclenche le tir dans le widget
        power = self.__view.progressBar.value() / 100.0
        self.__view.pymunk_widget.shoot(power)

    # Note: les méthodes sont gérés par PymunkWidget, je les laisse ici au cas-où

    def on_mouse_move(self, x: int, y: int):
        pass

    def on_mouse_press(self):
        pass

    def on_mouse_release(self):
        pass

    def on_toggle_lock(self):
        pass

    def ajouter_balle_liste(self):
        self.__model.ajouter_balle_liste(self.__view.balleSpinBox.value())

    def supprimer_balle_liste(self):
        self.__model.supprimer_balle_liste(self.__view.balleSpinBox.value())