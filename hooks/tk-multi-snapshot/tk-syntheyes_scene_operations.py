# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank import Hook
from tank import TankError

from syntheyes import get_existing_connection

HookClass = tank.get_hook_baseclass()


class Operations(object):
    CurrentPath = "current_path"
    Open = "open"
    Save = "save"
    SaveAs = "save_as"
    Reset = "reset"


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
    """
    def __init__(self, *args, **kwargs):
        super(SceneOperation, self).__init__(*args, **kwargs)
        self._connection = get_existing_connection()

    def execute(self, operation, file_path, **kwargs):
        """
        Main hook entry point

        :operation: String
                    Scene operation to perform

        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)

        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        app = self.parent

        app.log_debug("-" * 50)
        app.log_debug("operation: %s" % operation)
        app.log_debug("file_path: %s" % file_path)

        if operation == Operations.CurrentPath:
            # return the current scene path
            return self.__filename()

        elif operation == Operations.Open:
            self.__open(file_path)

        elif operation == Operations.Save:
            self.__save()

    def __modified(self):
        return self._connection.HasChanged()

    def __filename(self):
        return self._connection.SNIFileName()

    def __open(self, path):
        self._connection.OpenSNI(path)

    def __save(self, path=None):
        if path is None:
            path = self.__filename()

        self._connection.Begin()
        self._connection.SetSNIFileName(path)
        self._connection.Accept("Save As: %s" % path)
        self._connection.ClickMainMenuAndWait("Save")
