
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import glob
import _thread

from .pascal_voc_io import PascalVocReader
from .ui_ExportCls import Ui_ExportCls
from .ustr import ustr

# 操作类/操作层
class ExportCls(PascalVocReader):
    CLASSLIST = "classlist.txt"

    def __init__(self,xmlDir):
        self._shapes = []
        self._filepath = None
        self._imgPath = None
        self._resetImagesDir = None

        self.verified = False
        self._workDir = xmlDir  # xml saveDir= settingDir/classification
        self._workDir = os.path.join(self._workDir,"classification")
        self._classlist = dict()
        self._countsError = 0

    def saveImage(self,xmlPath):
        # 清空信息
        self._shapes.clear()
        self._imgPath = None
   
        self._filepath = xmlPath

        # 获取信息
        try:
            self._parseXML()
        except:
            pass

        # 图像重定向
        if self._resetImagesDir is not None:
            self._imgPath = os.path.join(self._resetImagesDir,self._filename)

        # 检查图像路径
        if not os.path.exists(self._imgPath):
            self._countsError += 1
            return 0
            
        # 导出图像分类-图像
        pixmap = QPixmap(self._imgPath)
        for i,shape in enumerate(self._shapes):
            clsName = shape[0]
            rect = self._getRect(shape[1])
            savePath = self._makeSaveDir(clsName,i)
            try:
                self._saveObj(pixmap,rect,savePath)
            except:
                # log
                pass

    def saveClasslist(self):
        txt_path = os.path.join(self._workDir,self.CLASSLIST)
        if os.path.exists(txt_path):
            os.remove(txt_path)
        
        if self._classlist:
            with open(txt_path,"w") as f:
                for key in self._classlist.keys():
                    f.writelines(key+"\n")                      
        
    def slot_changeSaveDir(self,saveDir):
        # 重置
        assert os.path.exists(saveDir),"error !"
        self._workDir = saveDir
        self._workDir = os.path.join(self._workDir,"classification")
        
        txt_path = os.path.join(self._workDir,self.CLASSLIST)
        print(txt_path)
        if os.path.exists(txt_path):
            with open(txt_path,"r") as f:
                for line in f.readlines():
                    self._classlist[line] = None
        else:
            self._classlist = dict()
        
        self._shapes = []
        self._filepath = None
        self._imgPath = None
        self.verified = False

    def _makeSaveDir(self,clsName,i):
        if clsName not in self._classlist.keys():
            self._classlist[clsName] = None

        path_dir = os.path.join(self._workDir,clsName)

        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        
        info = os.path.splitext(os.path.basename(self._imgPath))

        path = os.path.join(path_dir,"{}_{}{}".format(info[0],i,info[1]))
        return path

    def _getRect(self,points):
        return QRect(QPoint(points[0][0],points[0][1]),
                        QPoint(points[2][0],points[2][1]))

    def _saveObj(self,pixmap,rect,savePath):
        pixmap.copy(rect).save(savePath)

    def isOverError(self,allCounts,threshod=0.3):
        res = (self._countsError/allCounts) > threshod
        if res:
            self._countsError = 0
        return res

    def resetImageDir(self,imagesDir):
        self._resetImagesDir = imagesDir

# 业务类/业务层
class Dialog_ExportCls(QDialog):

    def __init__(self,parent = None,xmlDir=None,):
        super(Dialog_ExportCls,self).__init__(parent)
        self.ui = Ui_ExportCls()
        self.ui.setupUi(self)
        self.xmlDir = None   # xml信息目录，也是导出分类目录

        self.showSaveDir(xmlDir)
        self.ui.buttonBox.accepted.connect(self.clicked_ok)
        self.ui.buttonBox.rejected.connect(self.cliked_reject)
        self.ui.pushButton.clicked.connect(self.clicked_open)

        self._fix_counts = 0
        self._exit = False

    def showSaveDir(self,path_dir):
        self.ui.lineEdit.setText(path_dir)
        self.xmlDir = path_dir

    def cliked_reject(self):
        self._exit = True

    def clicked_ok(self):
       
        if self.xmlDir is None:
            self.close()
            return 0
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        try:
            _thread.start_new_thread(self.export_worker,())
        except:
            self.close()
        
    def export_worker(self):
        # 开始执行：导出（工作线程）
        exporter = ExportCls(self.xmlDir)
        
        # 互动式导出
        self._fix_imgPath(exporter)
        
        exporter.saveClasslist()

        # python中创建的对象，会因为close()释放内存吗？
        self.close()

    def _fix_imgPath(self,exporter):
        if self._fix_counts > 2 :
            return 0

        files = glob.glob('{}/*.xml'.format(self.xmlDir))
        for i,xmlPath in enumerate(files):
            if self._exit:
                _thread.exit()

            if exporter.isOverError(len(files)):
                self._fix_counts += 1
                # 更新图像目录
                dirpath = ustr(QFileDialog.getExistingDirectory(self,
                                                       'images directory:', self.xmlDir,  QFileDialog.ShowDirsOnly
                                                       | QFileDialog.DontResolveSymlinks))
                exporter.resetImageDir(dirpath)
                # 重新开始，丢弃上层递归
                self._fix_imgPath(exporter)
                return 0

            exporter.saveImage(xmlPath)
            # 进度条i/len(files)
            i += 1
            self.ui.progressBar.setValue(round(i*100/len(files)))

    def clicked_open(self):
        self.xmlDir = ustr(QFileDialog.getExistingDirectory(self,
                                                       'xml directory:', self.xmlDir,  QFileDialog.ShowDirsOnly
                                                       | QFileDialog.DontResolveSymlinks))   
        self.showSaveDir(self.xmlDir)





    
    


    
    

