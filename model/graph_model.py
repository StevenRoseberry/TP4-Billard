from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal

class BallsList(QAbstractListModel):
    update_supprimer_push_button = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.balls_set: set[int] = {0}
        self.balls_list: list[int] = sorted(self.balls_set)

    def rowCount(self, parent=QModelIndex()):
        return len(self.balls_list)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole and index.isValid():
            return f"Balle numéro {self.balls_list[index.row()]}"
        return None

    def add_item(self, item: int):
        if item in self.balls_set:
            return

        insert_pos = 0
        for i, val in enumerate(self.balls_list):
            if item < val:
                break
            insert_pos += 1

        self.beginInsertRows(QModelIndex(), insert_pos, insert_pos)

        self.balls_set.add(item)
        self.balls_list.insert(insert_pos, item)

        self.endInsertRows()
        self.update_supprimer_push_button.emit(True)

    def remove_item(self, item: int):
        if item not in self.balls_set:
            return

        row = self.balls_list.index(item)

        self.beginRemoveRows(QModelIndex(), row, row)

        self.balls_list.pop(row)
        self.balls_set.remove(item)

        self.endRemoveRows()
        self.update_supprimer_push_button.emit(len(self.balls_list) > 0)