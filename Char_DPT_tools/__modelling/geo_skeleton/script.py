import maya.cmds as cmds
import maya.OpenMaya as om
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya
import logging

VERSION = '2.00'
ROOT_JOINTS = 'ROOT', 'root'
L_EYE, R_EYE = 'eye_L', 'eye_R'
FORBIDDEN_OBJECTS = "Trajectory", "smart_target", "cam_root", "cam_anim", "surface", "GUN_ANIM", "Gun_pose", \
                    "Left_hand_hold", "Right_hand_hold", 'ik_hand_gun', 'ik_hand_root', 'hand_r_attach', \
                    'hand_l_attach', 'ik_foot_root'

ABOUT_SCRIPT = "\n" \
               "Latest updates:                                     \n" \
               "25.09.2025    -adapted for Ardena project          \n" \
               "23.01.2023    -Add eyes                             \n" \
               "13.02.2022    -First version created                \n" \
               "                                                    \n" \
               "Created by Andrey Belyaev                           \n" \
               "andreikin@mail.ru"

HELP_LABEL = "Creates a geometric copy of the skeleton. If  skeleton exist,\n" \
             "it is recreated. The skeleton will be created under the child joints\n" \
             'of the locator "ROOT" or "root"'

HELP_TEXT = "\n" \
            "Bone thickness :  attribute is responsible for the total thickness of the \n" \
            "generated geometric bone\n" \
            "\n" \
            "Thickness of small bones - attribute defines the thickness of small bones. \n" \
            "At the maximum value, the thickness of these bones will correspond to the \n" \
            "thickness of the largest bone in the skeleton\n"

logger = logging.getLogger(__name__)
logger.handlers = []
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s  line: %(lineno)s   - function  %(funcName)s() %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class PolyJoint:
    def __init__(self, joint, width=1):
        self.joint = joint
        self.width = width
        self.child = self.get_child()
        self.length = self.get_length()

    def get_child(self):
        child = cmds.listRelatives(self.joint, children=True)
        child = [x for x in child if x not in FORBIDDEN_OBJECTS]
        child_lst = [[x, CreateSkeletonUi.distans(self.joint, x)] for x in child]
        return sorted(child_lst, key=lambda x: x[1])[-1][0]

    def get_length(self):
        length = CreateSkeletonUi.distans(self.joint, self.child)
        if length < 0.000001:
            parent = cmds.listRelatives(self.joint, parent=True)
            length = CreateSkeletonUi.distans(self.joint, parent[0])
        if length < 0.000001:
            length = 1
        return length

    def create(self):
        self.create_poly_locator()
        self.create_poly_cylinder()
        self.create_poly_cub()
        self.grp = cmds.group(name=self.joint + "_grp", em=True)
        self.place_on_jnt()
        return self.grp

    def create_poly_locator(self):
        size, width = self.width, self.width / 100.0
        self.locator = cmds.polyUnite(cmds.polyCube(w=size, h=width, d=width),
                                      cmds.polyCube(w=width, h=size, d=width),
                                      cmds.polyCube(w=width, h=width, d=size),
                                      name=self.joint + "_loc",
                                      ch=False)

    def create_poly_cylinder(self):
        size = self.width / 3.0
        self.cylinder = cmds.polyCylinder(name=self.joint + "_cylinder",
                                          axis=[0, 0, 1],
                                          subdivisionsZ=1,
                                          radius=size,
                                          height=size / 2.0)[0]

    def create_poly_cub(self):
        size = self.width / 3.0
        end_scale = 1
        self.cub = cmds.polyCube(w=self.length, h=size, d=size, name=self.joint + "_cub")[0]
        clast = cmds.cluster([self.cub + ".vtx[1]", self.cub + ".vtx[3]", self.cub + ".vtx[5]", self.cub + ".vtx[7]"])[
            1]
        cmds.setAttr(clast + ".scale", end_scale, end_scale, end_scale)
        clast = cmds.cluster(self.cub)[1]
        cmds.setAttr(clast + ".translateX", self.length / 2)
        cmds.delete(self.cub, ch=True)

    def place_on_jnt(self):
        cmds.parent(self.locator, self.cylinder, self.cub, self.grp)

        cmds.delete(cmds.pointConstraint(self.joint, self.grp, mo=False))
        cmds.delete(cmds.aimConstraint(self.child, self.grp,
                                       worldUpType="objectrotation",
                                       worldUpObject=self.joint,
                                       upVector=[0, 0, 1],
                                       worldUpVector=[0, 0, 1],
                                       mo=False))
        if self.joint in ["CENTRE", "HANDL", "HANDR"]:
            cmds.delete(cmds.parentConstraint(self.joint, self.grp, mo=False))
            if cmds.objExists("HANDR_cub.scaleX"):
                cmds.setAttr("HANDR_cub.scaleX", -1)


