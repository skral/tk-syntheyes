# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights
# not expressly granted therein are reserved by Sebastian Kral.

# system modules
import os
import sys
import logging

import SyPy

# Constants
SGTK_SYNTHEYES_PORT = 'SGTK_SYNTHEYES_PORT'
SGTK_SYNTHEYES_PIN = 'SGTK_SYNTHEYES_PIN'

# setup logging
################################################################################
logger = logging.getLogger('sgtk.syntheyes')


def log_debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)


def log_error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)


def log_exception(msg, *args, **kwargs):
    logger.exception(msg, *args, **kwargs)


# setup default exception handling to log
def logging_excepthook(type, value, tb):
    logger.exception("Uncaught exception", exc_info=(type, value, tb))
    sys.__excepthook__(type, value, tb)
sys.execpthook = logging_excepthook


def get_existing_connection():
    port = int(os.environ[SGTK_SYNTHEYES_PORT])
    pin = os.environ[SGTK_SYNTHEYES_PIN]
    hlev = SyPy.SyLevel()
    hlev.OpenExisting(port, pin)
    return hlev
