import maya.cmds as cmds
import maya.mel as mel
import re
import pymel.core as pm
from skining import getSkin, setSkin
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import cPickle


ROOT_LOC = "ROOT"
joints = []

def an_saveLoadData(data=[], obgect='', delAttr=False, vDir=''):  # save and load data to/from object and file

    if not vDir: vDir = mel.eval("getenv (\"HOME\")")
    if data:  # if data exist - save mod
        if obgect:  # if  obgect exist - save on it
            if not cmds.objExists(obgect + '.data'):
                cmds.addAttr(obgect, ln="data", dt="string", keyable=False)
            cmds.setAttr(obgect + ".data", cPickle.dumps(data), type="string")
        else:
            vFileName = cmds.fileDialog2(fileFilter='*.dat', fileMode=0, caption="Save position", dir=vDir)
            f = open(vFileName[0], 'w')
            cPickle.dump(data, f)
            f.close()

    else:  # if data absent - load mod
        if obgect:  # if  obgect exist - load from it
            vString = cmds.getAttr(obgect + '.data')
            if delAttr: cmds.deleteAttr(obgect + '.data')
            return cPickle.loads(str(vString))
        else:  # if  obgect not exist - load from file
            # vDir = mm.eval("getenv (\"HOME\")")
            vFileName = cmds.fileDialog2(fileMode=1, caption="Load position", dir=vDir)
            r = open(vFileName[0], 'r')
            data = cPickle.load(r)
            r.close()
            return data

def get_joints_brache(jnt):
    """
    get joints brache
    """
    if jnt not in joints:
        joints.append(jnt)
    children = cmds.listRelatives(jnt, children=True)

    if children:
        for chaild in children:
            if cmds.nodeType(chaild) == "joint" and not chaild in joints:
                get_joints_brache(chaild)

    parent = cmds.listRelatives(jnt, parent=True)
    if parent:
        get_joints_brache(parent[0])


def generate_unique_name(name):
    if cmds.objExists(name):
        shot_name = name.split("|")[-1] if "|" in name else name  # if given path - get object name
        i = 1
        while True:  # if there are numbers in the name - increase their value until the name becomes unique

            if re.search("\d+", shot_name):
                new_name = re.sub(r"\d+", '{0:02d}'.format(i), shot_name, count=1)

            elif re.findall(r"_", shot_name):
                sfx = shot_name.split("_")[-1] if re.findall(r"_", shot_name) else ""
                new_name = re.sub("_" + sfx, '{0:02d}_'.format(i) + sfx, shot_name, count=1)

            else:
                new_name = shot_name + '{0:02d}'.format(i)

            if not cmds.objExists(new_name) or i > 1000:  break
            i += 1
        return new_name
    else:
        return name


class CheckBoxGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(attribut)
        self.lebel.setFixedSize(110, 20)
        self.layout.addWidget(self.lebel)

        self.check_box  = QCheckBox()
        self.layout.addWidget(self.check_box )

    def value(self):
        return self.lebel.text(), bool(self.check_box.checkState())

