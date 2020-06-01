# Copyright (c) 2016 Tzutalin
# Create by TzuTaLin <tzu.ta.lin@gmail.com>

try:
    from PyQt5.QtGui import QImage
except ImportError:
    from PyQt4.QtGui import QImage

from base64 import b64encode, b64decode
from libs.pascal_voc_io import PascalVocWriter
from libs.yolo_io import YOLOWriter
from libs.pascal_voc_io import XML_EXT
import os.path
import sys
import json

from libs.seg_io import JSON_EXT

class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT
    suffix_seg = JSON_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False

    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        #imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image = QImage()
        image.load(imagePath)
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = PascalVocWriter(imgFolderName, imgFileName,
                                 imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            # Add Chris
            difficult = int(shape['difficult'])
            bndbox = LabelFile.convertPoints2BndBox(points)
            writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label, difficult)

        writer.save(targetFile=filename)
        return

    def saveYoloFormat(self, filename, shapes, imagePath, imageData, classList,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        #imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image = QImage()
        image.load(imagePath)
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = YOLOWriter(imgFolderName, imgFileName,
                                 imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            # Add Chris
            difficult = int(shape['difficult'])
            bndbox = LabelFile.convertPoints2BndBox(points)
            writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label, difficult)

        writer.save(targetFile=filename, classList=classList)
        return

    def saveJsonFormat(self,filename,shapes,imagePath,imageHeight,imageWidth,
                        imageData=None,otherData=None,flags=None):
        if imageData is not None:
            imageData = None
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = {}
        data = dict(
            version="4.4.0",
            flags=flags,
            shapes=shapes,
            imagePath=imagePath,
            imageData=imageData,
            imageHeight=imageHeight,
            imageWidth=imageWidth,
        )
        for key, value in otherData.items():
            assert key not in data
            data[key] = value
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    def toggleVerify(self):
        self.verified = not self.verified

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    @staticmethod
    def isLabelFile_Seg(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix_seg

    @staticmethod
    def convertPoints2BndBox(points):
        xmin = float('inf')
        ymin = float('inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            xmin = min(x, xmin)
            ymin = min(y, ymin)
            xmax = max(x, xmax)
            ymax = max(y, ymax)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while
        # training faster-rcnn object detector.
        if xmin < 1:
            xmin = 1

        if ymin < 1:
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))
