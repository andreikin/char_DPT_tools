import maya.cmds as cmds
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya


class CreateTwistJnt_UI(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Create twist joints system")

        self.layout = QGridLayout()
        self.layout.setSpacing(6)
        self.setLayout(self.layout)

        self.label = QLabel(
            "Select the joint you want to add a twist to. \nMake sure this joint has a parent and child.\n")
        self.layout.addWidget(self.label, 0, 0, 1, 2)

        self.label_pfx = QLabel("Prefix")
        self.layout.addWidget(self.label_pfx, 1, 0)
        self.pfx_jine = QLineEdit()
        self.layout.addWidget(self.pfx_jine, 1, 1)

        self.label_aim = QLabel("Aim axis")
        self.layout.addWidget(self.label_aim, 2, 0)
        self.aim_combo = QComboBox()
        for pfx in ["  x", "  y", "  z", "  -x", "  -y", "  -z"]:
            self.aim_combo.addItem(pfx)
        self.layout.addWidget(self.aim_combo, 2, 1)

        self.label_up = QLabel("Up axis")
        self.layout.addWidget(self.label_up, 3, 0)
        self.up_combo = QComboBox()
        for pfx in ["  z", "  x", "  y", "  -x", "  -y", "  -z"]:
            self.up_combo.addItem(pfx)
        self.layout.addWidget(self.up_combo, 3, 1)

        self.buttonConnect = QPushButton("Add up joint")
        self.layout.addWidget(self.buttonConnect, 4, 0)
        self.buttonConnect.clicked.connect(self.add_up_joint)
        self.buttonDisonnect = QPushButton("Add down joint")
        self.layout.addWidget(self.buttonDisonnect, 4, 1)
        self.buttonDisonnect.clicked.connect(self.add_dw_joint)
        self.setFixedWidth(400)

    def get_data(self):
        data = dict()
        axis = {"  x": [1, 0, 0], "  y": [0, 1, 0], "  z": [0, 0, 1],
                "  -x": [-1, 0, 0], "  -y": [0, -1, 0], "  -z": [0, 0, -1]}
        data["pfx"] = self.pfx_jine.text()
        data["jnt"] = cmds.ls(sl=True)[0]
        data["aim"] = axis[self.aim_combo.currentText()]
        data["up"] = axis[self.up_combo.currentText()]
        data["child_jnt"] = cmds.listRelatives(data["jnt"], c=True)[0]
        data["parent_jnt"] = cmds.listRelatives(data["jnt"], p=True)[0]
        return data

    def add_up_joint(self):
        data = self.get_data()
        insert_twist_jnt(data["jnt"], data["pfx"], aim=data["aim"], parent_jnt=data["parent_jnt"],  up=data["up"])

    def add_dw_joint(self):
        data = self.get_data()
        insert_twist_jnt(data["jnt"], data["pfx"], aim=data["aim"], parent_jnt=data["parent_jnt"], child_jnt=data["child_jnt"],  up=data["up"])


def create_twist_jnt():
    window = CreateTwistJnt_UI()
    window.show()






def insert_twist_jnt(jnt, pfx, up=None, aim=None, parent_jnt=None, child_jnt=None):
    if aim is None:
        aim = [1, 0, 0]
    if up is None:
        up = [0, 0, 1]
    #  add up joint
    if parent_jnt and not child_jnt:
        cmds.select(cl=1)
        tw_jnt = cmds.joint(n=pfx + "UpTw_jnt")
        constraint = cmds.pointConstraint(jnt, tw_jnt, w=0.9)
        cmds.pointConstraint(parent_jnt, tw_jnt, w=0.1)
        cmds.delete(constraint)
        cmds.aimConstraint(parent_jnt, tw_jnt, aim=aim, worldUpVector=up, worldUpObject=jnt, upVector=up,
                           worldUpType="objectrotation")
        cmds.parent(tw_jnt, parent_jnt)
    #  add dw joint
    if child_jnt:
        cmds.select(cl=1)
        tw_jnt = cmds.joint(n=pfx + "DwTw_jnt")
        constraint = cmds.pointConstraint(jnt, tw_jnt, w=0.9)
        cmds.pointConstraint(child_jnt, tw_jnt, w=0.1)
        cmds.delete(constraint)
        cmds.aimConstraint(child_jnt, tw_jnt, aim=aim, worldUpVector=up, worldUpObject=parent_jnt, upVector=up,
                           worldUpType="objectrotation")
        cmds.parent(tw_jnt, jnt)


create_twist_jnt()