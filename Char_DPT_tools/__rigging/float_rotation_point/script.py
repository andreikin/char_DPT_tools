


import maya.cmds as cmds
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya

from float_point import float_point


class CreateFloatPoint_UI(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Create floating pivot")

        self.layout = QGridLayout()
        self.layout.setSpacing(6)
        self.setLayout(self.layout)

        self.label = QLabel(
            "Create a floating pivot for the selected controller. \nThe controller must be in a group")
        self.layout.addWidget(self.label, 0, 0, 1, 2)
        
        self.label_pfx = QLabel("Prefix")
        self.layout.addWidget(self.label_pfx, 1, 0)

        self.pfx_jine = QLineEdit()
        self.pfx_jine.setPlaceholderText("  enter prefx (if needed)")
        self.pfx_jine.setClearButtonEnabled(True)
        self.layout.addWidget(self.pfx_jine, 1, 1)
        
        self.button = QPushButton("Create floating pivot")
        self.layout.addWidget(self.button, 2, 0, 1, 2)
        self.button.clicked.connect(self.create)
    
    def create(self):
        ctrl = cmds.ls(sl=1)[0]        
        pfx = self.pfx_jine.text()   
        print ctrl, pfx
        float_point (ctrl, pfx)

def create_float_point():
    window = CreateFloatPoint_UI()
    window.show()


create_float_point()


 