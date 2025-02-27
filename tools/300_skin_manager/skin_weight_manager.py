# -*- coding: utf-8 -*-
import copy
import json
import math
import re
from pprint import pprint
from random import random, uniform

from PySide2.QtWidgets import QMainWindow, QMenuBar, QMenu, QAction, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, \
    QGroupBox, QButtonGroup, QPushButton, QLabel, QProgressBar, QLineEdit, QGridLayout, QDialog, QScrollArea

from PySide2.QtCore import Qt, QSettings
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.mel as mm


PFX_PATTERN = '^(L_|R_|l_|r_|left_|right_|Left_|Right_)'
DIGIT_PATTERN = r'\d{1,}$'
AUXILIARY_ATTRIBUTES = ["paint_weights", "skinningMethod"]

ABOUT_PROGRAM = "\nLatest updates:                                   \n" \
                "25.10.2024    -added dialog for missing objects     \n" \
                "17.04.2024    -update save_skin function            \n" \
                "23.05.2021    -added Switch geometry tool           \n" \
                "19.05.2021    -added mirror weights tool            \n" \
                "16.05.2021    -added help                           \n" \
                "                                                    \n" \
                "Created by Andrey Belyaev                           \n" \
                "andreikin@mail.ru"

HELP_TEXT = """
            \n1 Save/Load skining:
            \n- The save weights button saves the skin weights of all selected objects.
            \n- The load weights button sets the weights of the objects saved in the corresponding file (highlighting is not necessary
            \n\n2 Copy weights to selected vertex:
            \n- Specify the copy source using the "Add Selected" button. After that, select the necessary vertices to which you want to copy the weight and click the "Copy weights to vertex" button
            \n\n3 Copy weights:
            \n- To copy from several objects, select all objects from which the weights will be copied. Select the target object last
            \n- To copy weights to several objects, first select the object from which weights will be copied, then all objects to which weights will be copied and click "Copy weights"
            \n\n4 Other tools:
            \n- "Flood shell" allows you to fill the weight of the selected joint with a geometric object inside the combined geometry. To do this, select the desired joint, then one of the object's vertices
            \n- "Select skin joints" selects all joints from the skin cluster of the selected geometry
            """


