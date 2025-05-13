import hou
import pathlib
from PySide2 import QtWidgets, QtCore
import re

class ErrorDialog(QtWidgets.QMainWindow,QtWidgets.QDialog):
    def __init__(self, message):
        super().__init__()
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setWindowTitle("Error")
        msgbox.setText(message)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msgbox.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        msgbox.exec_()

class MainWindow(QtWidgets.QMainWindow, QtWidgets.QWidget):
    def __init__(self,title):
        super().__init__()

        self.setWindowTitle(title)

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        mainLayout = QtWidgets.QVBoxLayout()

        layout1 = QtWidgets.QHBoxLayout()
        self.text = QtWidgets.QLineEdit("Texture Folder")
        layout1.addWidget(self.text)
        button1 = QtWidgets.QPushButton((".."))
        button1.clicked.connect(self.openFolder)
        layout1.addWidget(button1)
        mainLayout.addLayout(layout1)

        button2 = QtWidgets.QPushButton("Create")
        button2.clicked.connect(self.create)
        mainLayout.addWidget(button2)

        widget.setLayout(mainLayout)
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)

    def openFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Folder"))
        if not folder:
            return()
        self.text.setText(folder)
        
    def create(self):
        folder = self.text.text()
        path = pathlib.Path(folder)
        if not path.exists():
            ErrorDialog("Folder is not found")
            return()
        texCon(str(folder))

# main
def texCon(folder):
    with hou.undos.group("textureConnect") :
        fileType = ['BaseColor','Metalness','Roughness','Opacity','Emission','Normal','Height']
        filename = [getFiles(folder,t) for t in fileType]
        if not any(filename):
            ErrorDialog("Texture file not found")
            return()
        mat,disp,height,image = makeNodes(filename)
        fileSetting(filename,image,height,disp)
        connectNode(filename,mat,image,disp,height)
        mat.parent().layoutChildren()
    
def replacePath(i):
    hip = hou.hipFile.path()
    if not hip:
        return()
    hippath = pathlib.Path(hip)
    hippath = hippath.parent.name
    replacePath = re.sub("^.*"+f"{hippath}","$HIP",str(i))
    return(replacePath)

# getFiles
def getFiles(folder,texType):
    #フォルダからファイルを取り出す
    #選択されたフォルダがあるかどうか
    path = pathlib.Path(folder)
    if not path.exists():
        return(False)
    # フォルダ内に特定のファイルがあるか
    for i in path.iterdir():
        if i.suffix in ["tx","rat"]:
            continue
        if texType in str(i) :
            if re.search(r'_\d+\.',str(i)):
                i = re.sub(r'_\d+\.',r'_%(UDIM)d.',str(i))
            i = replacePath(i)
            return(i)
    else:
        return(False)   

# getNode
def makeNodes(filename):
    h = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    mat = hou.selectedItems()[0]
    disp = mat.outputs()[0].input(1)
    image = hou.node((h.pwd().path())).createNode('hmtlxpbrtextureset','hmtlxpbrtextureset1')
    height = False
    if filename[6]:
        height =  hou.node((h.pwd().path())).createNode('mtlximage','mtlximage1')
    return(mat,disp,height,image)

# setFilesParm
def fileSetting(filename,image,height,disp):
    hParm = ['base_color_file','metalness_file','specular_roughness_file','opacity_file','emission_color_file','bump_normal_file','Height_file']
    for i,f in enumerate(filename):
        # heightがあれば
        if i == 6 and f:
            height.parm('file').set(str(f))  # heightfile
            height.parm('signature').set('Float')  # flortType
            height.parm('filecolorspace').set('Raw')  # colorSpace
            disp.parm('scale').set(0.5)  # heightScale
            continue
        # 基本
        if f:
            image.parm(hParm[i]).set(str(f))
        # normalがあれば
        if i == 5 and f:
            image.parm('bump_style').set(1)  # RawSpace
            image.parm('bump_scale').set(1)  # normalScale
    
# connect
def connectNode(filename,mat,image,disp,height):
    if filename[0]:
        mat.setInput(1,image,0)  # baseColor
    if filename[1]:
        mat.setInput(3,image,1)  # metalness
    if filename[2]:
        mat.setInput(6,image,3)  # roughness
    if filename[3]:
        mat.setInput(38,image,10)  # opacity
    if filename[4]:
        mat.setInput(36,image,8)  # emission
    if filename[5]:
        mat.setInput(40,image,11)  # normal
    if filename[6]:
        disp.setInput(0,height,0)  # height
# outputNode:inputParmNum,inputNode,outputParmNum


def closeOldWindow(title):
    for widget in QtWidgets.QApplication.instance().topLevelWidgets():
        if widget.windowTitle() == title:
            widget.close()

def main():
    title = "textureConnect"
    closeOldWindow(title)
    
    win = MainWindow(title)
    win.show()

main()
