# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# system modules
import sys
import logging

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
