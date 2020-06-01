import json
from libs.shape import *

JSON_EXT = ".json"
LAEBLME_VERSION = "4.4.0"

class SegReader:

    def __init__(self, filepath):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self._shapes = []
        self._filepath = filepath
        self._imgPath = None
        self._filename = None
        self.verified = False
        try:
            self._load(filepath)
        except:
            pass

    def getShapes(self):
        return self._shapes

    def _load(self,filename):
        keys = [
            'version',
            'imageData',
            'imagePath',
            'shapes',  # polygonal annotations
            'flags',   # image level flags
            'imageHeight',
            'imageWidth',
        ]
        shape_keys = [
            'label',
            'points',
            'group_id',
            'shape_type',
            'flags',
        ]

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            version = data.get('version')
            if version is None:
                print(
                    'Loading JSON file ({}) of unknown version'
                    .format(filename)
                )
            elif version.split('.')[0] != LAEBLME_VERSION.split('.')[0]:
                print(
                    'This JSON file ({}) may be incompatible with '
                    'current labelme. version in file: {}, '
                    'current version: {}'.format(
                        filename, version, LAEBLME_VERSION
                    )
                )


            flags = data.get('flags') or {}
            imagePath = data['imagePath']
           
            shapes = [
                dict(
                    label=s['label'],
                    points=s['points'],
                    shape_type=s.get('shape_type', 'polygon'),
                    flags=s.get('flags', {}),
                    group_id=s.get('group_id'),
                    other_data={
                        k: v for k, v in s.items() if k not in shape_keys
                    }
                )
                for s in data['shapes']
            ]
        except Exception as e:
            pass

        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value

        # Only replace data after everything is loaded.
        self.flags = flags
        self._shapes = shapes
        self.imagePath = imagePath
        self.filename = filename
        self.otherData = otherData


class Shape_seg(Shape):

    def __init__(self, label=None, line_color=None, shape_type=None,
                 flags=None, group_id=None,paintLabel=False):

        self.paintLabel = paintLabel

        self.label = label
        self.group_id = group_id
        self.points = []
        self.fill = False
        self.selected = False
        self.shape_type = shape_type
        self.flags = flags
        self.other_data = {}

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

        self.shape_type = shape_type

    @property
    def shape_type(self):
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        if value is None:
            value = 'polygon'
        if value not in ['polygon', 'rectangle', 'point',
           'line', 'circle', 'linestrip']:
            raise ValueError('Unexpected shape_type: {}'.format(value))
        self._shape_type = value

    def copy(self):
        shape = Shape_seg("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape_seg.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape_seg.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        return shape