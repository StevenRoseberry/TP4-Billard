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

    """Comment avoir une structure cmv réussite
    
        1 : stocker TOUTES les données (dimentions, pourcentage, force, dernier coup) dans le modèle
        
        2 : pour accéder à une donné du modèle à partir de la vue, passer par le controller qui communique avec le model
        
        3 : pour passer une donné du model jusqu'à la vue (exemple : update l'image) utiliser un signal que le controleur récupère et donne à la vue
        
        4 : Pour connecter un élément du Ui qui est à la foie dans la vue et dans le modèle, connecter le signal dans le controler
        4.1 : Ensuite, il faut update le model en premier. Finalement, envoyer un signal depuis le model pour update la vue
        
        Bonne nouvelle!!!!!!! Julien a dit qu'on est pas obliger de séparer la physique du jeu du modele alors le pymunk peut être entièrement dans la vue
        il fait ca pour nous simplifier la vie
        """
