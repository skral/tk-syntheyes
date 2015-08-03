# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights not expressly granted therein are
# reserved by Sebastian Kral.

from shutil import copyfile
import ConfigParser
import os
import re
import sys

import sgtk

CURRENT_EXTENSION = "0.1.0"


def bootstrap(engine_name, context, app_path, app_args, extra_args):

    engine_path = sgtk.platform.get_engine_path(engine_name, context.tank,
                                                context)
    if engine_path is None:
        msg = "Path to SynthEyes engine (tk-syntheyes) could not be found."
        raise TankError(msg)

    se_path = os.path.abspath(os.path.dirname(os.path.expandvars(app_path)))
    sgtk.util.append_path_to_env_var("PYTHONPATH", se_path)
    sys.path.append(se_path)

    # Get the path to the python executable
    python_setting = {"darwin": "mac_python_path",
                      "win32": "windows_python_path",
                      "linux": "linux_python_path"}[sys.platform]
    python_path = extra_args.get(python_setting)
    if not python_path:
        msg = ("Your SynthEyes app launch config is missing the"
               "extra setting %s" % python_setting)
        raise sgtk.TankError(msg)

    update(engine_path)

    # Store data needed for bootstrapping Toolkit in env vars.
    # Used in startup/menu.py
    os.environ["SGTK_SYNTHEYES_PYTHON"] = os.path.expandvars(python_path)
    os.environ["SGTK_SYNTHEYES_BOOTSTRAP"] = os.path.join(engine_path,
                                                          "python",
                                                          "startup",
                                                          "engine_bootstrap.py")

    import SyPy
    port = SyPy.syconfig.RandomPort(59200, 59300)
    pin = SyPy.syconfig.RandomPin()
    os.environ["SGTK_SYNTHEYES_PORT"] = str(port)
    os.environ["SGTK_SYNTHEYES_PIN"] = str(pin)

    new_args = ['-l', str(port), '-pin', pin,
                '-run', '"SGTK Initialize Engine"']

    xt = extra_args.get('extreme')
    if xt:
        new_args.append('-xt', xt)

    new_args = ' '.join(new_args)

    if app_args:
        app_args = "%s %s" % (new_args, app_args)
    else:
        app_args = new_args

    return app_path, app_args


def _user_path():
    user_path = {"darwin": "~/Library/Application Support/SynthEyes",
                 "win32": "%APPDATA%/SynthEyes",
                 "linux": "~/.SynthEyes"}[sys.platform]
    return os.path.expandvars(os.path.expanduser(user_path))


def _get_conf_fname():
    return os.path.join(_user_path(), 'sgtk_tk-syntheyes.ini')


def _get_config():
    # Setup defaults
    config = ConfigParser.SafeConfigParser()
    config.add_section("SGTK SynthEyes")
    config.set("SGTK SynthEyes", "installed_version", "0.0.0")

    # Load the actual config
    config_fname = _get_conf_fname()
    if os.path.exists(config_fname):
        config.read(config_fname)

    return config


def _save_config(config):
    # Create directory for config file if it does not exist
    config_fname = _get_conf_fname()
    config_dir = os.path.dirname(config_fname)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # Save out the updated config
    with open(config_fname, "wb") as file_:
        config.write(file_)


def tag(version):
    config = _get_config()
    config.set("SGTK SynthEyes", "installed_version", version)
    _save_config(config)


def _get_user_script_dir():
    return os.path.join(_user_path(), 'scripts')


def _version_cmp(left, right):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(left), normalize(right))


def _upgrade_script(engine_path):
    szl = "sgtk_bootstrap.szl"
    source_szl = os.path.abspath(os.path.join(engine_path, "bootstrap", szl))
    target_dir = _get_user_script_dir()
    target_szl = os.path.join(target_dir, szl)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    copyfile(source_szl, target_szl)


def update(engine_path):
    # Upgrade if the installed version is out of date
    config = _get_config()
    installed_version = config.get("SGTK SynthEyes", "installed_version")

    if _version_cmp(CURRENT_EXTENSION, installed_version) > 0:
        _upgrade_script(engine_path)
        tag(CURRENT_EXTENSION)
