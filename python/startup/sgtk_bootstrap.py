# TODO: Has to be a sizzle script with calls to system commands
# This is the only way how we can run syntheyes without first setting up python


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


def bootstrap_sgtk():
    python_path = os.environ.get("SGTK_SYNTHEYES_PYTHON")
    bootstrap_script = os.environ.get("SGTK_SYNTHEYES_BOOTSTRAP")
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

    # file_to_open = os.environ.get("SGTK_SYNTHEYES_BOOTSTRAP")
    # if file_to_open:
    #     import photoshop
    #     f = photoshop.RemoteObject("flash.filesystem::File", file_to_open)
    #     photoshop.app.load(f)

    # clean up temp env vars
    for var in ["TANK_ENGINE", "TANK_CONTEXT", "TANK_FILE_TO_OPEN"]:
        if var in os.environ:
            del os.environ[var]


bootstrap_sgtk()
