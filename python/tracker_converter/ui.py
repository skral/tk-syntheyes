import logging

from qt import QtWidgets, QtGui, QtCore

_logger = logging.getLogger()


class TrackerConvertDialog(QtWidgets.QWidget):
    def __init__(self, logger=None, parent=None):
        super(TrackerConvertDialog, self).__init__(parent)
        self.logger = logger or _logger

        self.title = "Tracker Converter"

        self.buttons = QtWidgets.QWidget()
        self.source_browser = QtWidgets.QWidget()
        self.dest_browser = QtWidgets.QWidget()

        self.se_to_equalizer_label = None
        self.equalizer_to_se_label = None

        self.se_to_equalizer_check_box = None
        self.equalizer_to_se_check_box = None

        self.source_file_label = None
        self.dest_file_label = None

        self.source_file_text_box = None
        self.dest_file_text_box = None

        self.source_file_browse_button = None
        self.dest_file_browse_button = None
        self.convert_button = None

        self.check_box_group = None

        self.source_file = None
        self.dest_file = None

        self.setLayout(QtWidgets.QGridLayout())

        self.buildUI()

    def buildUI(self):
        self.setWindowTitle(self.title)

        self.se_to_equalizer_label = QtWidgets.QLabel()
        self.se_to_equalizer_label.setText("SynthEyes to 3DEqualizer")
        self.equalizer_to_se_label = QtWidgets.QLabel()
        self.equalizer_to_se_label.setText("3DEqualizer to SynthEyes")

        self.se_to_equalizer_check_box = QtWidgets.QCheckBox()
        self.equalizer_to_se_check_box = QtWidgets.QCheckBox()

        self.source_file_label = QtWidgets.QLabel("Source file")
        self.dest_file_label = QtWidgets.QLabel("Destination file")

        self.source_file_text_box = QtWidgets.QLineEdit()
        self.dest_file_text_box = QtWidgets.QLineEdit()

        self.source_file_browse_button = QtWidgets.QPushButton("Browse")
        self.dest_file_browse_button = QtWidgets.QPushButton("Browse")
        self.convert_button = QtWidgets.QPushButton("Convert")

        se_to_equalizer_layout = QtWidgets.QHBoxLayout()
        se_to_equalizer_layout.addWidget(self.se_to_equalizer_label)
        se_to_equalizer_layout.addWidget(self.se_to_equalizer_check_box)

        equalizer_to_se_layout = QtWidgets.QHBoxLayout()
        equalizer_to_se_layout.addWidget(self.equalizer_to_se_label)
        equalizer_to_se_layout.addWidget(self.equalizer_to_se_check_box)

        self.layout().addLayout(se_to_equalizer_layout, 0, 0)
        self.layout().addLayout(equalizer_to_se_layout, 0, 1)

        browse_file_layout = QtWidgets.QGridLayout()
        browse_file_layout.addWidget(self.source_file_label, 0, 0)
        browse_file_layout.addWidget(self.source_file_text_box, 0, 1)
        browse_file_layout.addWidget(self.source_file_browse_button, 0, 2)
        browse_file_layout.addWidget(self.dest_file_label, 1, 0)
        browse_file_layout.addWidget(self.dest_file_text_box, 1, 1)
        browse_file_layout.addWidget(self.dest_file_browse_button, 1, 2)

        self.layout().addLayout(browse_file_layout, 1, 0, 2, 2)

        self.layout().addWidget(self.convert_button, 3, 0, 1, 2)

        self.check_box_group = QtWidgets.QButtonGroup()

        self.check_box_group.addButton(self.se_to_equalizer_check_box)
        self.check_box_group.addButton(self.equalizer_to_se_check_box)

        self.source_file_text_box.setReadOnly(True)
        source_file_palette = self.source_file_text_box.palette()
        source_file_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.gray)
        self.source_file_text_box.setPalette(source_file_palette)

        self.dest_file_text_box.setReadOnly(True)
        dest_file_palette = self.dest_file_text_box.palette()
        dest_file_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.gray)
        self.dest_file_text_box.setPalette(dest_file_palette)

        self.source_file_browse_button.clicked.connect(self._handle_source_file_browse_button_clicked)
        self.dest_file_browse_button.clicked.connect(self._handle_dest_file_browse_button_clicked)
        self.convert_button.clicked.connect(self._handle_convert_button_clicked)
        # You want to build a fairly simple window: two exclusive buttons (radio?) at the top, a file browser in the
        # middle, and something that'll let you create a file at the bottom. The program should start with a button
        # selected. This button should determine what filters are applied to the file browsers.

    @QtCore.Slot()
    def _handle_source_file_browse_button_clicked(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setViewMode(QtWidgets.QFileDialog.Detail)

        file_dialog.exec_()

        selected_files = file_dialog.selectedFiles()

        if not selected_files:
            # no selection was made; most likely because the operation was cancelled.
            pass
        elif len(selected_files) > 1:
            self._show_error_message("Only one file can be selected at a time.")
        else:
            selected_file = file_dialog.selectedFiles()[0]

            self.source_file_text_box.setText(selected_file)
            self.source_file = selected_file

    @QtCore.Slot()
    def _handle_dest_file_browse_button_clicked(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setViewMode(QtWidgets.QFileDialog.Detail)

        file_dialog.exec_()

        selected_files = file_dialog.selectedFiles()

        if not selected_files:
            # no selection was made; most likely because the operation was cancelled.
            pass
        elif len(selected_files) > 1:
            self._show_error_message("Only one file can be selected at a time.")
        else:
            selected_file = file_dialog.selectedFiles()[0]

            self.dest_file_text_box.setText(selected_file)
            self.dest_file = selected_file

    @QtCore.Slot()
    def _handle_convert_button_clicked(self):
        if not self.se_to_equalizer_check_box.isChecked() and not self.equalizer_to_se_check_box.isChecked():
            self._show_error_message("No conversion type has been selected.")
        elif self.source_file is None:
            self._show_error_message("No source file has been selected.")
        elif self.dest_file is None:
            self._show_error_message("No destination file has been selected.")
        else:
            # TODO: at this point, you have your conversion direction, the file you're converting, and the location
            #       of the file you'll be creating. Convert them, and you're done.
            pass



    @staticmethod
    def _show_error_message(error_text):
        error_message = QtWidgets.QMessageBox()
        error_message.setIcon(QtWidgets.QMessageBox.Critical)
        error_message.setWindowTitle("Error")
        error_message.setText("An error has occurred.")
        error_message.setInformativeText(error_text)
        error_message.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QtGui.QIcon("/mnt/Profiles/jharvey@trackvfx.local/Downloads/UD-pipeline-icon.png"))

    dialog = TrackerConvertDialog()
    dialog.show()

    app.exec_()
