# from plugin import TrackingPlugin
import tracker_converter
import tracker_converter.utils
import os
SPLIT_CHAR = " "


class SynthEyesNativePlugin:

    # SynthEyes does not offer direct Python access, instead opting to offer a scripting language (Sizzle) which can
    # invoke Python. As such, all data is passed to/from Sizzle in the form of text files; there is no other time-
    # efficient way to pass large quantities of data.
    # SynthEyes stores tracker locations as x-y pairs, with coordinates ranging between -1 and 1. The bottom right
    # corner is (1, 1), and the upper-left is (-1, -1).

    def _encode_to_internal(self, point, shot=None):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position, with the x-y values ranging
                                                    between -1 and 1.
        :param None|tracker_converter.utils.Shot shot: This value is not used and None may be passed safely.
        :return: a tuple representing an x-y position, with the x-y values ranging between -1 and 1.
        :rtype: tracker_converter.utils.Point
        :raises: ValueError if the point passed is outside of the expected range for SynthEyes.
        """

        # TODO: temporarily removed exception for testing purposes.
        # x_not_in_range = not -1 < point.x < 1
        # y_not_in_range = not -1 < point.y < 1
        #
        # if x_not_in_range or y_not_in_range:
        #     raise ValueError("Values outside of the program format's range were passed.")

        # To encode to the internal format, we simply need to invert the y-value (multiply by -1).

        x = point.x
        y = -1 * point.y

        return tracker_converter.Point(x, y)

    def _decode_from_internal(self, point, shot=None):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position, with the x-y values ranging
                                                    between -1 and 1.
        :param None|tracker_converter.utils.Shot shot: This value is not used and None may be passed safely.
        :return: a tuple representing an x-y position, with the x-y values ranging between -1 and 1.
        :rtype: tracker_converter.utils.Point
        :raises: ValueError if the point passed is outside of the expected range for our internal format.
        """
        if not -1 < point.x < 1 or not -1 < point.y < 1:
            raise ValueError("Values outside of the internal range were passed.")

        # To decode from the internal format, we simply need to invert the y-value (multiply by -1).

        x = point.x
        y = -1 * point.y

        return tracker_converter.Point(x, y)

    def trackers_to_internal(self, file_path, shot):
        """
        This function reads from a file passed via Sizzle from SynthEyes, and returns a list of Tracker objects.

        :param str file_path: the file path. The file is assumed to be formatted with a tracker name, frame number, and
                              an x and y position on each line, separated by spaces.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: A list of Tracker objects, with x-y values ranging between -1 and 1.
        :rtype: list[tracker_converter.utils.Tracker...]
        """
        with open(file_path, "r") as file_handle:
            contents = file_handle.read().strip("\n")

        lines = contents.split("\n")

        trackers = {}

        for line in lines:
            line = line.strip()
            words = line.split(SPLIT_CHAR)

            name = words[0]
            frame = words[1]
            x = words[2]
            y = words[3]

            if name not in trackers:
                trackers[name] = tracker_converter.utils.Tracker(name)

            point = self._encode_to_internal(tracker_converter.utils.Point(x, y), None)

            trackers[name].add_frame(int(frame) - shot.offset, point)

        internal_data = []
        for tracker in trackers.values():
            for frame in tracker.frame_numbers:
                internal_data.append(tracker.name + ' ' + str(int(frame)) + ' ' + str(tracker.point_at(frame).x)
                                     + ' ' + str(tracker.point_at(frame).y))

        internal_text = "\n".join(internal_data)

        with open("{}/import_3DE_to_SE_internal.txt".format(os.path.dirname(file_path)), "w") as fh:
            fh.write(internal_text)

        return trackers.values()

    def internal_to_trackers(self, tracker_list, file_path, shot=None):
        """
        This function takes a list of Tracker objects and writes a text file which can be easily read by a Sizzle script
        to create those trackers in SynthEyes. Each line of the text file returned has the following format.

        TRACKER_NAME TRACKER_FRAME_NUMBER X_POS Y_POS

        ... where TRACKER_NAME has had any spaces removed and replaced with the pipe character ('|').

        :param list[Tracker...] tracker_list: a list of Tracker objects with x-y values ranging between -1 and 1.
        :param str file_path: the file path of the text file to which trackers are being written.
        :param None|tracker_converter.utils.Shot shot: This value is not used and None may be passed safely.
        """

        encoded_data = []

        # The lines are sorted by tracker name, then frame number. The existing script makes a big deal out of this, so
        # I'm mirroring it, even though I'm not sure it's necessary.

        for tracker in sorted(tracker_list, key=lambda x: x.name, reverse=False):
            name = tracker.name.replace(' ', '|')
            for frame in sorted(tracker.frame_numbers):
                encoded_point = self._decode_from_internal(tracker.point_at(frame))
                encoded_data.append(name + ' ' + str(int(frame) + shot.offset) + ' ' + str(encoded_point.x) + ' ' +
                                    str(encoded_point.y))

        encoded_text = "\n".join(encoded_data)

        with open(file_path, "wb") as fh:
            fh.write(encoded_text)
