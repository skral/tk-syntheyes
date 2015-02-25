import os
import sys

import sgtk

def bootstrap(engine_name, context, app_path, app_args):

    # TODO: Where does the launcher come from?
    launcher = sgtk.platform.Application
    extra_configs = launcher.get_setting("extra", {})

    # Get the path to the python executable
    python_setting = {"darwin": "mac_python_path", "win32": "windows_python_path"}[sys.platform]
    python_path = extra_configs.get(python_setting)
    if not python_path:
        raise sgtk.TankError("Your syntheyes app launch config is missing the extra setting %s" % python_setting)

    # TODO: Make sure bootstrap stub script is available to SynthEyes

    # Store data needed for bootstrapping Toolkit in env vars. Used in startup/menu.py
    os.environ["SGTK_SYNTHEYES_PYTHON"] = python_path
    os.environ["SGTK_SYNTHEYES_BOOTSTRAP"] = os.path.join(os.path.dirname(__file__), "engine_bootstrap.py")

    # add our startup path to the syntheyes init path
    # startup_path = os.path.abspath(os.path.dirname(__file__))
    # sgtk.util.append_path_to_env_var("PYTHONPATH", startup_path)
