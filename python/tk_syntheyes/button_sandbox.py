from PySide import QtGui, QtCore
import sys


class Main(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Main, self).__init__(parent)
        layout = self.layout()
        button = QtGui.QPushButton('panel', self)
        layout.addWidget(button)
        button.clicked.connect(self.create_panel)

    def create_panel(self):
        # layout.addWidget(button)
        # layout = QtGui.QVBoxLayout(self)
        self.ui = Ui_SgtkPanel(self)
        # layout.addWidget(self.ui)
        buttons = [('test1', test1), ('clear', self.ui.clear_panel), ('destroy', self.ui.destroy_panel)]
        for button in buttons:
            self.ui.add_button(*button)
        # layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.ui.raise_()
        self.ui.activateWindow()
        self.ui.show()

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

def test1():
    print 'test1'

def test2():
    print 'test2'


class Test(QtGui.QWidget):
  def __init__( self, parent=None):
      super(Test, self).__init__(parent)

      self.pushButton = QtGui.QPushButton('I am in Test widget')

      layout = QtGui.QHBoxLayout()
      layout.addWidget(self.pushButton)
      self.setLayout(layout)


app = QtGui.QApplication(sys.argv)
myWidget = Main()
myWidget.show()
sys.exit(app.exec_())
