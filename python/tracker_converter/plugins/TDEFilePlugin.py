import tracker_converter
import tracker_converter.utils

# from plugin import TrackingPlugin
import re

FRAME_MATCH_RE = re.compile(r"""
(?P<frame>\d+)\s       # This will look for an int at the start of the string followed by a whitespace
(?P<xpos>-?\d+.\d+)\s  # This will look for a float followed by a whitespace
(?P<ypos>-?\d+.\d+)    # This will look for a float
""", re.VERBOSE)


class LineIsNotAFrame(RuntimeError):
    pass


class TrackerCreationEndedEarly(RuntimeError):
    pass


class TrackingPlugin3DENative:

    # 3DE stores trackers at values that range between 0 and height/width, unless the tracker is not present in the
    # shot, in which case both the x and y values are -1. The top right corner is (width, height).

    def _encode_to_internal(self, point, shot):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position, with the x-y values ranging
                                                    between 0 and width/height.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: a tuple representing an x-y position, with the x-y values ranging between -1 and 1.
        :rtype: tracker_converter.utils.Point
        """
        # [0, height] -> [-1, 1]
        # [0, height] / height = [0, 1]
        # 2 * [0, 1] = [0, 2]
        # [0, 2] - 1 = [-1, 1]
        # 2 * [0, 1] / height - 1 = [-1, 1]

        x_not_in_range = not 0 < point.x < shot.width
        y_not_in_range = not 0 < point.y < shot.height

        if x_not_in_range or y_not_in_range:
            raise ValueError("Values outside of the program format's range were passed.")

        x = 2 * point.x / shot.width - 1
        y = 2 * point.y / shot.height - 1

        return tracker_converter.Point(x, y)

    def _decode_from_internal(self, point, shot):
        """
        :param tracker_converter.utils.Point point: a tuple representing an x-y position, with x-y value ranging between
                                                    -1 and 1.
        :param None|tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and
                                                       frame offset.
        :return: a tuple representing an x-y position, with the x-y values ranging between 0 and width/height.
        :rtype: tracker_converter.utils.Point
        """
        # [-1, 1] -> [0, height]
        # [-1, 1] + 1 = [0, 2]
        # [0, 2] / 2 = [0, 1]
        # [0, 1] * height = [0, height]
        # ([-1, 1] + 1) * height / 2 = [0, height]

        # x_not_in_range = not -1 < point.x < 1
        # y_not_in_range = not -1 < point.y < 1
        #
        # if x_not_in_range or y_not_in_range:
        #     raise ValueError("Values outside of the program format's range were passed.")

        x = (point.x + 1) * shot.width / 2.0
        y = (point.y + 1) * shot.height / 2.0

        return tracker_converter.Point(x, y)

    def _create_frame(self, tracker, line, shot):
        """
        Reads the passed string. If it matches the tracker format, adds it to tracker.

        :param tracker_convert.utils.Tracker tracker: a Tracker object.
        :param str line: a string which might contain data which defines a frame of a tracker.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and
                                                  frame offset.
        :raises: NotFrameLineError
        """

        match = FRAME_MATCH_RE.match(line)
        if match:
            data = match.groupdict()
            point = tracker_converter.utils.Point(data.get("xpos"), data.get("ypos"))
            internal_point = self._encode_to_internal(point, shot)
            tracker.add_frame(int(data.get("frame")) - shot.offset, internal_point)
        else:
            raise LineIsNotAFrame(line)

    def _create_tracker(self, lines, shot):
        """
        :param List[str...] lines: a list of strings which represent the data read from file.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and
                                                  frame offset.
        :return: a Tracker object which contains the data in the file passed.
        """
        name = lines.pop(0)
        # TODO: check to make sure it is a name
        zero = lines.pop(0)
        if zero is '0':
            tracker_count = int(lines.pop(0))
            tracker = tracker_converter.utils.Tracker(name)
            for count in range(tracker_count):
                try:
                    self._create_frame(tracker, lines.pop(0), shot)
                except LineIsNotAFrame as err:
                    print("Failure: not a line! %s" % str(err))
                    raise TrackerCreationEndedEarly("Frame {} is bad".format(count))
            return tracker
        # TODO: throw an exception if zero wasn't found.

    def trackers_to_internal(self, text, shot):
        """
        This function creates a list of Tracker objects from a text file containing trackers exported by 3DE.
        :param str text: the file path of the exported trackers.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        :return: A list of Tracker objects, with x-y values ranging between -1 and 1.
        :rtype: list[Tracker...]
        """

        with open(text, "rb") as file_handle:
            text = file_handle.read()
        lines = text.split("\n")
        first_line = lines.pop(0)
        try:
            tracker_count_expected = int(first_line)
        except ValueError:
            raise ValueError("The first line of the file is {}, which is not a number.".format(first_line))

        trackers = []
        for counter in range(tracker_count_expected):
            try:
                t = self._create_tracker(lines, shot)
            except TrackerCreationEndedEarly:
                print("Could not finish creating tracker {}".format(counter))
            else:
                trackers.append(t)

        return trackers

    def internal_to_trackers(self, tracker_list, text, shot):
        """
        This function takes a list of Tracker objects and creates a text file which can be imported to 3DE.
        :param list[tracker_converter.utils.Tracker...] tracker_list: a list of Tracker objects with x-y values ranging
                                                                      between -1 and 1.
        :param str text: the file path to which the trackers should be written.
        :param tracker_converter.utils.Shot shot: a tuple representing the shot - a width and height of plate, and frame
                                                  offset.
        """
        encoded_data = []
        num_trackers = len(tracker_list)
        encoded_data.append(str(num_trackers))
        for tracker in tracker_list:
            tracker_name = tracker.name
            encoded_data.append(tracker_name)
            encoded_data.append('0')
            encoded_data.append(str(tracker.number_of_frames))
            for frame_number in sorted(tracker.frame_numbers):
                point = tracker.point_at(frame_number)
                decoded_point = self._decode_from_internal(point, shot)
                encoded_data.append("{} {} {}".format(str(frame_number + shot.offset),
                                                      str(decoded_point.x),
                                                      str(decoded_point.y)))

        encoded_text = "\n".join(encoded_data)

        with open(text, "w") as fh:
            fh.write(encoded_text)
