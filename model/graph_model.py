from PyQt6.QtCore import QModelIndex, Qt, QAbstractListModel


class BallsList(QAbstractListModel):

    def __init__(self):
        super().__init__()

        self.balls_set: set[int] = {0}

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        balls_list = list(self.balls_set)

        if role == Qt.ItemDataRole.DisplayRole:
            return str(f"Balle numéro {balls_list[index.row()]}")
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex) -> int:
        return len(self.balls_set)

    def add_item(self, item):
        self.beginInsertRows(QModelIndex(),self.rowCount(), self.rowCount())
        self.balls_set.add(item)
        self.endInsertRows()