class SkinWeightManager(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(SkinWeightManager, self).__init__()
        self.setWindowTitle("Skin weight manager  v 5.0.1")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.layout = QVBoxLayout(self.centralwidget)
        self.layout.setSpacing(20)

        # ______________________ menu_bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.menu = QMenu("Help")
        self.menu_bar.addMenu(self.menu)

        self.help_action = QAction("Help", self)
        self.menu.addAction(self.help_action)

        self.about_script_action = QAction("About script", self)
        self.menu.addAction(self.about_script_action)

        self.help_action.triggered.connect(lambda: self.text_dialog_ui(HELP_TEXT))
        self.about_script_action.triggered.connect(lambda: self.text_dialog_ui(ABOUT_PROGRAM))

        # ______________________ save / load
        self.save_load_box = QGroupBox("Save/Load skining:")
        self.save_load_box_layout = QHBoxLayout(self.save_load_box)
        self.save_button = QPushButton('Save skin weight')
        self.save_load_box_layout.addWidget(self.save_button)

        self.blended_button = QPushButton('Load blended weights')
        self.save_load_box_layout.addWidget(self.blended_button)

        self.load_button = QPushButton('Load skin weight')
        self.save_load_box_layout.addWidget(self.load_button)
        self.layout.addWidget(self.save_load_box)
        self.save_button.clicked.connect(self.save_skin)

        self.blended_button.clicked.connect(self.load_blend_weights)

        self.load_button.clicked.connect(self.load_skin)

        # ______________________ copy_to_vertex

        self.to_vertex_box = QGroupBox("Copy weights to selected vertex:")
        self.to_vertex_box_layout = QVBoxLayout(self.to_vertex_box)
        self.layout.addWidget(self.to_vertex_box)

        to_vertex_h_layout = QHBoxLayout()
        self.to_vertex_h_lebel = QLabel("Copy from:")
        self.to_vertex_h_line_edit = QLineEdit()
        self.add_selection_button = QPushButton("Add selected")
        self.add_selected = lambda: self.to_vertex_h_line_edit.setText(cmds.ls(sl=True)[0])
        self.add_selection_button.clicked.connect(self.add_selected)
        for each in (self.to_vertex_h_lebel, self.to_vertex_h_line_edit, self.add_selection_button):
            to_vertex_h_layout.addWidget(each)
        self.to_vertex_box_layout.addLayout(to_vertex_h_layout)

        self.to_vertex_btn = QPushButton('Copy weights to vertex')
        self.to_vertex_btn.clicked.connect(self.copy_skin_to_vertex)
        self.to_vertex_box_layout.addWidget(self.to_vertex_btn)

        # ______________________ copy
        self.copy_box = QGroupBox("Copy weights:")
        self.copy_box_layout = QHBoxLayout(self.copy_box)
        self.layout.addWidget(self.copy_box)

        self.copy_several_button = QPushButton('Copy from several objects')
        self.copy_box_layout.addWidget(self.copy_several_button)
        self.copy_weights_button = QPushButton('Copy weights')
        self.copy_box_layout.addWidget(self.copy_weights_button)
        self.copy_several_button.clicked.connect(self.copy_from_objects)
        self.copy_weights_button.clicked.connect(self.copy_skin)

        # ______________________  other tools
        self.other_box = QGroupBox("Other tools:")
        self.other_box_layout = QGridLayout(self.other_box)
        self.layout.addWidget(self.other_box)

        self.flood_shell_button = QPushButton('Flood shell')
        self.other_box_layout.addWidget(self.flood_shell_button, 0, 0)
        self.flood_shell_button.clicked.connect(self.flood_shell)

        self.select_skin_button = QPushButton('Select skin joints')
        self.other_box_layout.addWidget(self.select_skin_button, 0, 1)
        self.select_skin_button.clicked.connect(self.selekt_skin_jnts)

        self.mirror_weights_button = QPushButton('Mirror weights')
        self.other_box_layout.addWidget(self.mirror_weights_button, 1, 0)
        self.mirror_weights_button.clicked.connect(self.mirror_command)

        self.reskin_geometry_button = QPushButton('Reskin geometry')
        self.other_box_layout.addWidget(self.reskin_geometry_button, 1, 1)
        self.reskin_geometry_button.clicked.connect(self.reskin)

        self.setFixedWidth(600)

    @staticmethod
    def text_dialog_ui(text_data):
        """
        'Help window' or 'About program' text dialog
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)

        if "Latest updates:" in text_data:
            help_dialog.setWindowTitle("About program")
        else:
            help_dialog.setWindowTitle("Help window")

        help_dialog.setText(text_data)
        help_dialog.setStandardButtons(QMessageBox.Cancel)
        help_dialog.exec_()

    def ___________________________(self):
        pass

    def load_blend_weights(self):

        vDir = cmds.workspace(q=True, rd=True)
        file_path = cmds.fileDialog2(fileFilter='*.dat', fileMode=1, caption="Save position", dir=vDir)

        if not file_path:
            om.MGlobal.displayError('Canceling a save')
            return False

        with open(file_path[0], "r") as file:
            data = json.load(file)[0]

        for geo in data.keys():
            weight = data[geo]
            bland_attr = weight.pop("paint_weights")
            skinning_method = weight.pop("skinningMethod")
            skin_cluster = Skin.get_skin_claster(geo)
            cmds.setAttr(skin_cluster + ".skinningMethod", skinning_method)
            for i, each in enumerate(bland_attr):
                cmds.setAttr(skin_cluster + '.bw[' + str(i) + ']', each)

        om.MGlobal.displayInfo('Weights successfully loaded!')

        print('load_blend_weights')

    def load_skin(self):

        vDir = cmds.workspace(q=True, rd=True)
        file_path = cmds.fileDialog2(fileFilter='*.dat', fileMode=1, caption="Save position", dir=vDir)

        if not file_path:
            om.MGlobal.displayError('Canceling a save')
            return False

        with open(file_path[0], "r") as file:
            data = json.load(file)[0]

        if self.get_missing_objects(data):
            self.dialog = ReplaceDialog(data, self)
            self.dialog.setWindowFlags(self.dialog.windowFlags() | Qt.WindowStaysOnTopHint)
            self.dialog.show()
        else:
            for geo in data.keys():
                Skin.set_weight(geo, data[geo])
            om.MGlobal.displayInfo('Weights successfully loaded!')

    def save_skin(recordNod=''):
        """
        Saves the skin weights of selected polygon objects onto a data object that can be loaded later.
        """
        listGeo = cmds.ls(sl=True)
        dataList = {}
        vDir = cmds.workspace(q=True, rd=True)
        file_path = cmds.fileDialog2(fileFilter='*.dat', fileMode=0, caption="Save position", dir=vDir)

        if not file_path:
            om.MGlobal.displayError('Canceling a save')
            return False

        if listGeo:
            # cmds.progressWindow(title='Save skin', progress=0, status='', isInterruptable=True)
            # i = 0
            for geo in listGeo:
                # i += 100 / max(len(listGeo), 1)
                # cmds.progressWindow(edit=True, progress=min(i, 100), status='')
                dataList[geo] = Skin.get_weight(geo)

            with open(file_path[0], "w") as file:
                json.dump([dataList, ], file, indent=4)

            # cmds.progressWindow(endProgress=1)
            om.MGlobal.displayInfo('Weights successfully saved!')
        else:
            om.MGlobal.displayError('One or more polygon objects must be selected!')

    def copy_skin_to_vertex(self):
        """
        Copies skin weights from one object onto selected vertices of another object.
        """
        try:
            sourceObj = self.to_vertex_h_line_edit.text()
            destVert = Utilities.convert_slice_to_list(cmds.ls(sl=True))
            Skin.copy_to_sel_vertex(sourceObj, destVert)
            om.MGlobal.displayInfo('Weights successfully copied!')
        except Exception as message:
            om.MGlobal.displayError(message)

    @staticmethod
    def copy_from_objects():
        """
        This function copies skin weights from a source geometry objects to a target geometry.
        """
        try:
            sGeo = cmds.ls(sl=True)[:-1]
            geo = cmds.ls(sl=True)[-1]
            if cmds.ls(cmds.listHistory(geo), type='skinCluster'):
                skCluster = cmds.ls(cmds.listHistory(geo), type='skinCluster')[0]
                cmds.skinCluster(skCluster, e=True, ub=True)
            jntList = []
            for each in sGeo:
                skinCluster = cmds.ls(cmds.listHistory(each), type='skinCluster')[0]
                jnts = cmds.ls(cmds.listHistory(skinCluster, levels=1), type='transform')
                for jnt in jnts:
                    if jnt not in jntList:
                        jntList.append(jnt)
            cmds.skinCluster(jntList, geo, tsb=True, normalizeWeights=True)
            cmds.select(sGeo + [geo])
            cmds.copySkinWeights(noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne')
            om.MGlobal.displayInfo('Weights successfully copied!')
        except Exception as message:
            om.MGlobal.displayError(message)

    @staticmethod
    def copy_skin():
        """Copying weights from the first selected object to the rest"""
        try:
            lst = cmds.ls(sl=True)
            for geo in lst[1:]:
                Skin.copy(lst[0], geo)
                om.MGlobal.displayInfo('Weights successfully copied to "' + geo + '"!')
        except Exception as message:
            om.MGlobal.displayError(message)

    @staticmethod
    def flood_shell():
        """
        Allows you to fill the weight of the selected joint with a geometric object inside the combined geometry.
        To do this, select the desired joint, then one of the object's vertices
        """
        mm.eval('polyConvertToShell;')
        sel = cmds.ls(sl=True)
        joint = [x for x in sel if cmds.nodeType(x) == "joint"][0]
        # get face if it exist
        selFaces = cmds.filterExpand(sm=34)
        if selFaces:
            sel_vertexees = Utilities.convert_slice_to_list(cmds.polyListComponentConversion(selFaces, tv=True))
        else:
            sel_vertexees = [x for x in sel if not cmds.nodeType(x) == "joint"]
        vertexees = []
        while sel_vertexees:
            node = sel_vertexees.pop()
            vertex = Utilities.convert_slice_to_list([node])
            vertexees += vertex

        geo = vertexees[0].split(".vtx")[0]
        weight = Skin.get_weight(geo)

        pointNumber = len(vertexees)
        if not joint in weight.keys():
            weight[joint] = [0 for x in range(pointNumber)]
        vertex_indexes = [int(x.split(".vtx[")[-1][:-1]) for x in vertexees]

        for jnt in weight.keys():
            if jnt not in AUXILIARY_ATTRIBUTES:
                if jnt == joint:
                    for i in vertex_indexes:
                        weight[jnt][i] = 1.0
                else:
                    for i in vertex_indexes:
                        weight[jnt][i] = 0.0

        Skin.set_weight(geo, weight)
        pprint(weight)

    @staticmethod
    def selekt_skin_jnts():
        """Selects all joints from the skin cluster of the selected geometry"""
        skinClusterName = cmds.ls(cmds.listHistory(cmds.ls(sl=True)), type='skinCluster')[0]
        jointName = cmds.ls(cmds.listHistory(skinClusterName, levels=1), type='transform')
        cmds.select(jointName)
        return jointName

    @staticmethod
    def mirror_command():
        selection = cmds.ls(sl=True)
        if selection:
            Mirror(selection[0]).mirror()
        cmds.select(selection)

    @staticmethod
    def reskin(objectName=None):
        if not objectName:
            objectName = cmds.ls(sl=True)[0]
        weightList = Skin.get_weight(objectName)
        skinClusterName = cmds.ls(cmds.listHistory(objectName, pdo=1), type='skinCluster')[0]
        cmds.skinCluster(skinClusterName, e=True, ub=True)
        Skin.set_weight(objectName, weightList)
        om.MGlobal.displayInfo('Weights successfully saved!')

    @staticmethod
    def get_missing_objects(data):
        """
        Finds objects from the dictionary with weights that are not present in the scene
        """
        missing_objects = set()
        for geo_dict in data:
            for joint in data[geo_dict]:
                if cmds.objExists(joint) or joint in AUXILIARY_ATTRIBUTES:
                    continue
                missing_objects.add(joint)

            if cmds.objExists(geo_dict):
                continue
            missing_objects.add(geo_dict)

        return list(missing_objects)


class ReplaceDialog(QDialog):
    def __init__(self, data, parent=None):
        super(ReplaceDialog, self).__init__(parent)
        self.item_list = list()
        self.data = data

        self.setWindowTitle('Set up name mapping')

        layout = QVBoxLayout()
        namespace_layout = QHBoxLayout()
        layout.addLayout(namespace_layout)

        self.text_label = QLabel('The following object are missing from the scene. Please specify the required ones.')
        layout.addWidget(self.text_label)
        self.text_label.setWordWrap(True)

        # _________________________________ namespace change button
        # creation
        self.namespace_label = QLabel('Namespace: ')
        self.namespace_le = QLineEdit()
        self.namespace_butten_add = QPushButton('Add')
        self.namespace_butten_sub = QPushButton('Subtract')
        # set location
        namespace_layout.addWidget(self.namespace_label)
        namespace_layout.addWidget(self.namespace_le)
        namespace_layout.addWidget(self.namespace_butten_add)
        namespace_layout.addWidget(self.namespace_butten_sub)
        # connection
        self.namespace_butten_add.clicked.connect(self.edit_namespace_add)
        self.namespace_butten_sub.clicked.connect(self.edit_namespace_sub)

        # _________________________________ central layout for items
        # creation
        self.items_layout = QVBoxLayout()
        self.inside_layout = QVBoxLayout()
        widget = QWidget()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # set location
        widget.setLayout(self.inside_layout)
        scroll_area.setWidget(widget)
        layout.addWidget(scroll_area)
        self.items_layout.addWidget(scroll_area)

        self.add_items()

        # ____________________________________ bottom buttons
        self.button_layout = QHBoxLayout()
        layout.addLayout(self.button_layout)
        # creation
        self.apply_button = QPushButton("Apply", self)
        self.cancel_button = QPushButton("Cancel", self)
        # set location
        self.button_layout.addWidget(self.apply_button)
        self.button_layout.addWidget(self.cancel_button)
        # connection
        self.apply_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setLayout(layout)

    def accept(self):
        missing_objects = self.get_data()
        temp_data = copy.deepcopy(self.data)

        for geometry in temp_data:
            for joint in temp_data[geometry]:
                if joint in missing_objects.keys():
                    jnt_data = temp_data[geometry].pop(joint)
                    temp_data[geometry][missing_objects[joint]] = jnt_data

            if geometry in missing_objects.keys():
                geo_data = temp_data.pop(geometry)
                temp_data[missing_objects[geometry]] = geo_data

        if not SkinWeightManager.get_missing_objects(temp_data):
            for geometry in temp_data:
                Skin.set_weight(geometry, temp_data[geometry])

            om.MGlobal.displayInfo('Weights successfully edit and loaded!')
            super(ReplaceDialog, self).accept()
        else:
            missing_objects = SkinWeightManager.get_missing_objects(temp_data)
            error_text = 'The list still contains objects that are not in the scene: ' + ' '.join(missing_objects)
            om.MGlobal.displayError(error_text)

    def edit_namespace_add(self):
        """
        Add a prefix in all lines
        :return: pass
        """
        namespace = self.namespace_le.text()
        if not namespace:
            return
        namespace = namespace + ':' if not namespace[-1] == ':' else namespace

        for item in self.item_list:
            new_name = namespace + item.line_edit.text()
            item.line_edit.setText(new_name)

    def edit_namespace_sub(self):
        """
        The function is linked to the button to remove the prefix in all lines
        if the prefix is at the root and is completely identical to the given one (and is not the name)
        :return: pass
        """
        namespace = self.namespace_le.text()
        pattern = r'^' + namespace + ':' if not namespace[-1] == ':' else r'^' + namespace

        for item in self.item_list:
            new_name = re.sub(pattern, '', item.line_edit.text())
            item.line_edit.setText(new_name)

    def add_items(self):
        """
        Adds all objects according to the data
        :return: pass
        """
        missing_objects = SkinWeightManager.get_missing_objects(self.data)
        for name in missing_objects:
            items_widget = JointWidget(name)
            self.item_list.append(items_widget)
            self.inside_layout.addWidget(items_widget)

    def get_data(self):
        """
        Gets data from a dialog box
        :return: adjusted joint
        """
        new_names_dict = dict()
        for item in self.item_list:
            new_names_dict[item.label.text()] = item.line_edit.text()
        return new_names_dict


class JointWidget(QWidget):
    def __init__(self, name, parent=None):
        super(JointWidget, self).__init__(parent)

        # Creating widgets
        self.label = QLabel(name, self)
        self.label.setFixedWidth(150)
        self.line_edit = QLineEdit(self)
        self.line_edit.setText(name)

        self.button = QPushButton("Add selected", self)
        self.add_selected = lambda: self.line_edit.setText(cmds.ls(sl=True)[0])
        self.button.clicked.connect(self.add_selected)

        # Horizontal layout for placing widgets
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)

        # Setting the horizontal layout in the widget
        self.setLayout(layout)


class Skin:
    def __init__(self):
        pass

    @staticmethod
    def get_weight(geo):
        skinCluster = Skin.get_skin_claster(geo)
        jnts = cmds.skinCluster(skinCluster, query=True, inf=True)
        jnts = [jnt for jnt in jnts if not cmds.connectionInfo(jnt + '.worldInverseMatrix[0]', isSource=True)]
        weight = {}
        jointIndex, skinClusterIndex, skinClusterConnect, skinClusterConnectPart = [], '', '', ''  # get jnt index and weight
        sizeArray = cmds.getAttr(geo + ".cp", size=True)
        cmds.progressWindow(title='Save ' + geo + ' weights:', progress=0, status='Progress: 0%')
        for i in xrange(len(jnts)):
            cmds.progressWindow(edit=True, progress=int(len(jnts) * 0.01 * i))
            skinClusterConnect = cmds.listConnections(jnts[i] + ".worldMatrix", type='skinCluster', plugs=True)
            for skinClusterIndex in xrange(len(skinClusterConnect)):
                skinClusterConnectPart = skinClusterConnect[skinClusterIndex].split("[")
                if skinCluster + ".matrix" == skinClusterConnectPart[0]:
                    break
            jointIndex = skinClusterConnectPart[1][:-1]
            weight[jnts[i]] = cmds.getAttr(
                skinCluster + ".weightList[0:" + str(sizeArray - 1) + "].w[" + jointIndex + "]")
        weight["skinningMethod"] = cmds.getAttr(skinCluster + ".skinningMethod")
        weight["paint_weights"] = cmds.getAttr(skinCluster + ".paintWeights")  # cmds.getAttr(skinCluster+'.bw[%d]'%i)
        cmds.progressWindow(endProgress=1)
        return weight

    @staticmethod
    def set_weight(geo, weight):
        bland_attr = weight.pop("paint_weights")
        skinning_method = weight.pop("skinningMethod")

        if Skin.get_skin_claster(geo):  # unbind skin Cluster if it exists
            skCluster = Skin.get_skin_claster(geo)
            cmds.skinCluster(skCluster, e=True, unbind=True)
        cmds.select(cl=True)

        # sort	jnt forvard
        jnt = [x for x in weight.keys() if cmds.objectType(x) == 'joint'] + [x for x in weight.keys() if
                                                                             not cmds.objectType(x) == 'joint']
        skCluster = cmds.skinCluster(jnt[0], geo, tsb=True, normalizeWeights=True)[0]  # skinning

        useGeoFlag = True if [x for x in jnt if not cmds.objectType(x) == 'joint'] else False  # influense geo test
        if useGeoFlag:  cmds.setAttr(skCluster + ".useComponents", 1)
        cmds.skinCluster(skCluster, e=True, useGeometry=useGeoFlag, addInfluence=jnt[1:], wt=0.0)  # add influenses
        pointsList = range(len(weight[jnt[0]]))  # point number list
        jntAndPos = []  # joint and pos in claster list
        for jn in jnt[1:]:
            jntAndPos.append([jn,
                              [x for x in cmds.connectionInfo(jn + '.worldMatrix[0]', dfs=True) if skCluster in x][
                                  0].split(
                                  ']')[0].split('[')[1]])  # get position in clasters jnt list

        cmds.progressWindow(title='Save ' + geo + ' weights:', progress=0, status='Progress: 0%')
        p = 0
        for jn, pos in jntAndPos:  # go through all the joints except the first one and it positions in skin claster
            cmds.progressWindow(edit=True, progress=int(len(jntAndPos) * 0.01 * p))
            p += 1
            for i in pointsList:  # go through all points for carrent joint
                if weight[jn][i] > 0:  # if point weight larger than 0
                    oldWeight = cmds.getAttr(
                        skCluster + ".weightList[" + str(i) + "].w[0]")  # get point weight for first joint
                    cmds.setAttr(skCluster + ".weightList[" + str(i) + "].w[0]",
                                 oldWeight - weight[jn][i])  # correct and set point weight for first joint
                    cmds.setAttr(skCluster + ".weightList[" + str(i) + "].w[" + pos + "]",
                                 weight[jn][i])  # set point weight for carrent joint

        # rebuilds dq weights
        cmds.setAttr(skCluster + ".skinningMethod", skinning_method)
        for i, each in enumerate(bland_attr):
            cmds.setAttr(skCluster + '.bw[' + str(i) + ']', each)

        cmds.progressWindow(endProgress=1)
        return skCluster

    @staticmethod
    def get_skin_claster(geo):
        skin_cluster = cmds.ls(cmds.listHistory(geo), type='skinCluster')
        if not skin_cluster:
            shape = cmds.listRelatives(geo, s=True)[0]
            skin_cluster = cmds.ls(cmds.listHistory(shape), type='skinCluster')
        if skin_cluster:
            return skin_cluster[0]
        else:
            return None

    @staticmethod
    def copy_to_sel_vertex(sourceObj, destVert):
        """
        Copy Skin Weights from object to list of vertex on over object
        """
        destObj = destVert[0].split('.')[0]
        sourceSkin = cmds.ls(cmds.listHistory(sourceObj, pruneDagObjects=True), type='skinCluster')[0]
        influences = cmds.skinCluster(sourceSkin, query=True, influence=True)
        # find skinCluster on the destination object
        destObjSkin = cmds.ls(cmds.listHistory(destObj, pruneDagObjects=True), type='skinCluster')[0]
        destInfluences = cmds.skinCluster(destObjSkin, query=True, influence=True)
        for inf in influences:
            if cmds.nodeType(inf) == 'joint' and not inf in destInfluences:
                cmds.skinCluster(destObjSkin, edit=True, lockWeights=False, weight=0, addInfluence=inf)
        cmds.select(sourceObj, destVert)
        cmds.copySkinWeights(noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne',
                             normalize=True)
        cmds.select(cl=True)

    @staticmethod
    def copy(geo, dest_geo):
        sourceSkin = cmds.ls(cmds.listHistory(geo, pruneDagObjects=True), type='skinCluster')[0]
        influences = cmds.skinCluster(sourceSkin, query=True, influence=True)
        joints = cmds.ls(influences, type='joint')  # getting joints list on source skinCluster
        nurbs = list(set(influences) - set(joints))  # getting nurbs list on source skinCluster
        # getting state   on source skinCluster
        useComp = cmds.getAttr(sourceSkin + '.useComponents')
        skin_method = cmds.getAttr(sourceSkin + '.skinningMethod')

        # try to find history on the destination object
        hist = cmds.listHistory(dest_geo, pruneDagObjects=True)
        # try to find skinCluster on the destination object
        dest_geoSkin = cmds.ls(hist, type='skinCluster')[0] if cmds.ls(hist, type='skinCluster') else None
        if dest_geoSkin:
            cmds.skinCluster(dest_geoSkin, e=True, unbind=True)  # unbind skinCluster with deleting history
        tempJoint = None  # create new skinCluster on destination object with joints influences
        if not joints:
            cmds.select(clear=True)
            tempJoint = cmds.joint()
            joints = tempJoint
        destSkin = cmds.skinCluster(dest_geo, joints, toSelectedBones=True, useGeometry=True, dropoffRate=4,
                                    polySmoothness=False, nurbsSamples=25, rui=False, mi=5, omi=False,
                                    normalizeWeights=True)[0]
        if nurbs:  # add nurbs influences in new skinCluster
            cmds.skinCluster(destSkin, edit=True, useGeometry=True, dropoffRate=4, polySmoothness=False,
                             nurbsSamples=25,
                             lockWeights=False, weight=0, addInfluence=nurbs)

        # set state  attribute
        cmds.setAttr((destSkin + '.useComponents'), useComp)
        cmds.setAttr((destSkin + '.skinningMethod'), skin_method)

        # copy skin weights from source object to destination
        cmds.copySkinWeights(sourceSkin=sourceSkin, destinationSkin=destSkin, noMirror=True,
                             surfaceAssociation='closestPoint', influenceAssociation='oneToOne', normalize=True)
        if tempJoint:
            cmds.delete(tempJoint)  # clear template joints

        if cmds.getAttr('%s.deformUserNormals' % destSkin):  # setting up userNormals
            cmds.setAttr('%s.deformUserNormals' % destSkin, 0)


class Utilities():
    @staticmethod
    def convert_slice_to_list(selection_list):
        """
        Converts a list of strings with index ranges into a list of individual elements.
        """
        pattern = r'(.+)\[(\d+):(\d+)\]|(.+)\[(\d+)\]'
        output = list()
        for selection in selection_list:
            match = re.search(pattern, selection)
            if match:
                received_list = [x for x in match.groups() if x]
                if len(received_list) == 2:
                    output.append(received_list[0] + '[' + received_list[1] + ']')
                else:
                    elements_range = range(int(received_list[1]), int(received_list[2]) + 1)
                    output += [received_list[0] + '[' + str(i) + ']' for i in elements_range]
        return output

    @staticmethod
    def unique_names_generator(in_name, name_index_padding=3):
        """
        Generates a unique name that is not in the scene
        """
        new_name = in_name
        num_str = '{0:0' + str(name_index_padding) + 'd}'
        pref, name, num, sfx = Utilities.divide_name(in_name)
        num = int(num) if num else 0
        while not len(cmds.ls(new_name)) == 0:
            num += 1
            str_new_num = num_str.format(num)
            new_name = pref + name + str_new_num + sfx
        return new_name

    @staticmethod
    def divide_name(in_name):
        """
        Divides the object name into its component parts: prefix, name, number and suffix
        """
        pref, sfx, num, namespace = '', '', '', ''

        # get namespace
        if ':' in in_name:
            namespace = in_name.split(':')[:-1]
            namespace = ':'.join(namespace) + ':'
            in_name = in_name.split(':')[-1]

        # get prefix
        match = re.match(PFX_PATTERN, in_name)
        if match:
            pref = match.group()
            in_name = in_name.replace(pref, '')

        # get name and sfix
        in_name = in_name.split('_')
        if len(in_name) >= 2:
            name, sfx = '_'.join(in_name[:-1]), '_' + in_name[-1]
        else:
            name = in_name[0]

        # get digit
        digit_search = re.findall(DIGIT_PATTERN, name)
        if digit_search:
            num = digit_search[0]
            name = re.sub(DIGIT_PATTERN, '', name)

        if namespace:
            pref = namespace + pref

        return pref, name, num, sfx

    @staticmethod
    def distance(start, end):
        """
        Calculate the distance between two objects or coordinates
        """
        a = cmds.xform(start, q=True, t=True, ws=True) if type(start) in (str, unicode) else start
        b = cmds.xform(end, q=True, t=True, ws=True) if type(end) in (str, unicode) else end
        return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


class Mirror:
    def __init__(self, geo, pfx=['l_', 'r_'], namespace=str()):
        if namespace:
            namespace += ':' if not namespace[-1] == ':' else ''
        self.pfx = [namespace + x for x in pfx]
        self.weight = Skin.get_weight(geo)
        self.joints_in_same_position = list()
        self.geo = geo

    def mirror(self):
        # ________________________________ get a list of "problem" joints.
        self.get_joints_in_same_position()
        problem_joints_list = self.joints_in_same_position[:]

        if not self.joints_in_same_position:
            self.select_vertex_and_mirror()
            return

        # ________________________________ create temporary joints and replace weight in the list
        while problem_joints_list:
            joint = problem_joints_list.pop()
            offset = self.create_temp_joint(joint)
            opposite_joint_name = self.get_opposite_joint_name(joint)

            if opposite_joint_name in problem_joints_list:
                problem_joints_list.remove(opposite_joint_name)
                self.create_temp_joint(opposite_joint_name, offset=offset)

        # ________________________________ put weights with temporary joints, mirror and take the resulting weights
        Skin.set_weight(geo=self.geo, weight=self.weight)
        self.select_vertex_and_mirror()
        self.weight = Skin.get_weight(self.geo)

        # ________________________________ change temporary joints to permanent ones in the dictionary with weights
        for joint in self.joints_in_same_position:
            self.weight[joint] = self.weight[joint + '_tmp_joint']
            self.weight.pop(joint + '_tmp_joint')

        # ________________________________ put weights and remove temporary joints
        Skin.set_weight(geo=self.geo, weight=self.weight)
        cmds.delete([x + '_tmp_joint' for x in self.joints_in_same_position])

    def get_opposite_joint_name(self, joint):
        pattern = r"^" + self.pfx[0]
        if not re.match(pattern, joint):
            return None
        right_joint = re.sub(pattern, self.pfx[1], joint)
        return right_joint

    def get_joints_in_same_position(self, accuracy=0.01):
        joint_list = [x for x in self.weight.keys() if x not in AUXILIARY_ATTRIBUTES][:]
        joint_list.sort()
        while joint_list:
            joint = joint_list.pop()
            for i, over_jnt in enumerate(joint_list):
                if Utilities.distance(over_jnt, joint) < accuracy:
                    self.joints_in_same_position.append(joint_list.pop(i))

    def create_temp_joint(self, target_joint, offset=0.0):
        pos = cmds.xform(target_joint, q=True, t=True, ws=True)
        if not offset:
            offset = uniform(1, 5)
        pos[1] += offset
        cmds.select(cl=True)
        cmds.joint(p=pos, n=target_joint + '_tmp_joint')

        self.weight[target_joint + '_tmp_joint'] = self.weight[target_joint]
        self.weight.pop(target_joint)
        return offset

    def select_vertex_and_mirror(self, accuracy=0.01):
        vertices = cmds.ls(self.geo + '.vtx[*]', fl=True)  # all geo vertices
        if accuracy:
            vertices = [i for i in vertices if abs(cmds.pointPosition(i)[0]) > accuracy]  # remove the central row
        cmds.select(vertices)

        skin_cluster = cmds.ls(cmds.listHistory(self.geo, pdo=1), type='skinCluster')[0]
        cmds.copySkinWeights(ss=skin_cluster, ds=skin_cluster, mirrorMode='YZ', mirrorInverse=False)



def skin_weight_manager():
    dyn_win = SkinWeightManager()
    dyn_win.show()

if __name__ == '__main__':
    skin_weight_manager()

