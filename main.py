
import sys
from PyQt6.QtWidgets import QApplication
from model.billard_model import BillardModel
from view.main_window import MainWindow
from controller.main_controller import MainController


def main():
    app = QApplication(sys.argv)

    # Créer le modèle
    model = BillardModel(width=1200, height=500)

    # Créer la vue
    view = MainWindow()
    view.setWindowTitle("Billard - Pymunk + QPainter")

    # Créer le contrôleur
    controller = MainController(model, view)

    # Afficher la fenêtre
    view.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()