# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank

from syntheyes import get_existing_connection

HookBaseClass = tank.get_hook_baseclass()


class Operations(object):
    GetFrameRange = "get_frame_range"
    SetFrameRange = "set_frame_range"


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def execute(self, operation, in_frame=None, out_frame=None, **kwargs):
        """
        Main hook entry point
        :operation: String
                    Frame operation to perform
        :in_frame: int
                    in_frame for the current context (e.g. the current shot,
                                                      current asset etc)
        :out_frame: int
                    out_frame for the current context (e.g. the current shot,
                                                      current asset etc)
        :returns:   Depends on operation:
                    'set_frame_range' - Returns if the operation was successful
                    'get_frame_range' - Returns the frame range in the form
                                        (in_frame, out_frame)
        """
        connection = get_existing_connection()

        if operation == "get_frame_range":
            current_in = connection.AnimStart()
            current_out = connection.AnimEnd()
            return current_in, current_out
        elif operation == "set_frame_range":
            connection.SetAnimStart(in_frame)
            connection.SetAnimEnd(out_frame)
            return True