class CreateSkinJnt_UI(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Create skining joints system")

        self.layout = QVBoxLayout()
        self.layout.setSpacing(3)
        self.setLayout(self.layout)

        self.label = QLabel(
            "Making a copy of skin bones and linking them to control \nbones. Select geometry before creating\n")
        self.layout.addWidget(self.label)

        self.constraints_check = CheckBoxGrp("Made constraints")
        self.constraints_check.check_box.setCheckState(Qt.Checked)
        self.layout.addWidget(self.constraints_check)

        self.connection_check = CheckBoxGrp("Connection file")
        self.layout.addWidget(self.connection_check)

        self.buttonFile = QPushButton("Create connection file")
        self.layout.addWidget(self.buttonFile)
        self.buttonFile.clicked.connect(self.connection_file)

        self.buttonCreate = QPushButton("Create 'skinned' joints")
        self.layout.addWidget(self.buttonCreate)
        self.buttonCreate.clicked.connect(self.create_joints)

        self.button_layout = QHBoxLayout()
        self.buttonConnect = QPushButton("Connect to rig")
        self.button_layout.addWidget(self.buttonConnect)
        self.buttonConnect.clicked.connect(self.connect_rig)
        self.buttonDisonnect = QPushButton("Disconnect rig")
        self.button_layout.addWidget(self.buttonDisonnect)
        self.buttonDisonnect.clicked.connect(self.disconnect_rig)
        self.layout.addLayout(self.button_layout)

        self.setFixedWidth(500)

    def connection_file(self):
        header = ['from maya import cmds',
                  'from s3dCharBuilder.SetupRig import find_node',
                  '',
                  '',
                  'def setup(namespace="", part=""):',
                  '    find = lambda i, c=namespace, p=part: find_node(i, character=c, part=p)']

        connection_list = an_saveLoadData(obgect=ROOT_LOC)
        for i in range(len(connection_list)):
            line = '    cmds.parentConstraint(find("$CHARACTER:' + connection_list[i][0] + '"), find("$CHARACTER:' + connection_list[i][1] + '"), mo=False)'
            header.append(line)
        file_path = cmds.fileDialog2(fileFilter='*.py', fileMode=0, caption="Save position", dir="")[0]
        file_obj = open(file_path, 'w+')
        for i in header:
            file_obj.write(i + "\n")
        file_obj.close()



    def disconnect_rig(self):
        connection_list = an_saveLoadData(obgect=ROOT_LOC)

        for i in range(len(connection_list)):
            if connection_list[i][2]:
                cmds.delete(connection_list[i][2])
                connection_list[i][2] = None
        an_saveLoadData(data=connection_list, obgect=ROOT_LOC)

    def connect_rig(self):
        connection_list = an_saveLoadData(obgect=ROOT_LOC)
        for i in range(len(connection_list)):
                connection_list[i][2] = cmds.parentConstraint(connection_list[i][0], connection_list[i][1], mo=False)[0]
        an_saveLoadData(data=connection_list, obgect=ROOT_LOC)

    def create_joints(self):
        all_geometry = cmds.ls(sl=1)
        print all_geometry
        for geo in pm.ls():
            if "|" in geo.name():
                new_name = generate_unique_name(geo.name())
                print(new_name)
                geo.rename(new_name)

        if not cmds.objExists(ROOT_LOC):
            cmds.spaceLocator(n=ROOT_LOC)

        skin_jnt_list = []
        for geo in all_geometry:
            skinCluster = mel.eval('findRelatedSkinCluster("' + geo + '")')
            if skinCluster:
                skin_jnt_list += cmds.skinCluster(skinCluster, query=True, inf=True)

        skin_jnt_list = list(set(skin_jnt_list))
        connection_list = []
        parent_list = []
        jnt_dict = dict()
        for jnt in skin_jnt_list:
            skin_jnt = jnt.replace("_jnt", "_skinned") if "_jnt" in jnt else jnt + "_skinned"
            jnt_dict[jnt] = skin_jnt
            cmds.select(cl=1)
            cmds.joint(n=skin_jnt)
            cmds.parent(skin_jnt, ROOT_LOC)

            if self.constraints_check.value()[1]:
                constraint = cmds.parentConstraint(jnt, skin_jnt, mo=False)[0]
                connection_list.append([jnt, skin_jnt, constraint])
            else:
                connection_list.append([jnt, skin_jnt, None])

            # get parent jnt
            parent_jnt = cmds.listRelatives(jnt, p=True)[0]
            if parent_jnt in skin_jnt_list:
                parent_skin_jnt = parent_jnt.replace("_jnt",
                                                     "_skinned") if "_jnt" in parent_jnt else parent_jnt + "_skinned"
                parent_list.append([skin_jnt, parent_skin_jnt])

        for jnt, parent_jnt in parent_list:
            cmds.parent(jnt, parent_jnt)

        for geo in all_geometry:
            if cmds.ls(cmds.listHistory(geo), type='skinCluster'):
                weight = getSkin(geo)
                new_weight = {jnt_dict[x]: weight[x] for x in weight.keys()}
                setSkin(geo, new_weight)

        an_saveLoadData(data=connection_list, obgect=ROOT_LOC)

        if self.connection_check.value()[1]:
            self.connection_file()

def create_skin_jnt():
    window = CreateSkinJnt_UI()
    window.show()


create_skin_jnt()
