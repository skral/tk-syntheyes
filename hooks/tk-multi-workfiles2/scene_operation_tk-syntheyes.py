# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


from syntheyes import get_existing_connection
import sgtk

HookClass = sgtk.get_hook_baseclass()


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

    def execute(
        self,
        operation,
        file_path,
        context,
        parent_action,
        file_version,
        read_only,
        **kwargs
    ):
        """
        Main hook entry point
        :param operation:       String
                                Scene operation to perform
        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)
        :param context:         Context
                                The context the file operation is being
                                performed in.
        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up
        :param file_version:    The version/revision of the file to be opened.
                                If this is 'None' then the latest version
                                should be opened.
        :param read_only:       Specifies if the file should be opened
                                read-only or not
        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an
                                                 empty state, otherwise False
                                all others     - None
        """
        app = self.parent

        app.log_debug("-" * 50)
        app.log_debug("operation: %s" % operation)
        app.log_debug("file_path: %s" % file_path)
        app.log_debug("context: %s" % context)
        app.log_debug("parent_action: %s" % parent_action)
        app.log_debug("file_version: %s" % file_version)
        app.log_debug("read_only: %s" % read_only)

        if operation == Operations.CurrentPath:
            # return the current scene path
            return self.__filename()

        elif operation == Operations.Open:
            self.__open(file_path)

        elif operation == Operations.Save:
            self.__save()

        elif operation == Operations.SaveAs:
            self.__save(path=file_path)

        elif operation == Operations.Reset:
            # Propose to save the project if it's modified
            app.log_debug("checking if needing to save...")
            if self.__modified():
                app.log_debug("saving filename: %s" % file_path)
                self.__save()

            app.log_debug("creating new project...")
            self.__open(path="")
            return True

    def __modified(self):
        return self._connection.HasChanged()

    def __filename(self):
        return self._connection.SNIFileName()

    def __open(self, path):
        self._connection.OpenSNI(path)

    def __save(self, path=None):
        self.logger.info(">>>>>>path")
        self.logger.info(path)
        if path is None:
            path = self.__filename()

        self._connection.Begin()
        self._connection.SetSNIFileName(path)
        self._connection.Accept("Save As: %s" % path)
        self._connection.ClickMainMenuAndWait("Save")