class CreateSkeletonUi(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(CreateSkeletonUi, self).__init__()
        self.setWindowTitle("Create polygonal skeleton v"+VERSION)
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)

        # menu_bar
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        menu = QMenu("Help")
        menu_bar.addMenu(menu)
        help_action = QAction("Help", self)
        menu.addAction(help_action)
        help_action.triggered.connect(lambda: self.text_dialog("Help"))
        about_script_action = QAction("About script", self)
        menu.addAction(about_script_action)
        about_script_action.triggered.connect(lambda: self.text_dialog("ABOUT_PROGRAM"))

        # text 
        self.help_label = QLabel(HELP_LABEL)
        self.verticalLayout.addWidget(self.help_label)

        # option_box 
        self.option_box = QGroupBox("Options:")
        self.option_box_layout = QVBoxLayout(self.option_box)

        # Joint width slider
        labels_width = 138
        self.joint_width = QLabel("Bone thickness :")
        self.joint_width.setFixedSize(labels_width, 20)

        self.width_slider = QSlider()
        self.width_slider.setRange(1, 20)
        self.width_slider.setSliderPosition(5)
        self.width_slider.setFixedSize(200, 20)
        self.width_slider.setOrientation(Qt.Horizontal)

        self.width_lineEdit = QLineEdit()
        self.width_lineEdit.setReadOnly(True)
        self.width_lineEdit.setFixedSize(50, 20)
        self.width_lineEdit.setText(str(0.5))
        self.width_slider.valueChanged.connect(self.widthHandler)

        # End joint slider
        self.end_width_lebel = QLabel("Thickness of small bones:")
        self.end_width_lebel.setFixedSize(labels_width, 20)

        self.end_width_slider = QSlider()
        self.end_width_slider.setFixedSize(200, 20)
        self.end_width_slider.setRange(0, 10)
        self.end_width_slider.setSliderPosition(1)
        self.end_width_slider.setOrientation(Qt.Horizontal)

        self.end_width_lineEdit = QLineEdit()
        self.end_width_lineEdit.setReadOnly(True)
        self.end_width_lineEdit.setFixedSize(50, 20)
        self.end_width_lineEdit.setText(str(0.1))
        self.end_width_slider.valueChanged.connect(self.valueHandler)

        grid = QGridLayout()  #
        grid.addWidget(self.joint_width, 0, 0)
        grid.addWidget(self.width_slider, 0, 1)
        grid.addWidget(self.width_lineEdit, 0, 2)
        grid.addWidget(self.end_width_lebel, 1, 0)
        grid.addWidget(self.end_width_slider, 1, 1)
        grid.addWidget(self.end_width_lineEdit, 1, 2)
        self.option_box_layout.addLayout(grid)
        self.verticalLayout.addWidget(self.option_box)

        # buttons 
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(3)
        self.button_close = QPushButton("Close")
        self.buttons_layout.addWidget(self.button_close)
        self.button_close.clicked.connect(self.close)

        self.create_button = QPushButton("Create")
        self.buttons_layout.addWidget(self.create_button)
        self.verticalLayout.addLayout(self.buttons_layout)
        self.create_button.clicked.connect(self.create_skeleton)
        logger.debug(" executed")

    def widthHandler(self, value):
        """
        Solve value for width_lineEdit
        """
        scaledValue = float(value) / 10
        self.width_lineEdit.setText(str(scaledValue))

    def valueHandler(self, value):
        """
        Solve value for end_width_lineEdit
        """
        scaledValue = float(value) / 10
        self.end_width_lineEdit.setText(str(scaledValue))

    @staticmethod
    def blend_two_art(atr1, atr2, blend):
        """
         Mixes two attributes and outputs the average
         value according to the mix attribute
        """
        return atr1 + (atr2 - atr1) * blend

    @staticmethod
    def distans(start, end):
        from math import sqrt
        a = cmds.xform(start, q=True, t=True, ws=True) if type(start) == str or type(start) == unicode else start
        b = cmds.xform(end, q=True, t=True, ws=True) if type(end) == str or type(end) == unicode else end
        xy = sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]))
        return sqrt(xy * xy + (a[2] - b[2]) * (a[2] - b[2]))

    @staticmethod
    def prohibited_objects_filtr(jnt_list):
        out_list = []
        while jnt_list:
            curent_jnt = jnt_list.pop()
            if curent_jnt in FORBIDDEN_OBJECTS:
                continue
            if '_twist_' in curent_jnt:
                continue
            if '_correctiveRoot_' in curent_jnt:
                continue
            if curent_jnt in ROOT_JOINTS:
                continue
            out_list.append(curent_jnt)
        return out_list


    @staticmethod
    def end_jnt_filtr(jnt_list):
        out_list = []
        while jnt_list:
            curent_jnt = jnt_list.pop()
            child = cmds.listRelatives(curent_jnt, children=True, fullPath=True)
            if child and any([cmds.nodeType(x) == "joint" for x in child]):
                out_list.append(curent_jnt)
        return out_list

    def get_root_jnt(self):
        for jnt in ROOT_JOINTS:
            if cmds.objExists(jnt):
                return jnt
        om.MGlobal.displayError('"ROOT" object not found, The script creates a polygonal skeleton for the child '
                                'objects of the "ROOT" object')
        return None

    def create_skeleton(self):

        width = float(self.width_lineEdit.text())
        end_width = float(self.end_width_lineEdit.text())
        root_jnt = self.get_root_jnt()
        if root_jnt:
            cmds.select(root_jnt)
            jnt_name = cmds.ls(sl=True)[0]
            cmds.select(hi=True)
            all_jnt = cmds.ls(sl=True, type="joint")
            cmds.select(jnt_name)

            # filtr
            all_jnt = self.end_jnt_filtr(all_jnt)
            all_jnt = self.prohibited_objects_filtr(all_jnt)

            # create geo
            grp = "skeleton_geo"
            if cmds.objExists(grp):
                cmds.delete(grp)
            grp = cmds.group(n=grp, em=True)

            max_length = max(PolyJoint(x).get_length() for x in all_jnt)

            for jnt in all_jnt:
                length = PolyJoint(jnt).get_length()
                length = self.blend_two_art(length, max_length, end_width)
                geo_jnt = PolyJoint(jnt, length * width).create()
                cmds.parent(geo_jnt, grp)

            if cmds.objExists(L_EYE) and cmds.objExists(R_EYE):
                self.create_eyes()

    def create_eyes(self):
        for jnt in L_EYE, R_EYE:
            radius = CreateSkeletonUi.distans(L_EYE, R_EYE) / 3
            geo = cmds.polySphere(n=jnt + "_sphere", axis=[1, 0, 0], r=radius)[0]
            cmds.delete(cmds.parentConstraint(jnt, geo, mo=False))
            cmds.parent(geo, "skeleton_geo")

    def text_dialog(self, text_type):
        """
        'Help window' or 'About program' text dialog
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        if text_type == "Help":
            help_dialog.setWindowTitle("Help window")
            help_dialog.setText(HELP_TEXT)
        else:
            help_dialog.setWindowTitle("About program")
            help_dialog.setText(ABOUT_SCRIPT)
        help_dialog.setStandardButtons(QMessageBox.Cancel)
        help_dialog.exec_()


def geo_skeleton():

    dyn_win = CreateSkeletonUi()
    dyn_win.show()


geo_skeleton()
