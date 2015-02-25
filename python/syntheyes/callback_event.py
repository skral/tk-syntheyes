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
framework for running callbacks in the main PySide GUI thread

This is used by the logging console to update the gui on the main thread
and so it cannot use logging itself
"""
import logging
from PySide import QtCore


class RunCallbackEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        QtCore.QEvent.__init__(self, RunCallbackEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class CallbackRunner(QtCore.QObject):
    _logger = logging.getLogger('sgtk.photoshop.engine')

    def event(self, event):
        try:
            if (getattr(event.fn, '_tkLog', True)):
                self._logger.info("Callback %s", str(event.fn))
            event.fn(*event.args, **event.kwargs)
        except Exception:
            self._logger.exception("Error in callback %s", str(event.fn))
        return True

g_callbackRunner = CallbackRunner()


def send_to_main_thread(fn, *args, **kwargs):
    global g_callbackRunner
    QtCore.QCoreApplication.postEvent(g_callbackRunner, RunCallbackEvent(fn, *args, **kwargs))
