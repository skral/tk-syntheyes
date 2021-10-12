class TrackingPlugin(object):
    def _encode_to_internal(self, point, shot):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: a tuple representing an x-y position, with the x-y values ranging between -1 and 1.
        :rtype: tracker_converter.utils.Point
        """
        raise NotImplementedError("Plugin %s does not define \"encode\"" % self.__class__.__name__)

    def _decode_from_internal(self, point, shot):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position, with x-y values ranging
                                                    between -1 and 1.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: a tuple representing an x-y position.
        :rtype: tracker_converter.utils.Point
        """
        raise NotImplementedError("Plugin %s does not define \"decode\"" % self.__class__.__name__)

    def trackers_to_internal(self, file_path, shot):
        """
        This function reads trackers, either directly from the program, or from a file, and returns a list of Tracker
        objects.

        :param str file_path: if importing from a .txt file, this is the file path. If not, pass None.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: A list of Tracker objects, with x-y values ranging between -1 and 1. The frame numbers of the Trackers
                 assume that the first frame of the scene is numbered zero.
        :rtype: list[tracker_converter.utils.Tracker...]
        """
        raise NotImplementedError("Plugin %s does not define \"import_trackers\"" % self.__class__.__name__)

    def internal_to_trackers(self, tracker_list, file_path, shot):
        """
        This function takes a list of Tracker objects and either creates the trackers in the calling program, or writes
        the trackers to file referenced in the arguments in the format of the calling program.

        :param list[Tracker...] tracker_list: a list of Tracker objects with x-y values ranging between -1 and 1. The
                                              frame numbers of the Trackers must be such that the first frame of the
                                              scene where they will be used is numbered zero.
        :param str file_path: if exporting to a text file, this is the file path. If not, pass None.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset. The frame offset is assumed to be the number of the first
                                                  frame in the scene where the trackers will be used.
        """
        raise NotImplementedError("Plugin %s does not define \"export_trackers\"" % self.__class__.__name__)
