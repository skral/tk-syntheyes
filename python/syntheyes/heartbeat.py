# Copyright (c) 2015 Sebastian Kral
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the MIT License included in this
# distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the MIT License. All rights not expressly granted therein are
# reserved by Sebastian Kral.

import logging
import os
import threading
import time

from syntheyes import get_existing_connection


# Constants
HEARTBEAT_INTERVAL = 'SGTK_SYNTHEYES_HEARTBEAT_INTERVAL'
HEARTBEAT_TOLERANCE = 'SGTK_SYNTHEYES_HEARTBEAT_TOLERANCE'


def setup():
    heartbeat = threading.Thread(target=heartbeat_thread_run,
                                 name="HeartbeatThread")
    heartbeat.start()


def heartbeat_thread_run():
    logger = logging.getLogger('sgtk.syntheyes.heartbeat')

    try:
        interval = float(os.getenv(HEARTBEAT_INTERVAL, '0.2'))
    except:
        logger.error("Error setting interval from %s: %s", HEARTBEAT_INTERVAL,
                     os.getenv(HEARTBEAT_INTERVAL))

    try:
        tolerance = int(os.getenv(HEARTBEAT_TOLERANCE, '1'))
    except:
        logger.error("Error setting tolerance from %s: %s", HEARTBEAT_TOLERANCE,
                     os.getenv(HEARTBEAT_TOLERANCE))

    error_cycle = 0
    while True:
        time.sleep(interval)
        try:
            hlev = get_existing_connection()
            if not hlev.core.OK():
                logger.error("Heartbeat: No connection.")
                error_cycle += 1
        except Exception, e:
            logger.exception("Python: Heartbeat unknown exception: %s" % e)

        if error_cycle >= tolerance:
            msg = "Python: Quitting. Heartbeat errors greater than tolerance."
            logger.error(msg)
            os._exit(0)
