import sys
from PyQt6.QtWidgets import QApplication
# Les imports doivent pointer vers le dossier model/
from model.billard_model import BillardModel
from view.main_window import MainWindow
from controller.main_controller import MainController

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Création du modèle principal
    model = BillardModel(width=1200, height=600)

    # Création de la vue
    view = MainWindow()
    view.setWindowTitle("Billard - Pymunk")

    # Création du contrôleur
    controller = MainController(model, view)
    view.set_controller(controller)

    view.show()
    sys.exit(app.exec())