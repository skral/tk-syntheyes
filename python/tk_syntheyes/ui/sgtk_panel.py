# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights
# not expressly granted therein are reserved by Sebastian Kral.

from PySide import QtCore
from PySide import QtGui


class Ui_SgtkPanel(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Ui_SgtkPanel, self).__init__(parent)

        self.setMinimumSize(200, 200)
        self.setWindowTitle("SGTK Panel")
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.buttons = []

        # load up previous position
        self.settings = QtCore.QSettings("Shotgun Software", "tk-syntheyes.sgtk_panel")
        pos = self.settings.value("pos")
        if pos:
            self.move(pos)

    def closeEvent(self, event):
        self.settings.setValue("pos", self.pos())
        event.accept()

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
