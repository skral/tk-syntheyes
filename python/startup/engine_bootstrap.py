# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights not expressly granted therein are
# reserved by Sebastian Kral.

import os
import sys
import logging
import logging.handlers


# platform specific alert with no dependencies
def msg_box(message):
    if sys.platform == "win32":
        import ctypes
        message_box = ctypes.windll.user32.MessageBoxA
        message_box(None, message, "Shotgun", 0)
    elif sys.platform == "darwin":
        os.system("""osascript -e 'tell app "System Events" to activate""")
        msg_ = ("""osascript -e 'tell app "System Events" to display"""
                """dialog "%s" with icon caution buttons "Sorry!"'""" % message)
        os.system(msg_)

# setup logging
################################################################################
try:
    log_dir = '%s/Library/Logs/Shotgun/' % os.path.expanduser('~')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'tk-syntheyes.log')
    rotating = logging.handlers.RotatingFileHandler(log_file,
                                                    maxBytes=4*1024*1024,
                                                    backupCount=10)
    pattern = '%(asctime)s [%(levelname) 8s] ' \
              '%(threadName)s %(name)s: %(message)s'
    rotating.setFormatter(logging.Formatter(pattern))
    logger = logging.getLogger('sgtk')
    logger.addHandler(rotating)
    logger.setLevel(logging.INFO)

    logger = logging.getLogger('sgtk.syntheyes.PythonBootstrap')
    msg = '================================== ' \
          'Initializing Python Interpreter ==================================='
    logger.info(msg)

    # setup default exception handling to log
    def logging_excepthook(type, value, tb):
        logger.exception("Uncaught exception", exc_info=(type, value, tb))
        sys.__excepthook__(type, value, tb)
    sys.execpthook = logging_excepthook
except Exception, e:
    msg_box("Shotgun Pipeline Toolkit failed to initialize logging:\n\n%s" % e)
    raise

# setup sys path to include SynthEyes API
################################################################################
api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "python"))
sys.path.insert(0, api_path)

# Initialize heartbeat
try:
    from syntheyes import heartbeat
    heartbeat.setup()
except Exception, e:
    msg = ("Shotgun Pipeline Toolkit failed to initialize"
           "SynthEyes heartbeat:\n\n%s" % e)
    msg_box(msg)
    logger.exception('Failed to initialize SynthEyes heartbeat')
    sys.exit(1)

# Startup PySide
################################################################################
try:
    from PySide import QtGui
    from tk_syntheyes import logging_console
except Exception, e:
    logger.exception("Failed to initialize PySide.")
    sys.exit(1)

# create global app
try:
    sys.argv[0] = 'Shotgun SynthEyes'
    g_app = QtGui.QApplication(sys.argv)
    g_app.setQuitOnLastWindowClosed(True)
    res_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
    g_app.setWindowIcon(QtGui.QIcon(os.path.join(res_dir,
                                                 "process_icon_256.png")))
    g_app.setApplicationName(sys.argv[0])
except Exception, e:
    logger.exception("Could not create global PySide app")
    sys.exit(1)

# logging console
try:
    g_log = logging_console.LogConsole()
    g_app.setProperty("tk-syntheyes.log_console", g_log)
    qt_handler = logging_console.QtLogHandler(g_log.logs)
    logger = logging.getLogger('sgtk')
    logger.addHandler(qt_handler)
    g_log.setHidden(True)
except Exception, e:
    logger.exception("Could not create logging console")
    sys.exit(1)

# run userSetup.py if it exists, borrowed from Maya
################################################################################
try:
    for path in sys.path:
        scriptPath = os.path.join(path, 'userSetup.py')
        if os.path.isfile(scriptPath):
            logger.debug('Running "%s"', scriptPath)
            import __main__
            try:
                execfile(scriptPath, __main__.__dict__)
            except:
                logger.exception('Error running "%s"', scriptPath)
except Exception, e:
    logger.exception('Failed to execute userSetup.py')

logger.info("Starting PySide backend application %s", g_app)
sys.exit(g_app.exec_())
