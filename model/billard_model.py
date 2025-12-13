from PyQt6.QtCore import QObject
from model.graph_model import BallsList

class BillardModel(QObject):
    # initialisation du QAbstractItemModel
    tracked_balls_list = BallsList()

    def __init__(self, width: int = 1200, height: int = 600):
        super().__init__()
        # Le modèle ne s'occupe plus de pymunk ou presque pu
        pass

    """Graph et liste de balle"""

    def add_ball(self, number):
        self.tracked_balls_list.add_item(number)

    def getListModel(self):
        return self.tracked_balls_list

    def ajouter_balle_liste(self, balle):
        if balle is not None:
            self.tracked_balls_list.add_item(balle)

    def supprimer_balle_liste(self, balle):
        if balle is not None and self.tracked_balls_list.rowCount() > 0:
            self.tracked_balls_list.remove_item(balle)