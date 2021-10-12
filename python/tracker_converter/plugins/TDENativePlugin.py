from plugin import TrackingPlugin
import tracker_converter
import tracker_converter.utils
import tde4


class TrackingPlugin3DENative(TrackingPlugin):

    # 3DE stores trackers at values that range between 0 and 1, unless the
    # tracker is not present in the shot, in which case both the x and y values
    # are -1. The top right corner is (1, 1).

    def _encode_to_internal(self, point, shot=None):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y
        position, with the x-y values ranging between 0 and 1.
        :param None|tracker_converter.utils.Shot shot: This value is not used
        and None may be passed safely.
        :return: a tuple representing an x-y position, with the x-y values
        ranging between -1 and 1.
        :rtype: tracker_converter.utils.Point
        :raises: ValueError if the point passed is outside of the expected
        range for 3DE.

        """
        x = 2 * point.x - 1
        y = 2 * point.y - 1

        return tracker_converter.Point(x, y)

    def _decode_from_internal(self, point, shot=None):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y
        position, with x-y value ranging between -1 and 1.
        :param None|tracker_converter.utils.Shot shot: This value is not used
        and None may be passed safely.
        :return: a tuple representing an x-y position, with the x-y values
        ranging between 0 and 1.
        :rtype: tracker_converter.utils.Point
        :raises: ValueError if the point passed is outside of the expected range
        for our internal format.
        """

        x = (point.x + 1) / 2
        y = (point.y + 1) / 2

        return tracker_converter.Point(x, y)

    def trackers_to_internal(self, file_path, shot):
        """
        This function creates a list of Tracker objects from trackers in 3DE.
        It also applies any frame offsets.
        :param None|str file_path: This field is not used and None can be passed
        safely.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot
        - a width and height of plate, and frame offset.
        :return: A list of Tracker objects, with x-y values ranging between -1
        and 1.
        :rtype: list[Tracker...]
        """
        camera = tde4.getCurrentCamera()
        point_group = tde4.getCurrentPGroup()

        if camera is not None and point_group is not None:

            first_frame, last_frame = tde4.getCameraPlaybackRange(camera)

            trackers = {}
            while point_group is not None:
                point_list = tde4.getPointList(point_group, 0)
                for point in point_list:
                    name = tde4.getPointName(point_group, point)
                    if name not in trackers:
                        trackers[name] = tracker_converter.Tracker(name)
                    xy = tde4.getPointPosition2DBlock(point_group, point,
                                                      camera, first_frame,
                                                      last_frame)

                    frame = first_frame - shot.offset
                    for x, y in xy:
                        # inactive trackers are -1, -1
                        if x != -1.0 and y != -1.0:
                            encoded_point = self._encode_to_internal(tracker_converter.Point(x, y),
                                                                     None)
                            trackers[name].add_frame(frame, encoded_point)
                        frame += 1
                point_group = tde4.getNextPGroup(point_group)
            if not trackers:
                tde4.postQuestionRequester("Error",
                                           "There are no trackers to export.",
                                           "OK")
                return None
            return trackers.values()
        else:
            tde4.postQuestionRequester("Error", "Either a point group or camera is missing.", "OK")

    def internal_to_trackers(self, tracker_list, file_path, shot):
        """
        This function takes a list of Tracker objects and creates the associated
        trackers in 3DE.

        :param list[tracker_converter.utils.Tracker...] tracker_list: a list of
        Tracker objects with x-y values ranging between -1 and 1.
        :param str file_path: This value is not used and None may be passed safely.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot
        - a width and height of plate, and frame offset.
        """
        camera = tde4.getCurrentCamera()
        point_group = tde4.getCurrentPGroup()

        if camera is not None and point_group is not None:
            first_frame, last_frame = tde4.getCameraPlaybackRange(camera)
            for tracker in tracker_list:
                point = tde4.createPoint(point_group)
                tde4.setPointName(point_group, point, tracker.name)
                list_of_vectors = []

                # generated 3DE trackers need a list of 2d vectors with a length
                # equal to the number of frames associated with the camera in
                # question. each vector is a set of x-y coordinates. if the
                # Tracker exists at that frame number, add that x-y data to the
                # list of 2d vectors. if the Tracker does not exist at that
                # frame number, add (-1, -1).

                for frame_number in range(first_frame, last_frame):
                    if frame_number - shot.offset in tracker.frame_numbers:
                        x = tracker.point_at(frame_number - shot.offset).x
                        y = tracker.point_at(frame_number - shot.offset).y
                        decoded_point = self._decode_from_internal(tracker_converter.Point(x, y),
                                                                   None)
                        list_of_vectors.append([decoded_point.x, decoded_point.y])
                    else:
                        list_of_vectors.append([-1, -1])
                tde4.setPointPosition2DBlock(point_group, point, camera,
                                             first_frame, list_of_vectors)
        else:
            tde4.postQuestionRequester("Import trackers to 3DE",
                                       "Either a point group or camera is missing.", "OK")
