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
This file is loaded automatically by SynthEyes at startup
It sets up the tank context and prepares the SGTK SynthEyes engine.
"""
import os
import sys


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


def bootstrap_tank():
    try:
        import sgtk
    except Exception, e:
        msg_box("Shotgun: Could not import sgtk! Disabling for now: %s" % e)
        return

    if "TANK_ENGINE" not in os.environ:
        msg_box("Shotgun: Missing required environment variable TANK_ENGINE.")
        return

    engine_name = os.environ.get("TANK_ENGINE")
    try:
        context = sgtk.context.deserialize(os.environ.get("TANK_CONTEXT"))
    except Exception, e:
        msg = ("Shotgun: Could not create context! Shotgun Pipeline Toolkit "
               "will be disabled. Details: %s" % e)
        msg_box(msg)
        return

    try:

        sgtk.platform.start_engine(engine_name, context.tank, context)
    except Exception, e:
        msg_box("Shotgun: Could not start SynthEyes engine: %s" % e)
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
