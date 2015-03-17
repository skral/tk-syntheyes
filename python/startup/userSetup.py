# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights
# not expressly granted therein are reserved by Sebastian Kral.

"""
This file is loaded automatically by SynthEyes at startup
It sets up the tank context and prepares the SGTK SynthEyes engine.
"""
import os
import sys


def msgbox(msg):
    if sys.platform == "win32":
        import ctypes
        MessageBox = ctypes.windll.user32.MessageBoxA
        MessageBox(None, msg, "Shotgun", 0)
    elif sys.platform == "darwin":
        os.system("""osascript -e 'tell app "System Events" to activate""")
        os.system("""osascript -e 'tell app "System Events" to display dialog "%s"'""" % msg)


def bootstrap_tank():
    try:
        import sgtk
    except Exception, e:
        msgbox("Shotgun: Could not import sgtk! Disabling for now: %s" % e)
        return

    if not "TANK_ENGINE" in os.environ:
        msgbox("Shotgun: Missing required environment variable TANK_ENGINE.")
        return

    engine_name = os.environ.get("TANK_ENGINE")
    try:
        context = sgtk.context.deserialize(os.environ.get("TANK_CONTEXT"))
    except Exception, e:
        msgbox("Shotgun: Could not create context! Shotgun Pipeline Toolkit will be disabled. Details: %s" % e)
        return
        
    try:    
        engine = sgtk.platform.start_engine(engine_name, context.tank, context)
    except Exception, e:
        msgbox("Shotgun: Could not start SynthEyes engine: %s" % e)
        return

    file_to_open = os.environ.get("TANK_FILE_TO_OPEN")
    if file_to_open:
        from syntheyes import get_existing_connection
        hlev = get_existing_connection()
        hlev.OpenSNI(file_path)

    # clean up temp env vars
    for var in ["TANK_ENGINE", "TANK_CONTEXT", "TANK_FILE_TO_OPEN"]:
        if var in os.environ:
            del os.environ[var]


bootstrap_tank()
