from tracker_converter.exceptions import FrameNotFoundError


class Shot(object):
    def __init__(self, width, height, offset):
        super(Shot, self).__init__()
        self._width = float(width)
        self._height = float(height)
        self._offset = int(offset)

    @property
    def width(self):
        """
        :return: the width of the shot
        :rtype: float
        """
        return self._width

    @property
    def height(self):
        """
        :return: the height of the shot
        :rtype: float
        """
        return self._height

    @property
    def offset(self):
        """
        :return: the offset of the shot
        :rtype: int
        """
        return self._offset


class Point(object):
    def __init__(self, x, y):
        super(Point, self).__init__()
        self._x = float(x)
        self._y = float(y)

    @property
    def x(self):
        """
        :return: the x-value of the tracker
        :rtype: float
        """
        return self._x

    @property
    def y(self):
        """
        :return: the x-value of the tracker
        :rtype: float
        """
        return self._y


class Tracker(object):
    def __init__(self, name):
        super(Tracker, self).__init__()
        self._name = name
        self._data = {}

    @property
    def name(self):
        """
        :return: the name of the Tracker.
        :rtype: str
        """
        return self._name

    @property
    def frame_numbers(self):
        """
        :return: the frame numbers where the Tracker is defined.
        :rtype: list[int...]
        """
        return list(self._data.keys())

    @property
    def number_of_frames(self):
        """
        :return: the number of frames for which the Tracker is defined.
        :rtype: int
        """
        return len(list(self._data.keys()))

    def add_frame(self, frame_number, point):
        """
        :param int frame_number: the frame associated with the Point being added.
        :param Point point: the Point associated with the frame being added.
        """
        if not isinstance(point, Point):
            raise ValueError("point must be a Point instance")
        self._data[int(frame_number)] = point

    def point_at(self, frame_number):
        """
        if the frame does not exist in the Tracker, throws an error.
        :param int frame_number: the frame number associated with the Point being found
        :return Point: the Point at the specified frame.
        :raises: FrameNotFoundError
        """
        point = self._data.get(frame_number, None)
        if point:
            return point
        raise FrameNotFoundError("Could not find a keyframe at frame %d in tracker %s" % (frame_number, self.name))

