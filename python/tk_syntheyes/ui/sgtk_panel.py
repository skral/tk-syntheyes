from PySide import QtCore, QtGui


class Ui_SgtkPanel(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Ui_SgtkPanel, self).__init__(parent)

        self.setMinimumSize(200, 200)
        self.setWindowTitle("SGTK Panel")
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.buttons = []

    def add_button(self, name, command):
        button = QtGui.QPushButton(name, self)
        button.clicked.connect(command)
        self.buttons.append(button)
        self.layout.addWidget(button)

    def delete_button(self, index):
        b = self.layout.takeAt(index)
        self.buttons.pop(index)
        b.widget().deleteLater()

    def clear_panel(self):
        count = len(self.buttons)
        for index in reversed(range(count)):
            self.delete_button(index)

    def destroy_panel(self):
        self.deleteLater()
