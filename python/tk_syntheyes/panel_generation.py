# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights not expressly granted therein are
# reserved by Sebastian Kral.

"""
Panel handling for SynthEyes
"""
import os
import sys
import webbrowser
import unicodedata


class PanelGenerator(object):
    """
    Panel generation functionality for SynthEyes
    """
    def __init__(self, engine):
        self._engine = engine
        self._dialogs = []
        self._ui = self._engine.ui
        # engine_root_dir = self._engine.disk_location

    ############################################################################
    # public methods

    def populate_panel(self):
        """
        Render the entire Toolkit panel.
        """
        # slight hack here but first ensure that the panel is empty
        self._ui.clear_panel()

        # now add the context item on top of the main panel
        self._add_context_buttons()

        # now enumerate all items and create panel objects for them
        panel_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            panel_items.append(AppCommand(cmd_name, cmd_details))

        self._engine.log_debug("panel_items: %s", panel_items)

        # now go through all of the panel items.
        # separate them out into various sections
        commands_by_app = {}

        for cmd in panel_items:
            if cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_button()
            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items"
                if app_name not in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        # now add all apps to main panel
        self._add_app_buttons(commands_by_app)

    def destroy_panel(self):
        self._ui.destroy_panel()

    ############################################################################
    # context panel and UI
    def _add_context_buttons(self):
        """
        Adds a context panel which displays the current context
        """

        # todo: display context on menu (requires sgtk core 0.12.7+)

        # create the panel object
        self._ui.add_button("Jump to Shotgun", self._jump_to_sg)
        self._ui.add_button("Jump to File System", self._jump_to_fs)
        self._ui.add_button("Show Log", self._handle_show_log)

    def _handle_show_log(self):
        from sgtk.platform.qt import QtCore
        app = QtCore.QCoreApplication.instance()
        win = app.property('tk-syntheyes.log_console')
        win.setHidden(False)
        win.activateWindow()
        win.raise_()

    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        url = self._engine.context.shotgun_url
        webbrowser.open(url, autoraise=True)

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)

    ############################################################################
    # app panels
    def _add_app_buttons(self, commands_by_app):
        """
        Add all apps to the main panel, process them one by one.
        """
        for app_name in sorted(commands_by_app.keys()):
            if len(commands_by_app[app_name]) > 1:
                # more than one panel entry fort his app
                # make a sub panel and put all items in the sub panel
                for cmd in commands_by_app[app_name]:
                    cmd.add_button()
            else:
                # this app only has a single entry.
                # display that on the panel
                # todo: Should this be labelled with the name of the app
                # or the name of the panel item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                cmd_obj.add_button()


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    def __init__(self, name, command_dict):
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name
        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD',
                                                doc_url).encode('ascii',
                                                                'ignore')
            return doc_url

        return None

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def add_button(self):
        """
        Adds an app command to the panel
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        engine.ui.add_button(self.name, self.callback)
