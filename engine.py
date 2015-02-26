# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A SynthEyes engine for Toolkit.
"""
import logging
import os
import sys

import sgtk


###############################################################################################
# The Toolkit SynthEyes engine
class SyntheyesEngine(sgtk.platform.Engine):
    _logger = logging.getLogger('sgtk.syntheyes.engine')

    ##########################################################################################
    # init and destroy
    def init_engine(self):
        self._init_logging()
        self.log_debug("%s: Initializing...", self)
        self.__qt_dialogs = []

    def pre_app_init(self):
        from tk_syntheyes.ui.sgtk_panel import Ui_SgtkPanel
        self.ui = Ui_SgtkPanel()
        self.ui.show()

    def post_app_init(self):
        import tk_syntheyes
        self._initialize_dark_look_and_feel()
        self._panel_generator = tk_syntheyes.PanelGenerator(self)
        self._panel_generator.populate_panel()

    def destroy_engine(self):
        self.log_debug("%s: Destroying...", self)
        self._panel_generator.destroy_panel()

    ##########################################################################################
    # UI

    def _define_qt_base(self):
        """
        This will be called at initialisation time and will allow 
        a user to control various aspects of how QT is being used
        by Toolkit. The method should return a dictionary with a number
        of specific keys, outlined below. 
        
        * qt_core - the QtCore module to use
        * qt_gui - the QtGui module to use
        * dialog_base - base class for to use for Toolkit's dialog factory
        
        :returns: dict
        """
        base = {}
        from PySide import QtCore, QtGui
        base["qt_core"] = QtCore
        base["qt_gui"] = QtGui
        base["dialog_base"] = QtGui.QDialog
        
        # tell QT to handle text strings as utf-8 by default
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)

        return base

    def _win32_get_syntheyes_process_id(self):
        """
        Windows specific method to find the process id of SynthEyes.  This
        assumes that it is the parent process of this python process
        """
        if hasattr(self, "_win32_syntheyes_process_id"):
            return self._win32_syntheyes_process_id
        self._win32_syntheyes_process_id = None

        this_pid = os.getpid()

        from tk_syntheyes import win_32_api
        self._win32_syntheyes_process_id = win_32_api.find_parent_process_id(this_pid)

        return self._win32_syntheyes_process_id

    def _win32_get_syntheyes_main_hwnd(self):
        """
        Windows specific method to find the main SynthEyes window
        handle (HWND)
        """
        if hasattr(self, "_win32_syntheyes_main_hwnd"):
            return self._win32_syntheyes_main_hwnd
        self._win32_syntheyes_main_hwnd = None

        # find SynthEyes process id:
        ps_process_id = self._win32_get_syntheyes_process_id()

        if ps_process_id != None:
            # get main application window for SynthEyes process:
            from tk_syntheyes import win_32_api
            found_hwnds = win_32_api.find_windows(process_id=ps_process_id, class_name="Syntheyes", stop_if_found=False)
            if len(found_hwnds) == 1:
                self._win32_syntheyes_main_hwnd = found_hwnds[0]

        return self._win32_syntheyes_main_hwnd

    def _win32_get_proxy_window(self):
        """
        Windows specific method to get the proxy window that will 'own' all Toolkit dialogs.  This
        will be parented to the main syntheyes application.  Creates the proxy window
        if it doesn't already exist.
        """
        if hasattr(self, "_win32_proxy_win"):
            return self._win32_proxy_win
        self._win32_proxy_win = None

        # get the main syntheyes window:
        ps_hwnd = self._win32_get_syntheyes_main_hwnd()
        if ps_hwnd != None:

            from sgtk.platform.qt import QtGui
            from tk_syntheyes import win_32_api

            # create the proxy QWidget:
            self._win32_proxy_win = QtGui.QWidget()
            self._win32_proxy_win.setWindowTitle('sgtk dialog owner proxy')

            proxy_win_hwnd = win_32_api.qwidget_winid_to_hwnd(self._win32_proxy_win.winId())

            # set no parent notify:
            win_ex_style = win_32_api.GetWindowLong(proxy_win_hwnd, win_32_api.GWL_EXSTYLE)
            win_32_api.SetWindowLong(proxy_win_hwnd, win_32_api.GWL_EXSTYLE, 
                                     win_ex_style 
                                     | win_32_api.WS_EX_NOPARENTNOTIFY)

            # parent to syntheyes application window:
            win_32_api.SetParent(proxy_win_hwnd, ps_hwnd)

        return self._win32_proxy_win

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        # determine the parent widget to use:
        parent_widget = None
        if sys.platform == "win32":
            # for windows, we create a proxy window parented to the
            # main application window that we can then set as the owner
            # for all Toolkit dialogs
            parent_widget = self._win32_get_proxy_window()
        else:
            from sgtk.platform.qt import QtGui
            parent_widget = QtGui.QApplication.activeWindow()
            
        return parent_widget

    def show_dialog(self, title, bundle, widget_class, *args, **kwargs):
        """
        Shows a non-modal dialog window in a way suitable for this engine.
        The engine will attempt to parent the dialog nicely to the host application.

        :param title: The title of the window
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        if not self.has_ui:
            self.log_error("Sorry, this environment does not support UI display! Cannot show "
                           "the requested window '%s'." % title)
            return
        
        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(title, bundle, widget_class, *args, **kwargs)
        
        # Note - the base engine implementation will try to clean up
        # dialogs and widgets after they've been closed.  However this
        # can cause a crash in syntheyes as the system may try to send
        # an event after the dialog has been deleted.
        # Keeping track of all dialogs will ensure this doesn't happen
        self.__qt_dialogs.append(dialog)

        # make sure the window raised so it doesn't
        # appear behind the main syntheyes window
        dialog.raise_()
        dialog.activateWindow()
                    
        # show the dialog:
        dialog.show()
        
        return widget

    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        """
        Shows a modal dialog window in a way suitable for this engine. The engine will attempt to
        integrate it as seamlessly as possible into the host application. This call is blocking
        until the user closes the dialog.

        :param title: The title of the window
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: (a standard QT dialog status return code, the created widget_class instance)
        """
        if not self.has_ui:
            self.log_error("Sorry, this environment does not support UI display! Cannot show "
                           "the requested window '%s'." % title)
            return        
        
        from sgtk.platform.qt import QtGui
        
        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(title, bundle, widget_class, *args, **kwargs)
        
        # Note - the base engine implementation will try to clean up
        # dialogs and widgets after they've been closed. However this
        # can cause a crash in syntheyes as the system may try to send
        # an event after the dialog has been deleted.      
        # Keeping track of all dialogs will ensure this doesn't happen  
        self.__qt_dialogs.append(dialog)
        
        # make sure the window raised so it doesn't
        # appear behind the main syntheyes window
        dialog.raise_()
        dialog.activateWindow()

        status = QtGui.QDialog.Rejected
        if sys.platform == "win32":
            from tk_syntheyes import win_32_api

            saved_state = []
            try:
                # find all syntheyes windows and save enabled state:
                ps_process_id = self._win32_get_syntheyes_process_id()
                if ps_process_id != None:
                    found_hwnds = win_32_api.find_windows(process_id=ps_process_id, stop_if_found=False)
                    for hwnd in found_hwnds:
                        enabled = win_32_api.IsWindowEnabled(hwnd)
                        saved_state.append((hwnd, enabled))
                        if enabled:
                            win_32_api.EnableWindow(hwnd, False)

                # show dialog:
                status = dialog.exec_()
            except Exception, e:
                self.log_error("Error showing modal dialog: %s" % e)
            finally:
                # kinda important to ensure we restore other window state:
                for hwnd, state in saved_state:
                    if win_32_api.IsWindowEnabled(hwnd) != state:
                        win_32_api.EnableWindow(hwnd, state)
        else:
            # show dialog:
            status = dialog.exec_()

        return status, widget

    ##########################################################################################
    # logging

    def _init_logging(self):
        toolkit_logger = logging.getLogger('sgtk')
        if self.get_setting("debug_logging", False):
            toolkit_logger.setLevel(logging.DEBUG)
        else:
            toolkit_logger.setLevel(logging.INFO)

    def log_debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def log_info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def log_exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)
