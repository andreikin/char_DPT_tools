from __future__ import absolute_import

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.mel as mm

from rigging_kit.utilities import distance
from rigging_kit.names import unique_names_generator, divide_name, suffix_minus
from rigging_kit.controller import Controller
from rigging_kit.connect import an_connectRigVis
from rigging_kit.maya_widgets import FloatSliderGrp, TextFieldButtonGrp, RadioButtonGrp


"""
Ensure that the Timeline is always on 1 or 0 when making curves dynamic.
Ensure that viewport 2.0 is paused during the Make selected Curves Dynamic action.
Set the evaluation mode to DG by navigating to Windows > Preferences > and click the Animation tab under Settings.
"""

ABOUT_SCRIPT = "\n" \
               "Latest updates:                                     \n" \
               "18.10.2022    -Remove matchTransform                 \n" \
               "11.10.2022    -Made the first version               \n" \
               "                                                    \n" \
               "Created by Andrey Belyaev                           \n" \
               "andreikin@mail.ru"

HELP_LABEL = "Select the desired joint (it must have a parent and a child),\n" \
             "specify the axis with less activity as the up.\n"

HELP_TEXT = "\n" \
            "- The bone for which the dynamic system will be made must be\n" \
            "   oriented and have a parent and a child.\n\n" \
            "- The behavior of the dynamics depends on the scale of the entire \n" \
            "   system. However, this can be fixed in Nucleus Solver.\n\n" \
            "- The main group that everything is in has an attribute that hides or\n" \
            "   shows the entire rig\n"


DEFAULT_PREFIX = "pendant001"

def create_dynamics_curve(input_curve):
    """ new """
    data = dict()
    cmds.select(input_curve)
    mm.eval('makeCurvesDynamic 2 { "0", "0", "1", "1", "0"};')
    crv_shape = cmds.listRelatives(input_curve, shapes=True)[0]
    data['follicle'] = cmds.listConnections(crv_shape + ".local")[0]
    data['follicle_shape'] = cmds.listRelatives(data['follicle'], s=True)[0]
    dyn_curve_shape = cmds.connectionInfo(data['follicle_shape'] + ".outCurve", destinationFromSource=True)[0].split('.')[0]
    data['dyn_curve'] = cmds.listRelatives(dyn_curve_shape, parent=True)[0]
    data['hair_sys_shape'] = cmds.connectionInfo(data['follicle_shape'] + ".outHair", destinationFromSource=True)[0].split('.')[0]
    data['hair_sys'] = cmds.listRelatives(data['hair_sys_shape'], parent=True)[0]
    data['dyn_curve_grp'] = cmds.listRelatives(data['dyn_curve'], parent=True)[0]
    return data


class DynamicsPendantSys():

    def __init__(self, **kwargs):
        self.sfx = "_grp"
        self.name = kwargs.setdefault("name", 'pendant001')
        self.name = suffix_minus(unique_names_generator(self.name + self.sfx))
        self.jnt = kwargs.setdefault("jnt", None)
        self.parent = kwargs.setdefault("parent", None)
        self.up_axis = kwargs.setdefault("up_axis", None)
        self.jnt_end = kwargs.setdefault("jnt_end", None)
        self.size = kwargs.setdefault("size", None)
        self.points_num = kwargs.setdefault("points_num", 5)  # min 5

        self.create()

    def create(self):
        if self.verification():
            self.side = 1 if cmds.getAttr(self.jnt_end + ".tx") > 0.001 else -1
            if not self.size:
                self.size = distance(self.jnt, self.jnt_end)

            self.rig_grp = cmds.group(n=self.name + self.sfx, em=True)
            self.jnt_grp = cmds.group(n=self.name + "Jnt_grp", em=True)
            self.up_grp = cmds.group(n=self.name + "Up_grp", em=True)
            self.scale_grp = cmds.group(self.jnt_grp, self.up_grp, n=self.name + "Scale_grp", )

            self.aim_grp = cmds.group(n=self.name + "Aim_grp", em=True)
            self.input_curve = self.create_curve()

            tmp_grp = cmds.group(em=True)
            cmds.parent(self.scale_grp, self.aim_grp, self.input_curve, tmp_grp)
            cmds.setAttr(self.up_grp + ".t" + self.up_axis.lower(), self.size * self.side)

            cmds.setAttr(self.input_curve + ".tx", self.size * 4 * self.side)
            #cmds.matchTransform(tmp_grp, self.jnt)
            cmds.delete(cmds.parentConstraint(self.jnt, tmp_grp, mo=False))
            cmds.ungroup(tmp_grp)

            cmds.parent(self.scale_grp, self.aim_grp, self.input_curve, self.rig_grp)
            self.rig_grp = cmds.group(self.scale_grp, self.aim_grp, self.input_curve,
                                      n=self.name + self.sfx)
            cmds.parentConstraint(self.parent, self.scale_grp, mo=True)
            self.create_controller()
            self.dynamic_curve()

            m_path = cmds.pathAnimation(self.aim_grp, c=self.dyn_curve)
            cmds.delete(cmds.listConnections(m_path, s=True, type="animCurveTL"))
            cmds.setAttr(m_path + ".uValue", self.points_num - 3)

            up_vector = {"Y": [0, 1, 0], "Z": [0, 0, 1]}[self.up_axis]
            cmds.aimConstraint(self.aim_grp, self.jnt_grp, aim=[1 * self.side, 0, 0], mo=False,
                               upVector=up_vector,
                               worldUpType="object",
                               worldUpObject=self.up_grp)

            cmds.parentConstraint(self.ctrl.name, self.jnt, mo=True)
            cmds.scaleConstraint(self.parent, self.scale_grp, mo=True)

            an_connectRigVis(self.rig_grp, [self.input_curve, self.follicle, self.dyn_curve, self.haer_sys_grp])

    def create_controller(self):
        ct_obj = {'name': self.name + "_ct",
                  'color': 13,
                  'shape': 'roll',
                  'size': self.size * 0.5,
                  'translate': [self.size * 3 * self.side, 0, 0],
                  'rotate': [0, 0, -90 * self.side],
                  'align_obj': self.jnt,
                  'parent': self.scale_grp,
                  'hid_attr': ['sx', 'sy', 'sz', 'v']
                  }
        self.ctrl = Controller(**ct_obj)
        self.ctrl.create()
        cmds.addAttr(self.ctrl.name, longName='dyn_Y', keyable=True, defaultValue=2)
        cmds.addAttr(self.ctrl.name, longName='dyn_Z', keyable=True, defaultValue=2)

        mdv = cmds.createNode('multiplyDivide', n=self.name + 'MDV')
        cmds.connectAttr(self.ctrl.name + '.dyn_Y', mdv + '.input1X')
        cmds.connectAttr(self.jnt_grp + '.ry', mdv + '.input2X')
        cmds.connectAttr(mdv + '.outputX', self.ctrl.conGrp + '.ry', f=True)

        cmds.connectAttr(self.ctrl.name + '.dyn_Z', mdv + '.input1Y')
        cmds.connectAttr(self.jnt_grp + '.rz', mdv + '.input2Y')
        cmds.connectAttr(mdv + '.outputY', self.ctrl.conGrp + '.rz', f=True)

    def create_curve(self):
        segment = self.size * 3.0 / self.points_num * self.side
        points = [(x * segment, 0, 0) for x in range(self.points_num)]
        curve = cmds.curve(n=self.name + "Input_crv", p=points, d=3)
        return curve

    def dynamic_curve(self):
        data = create_dynamics_curve(self.input_curve)
        self.follicle = cmds.rename(data['follicle'], self.name + '_follicle')
        cmds.setAttr(self.follicle + ".pointLock", 1)
        cmds.parent(self.follicle, self.scale_grp)

        cmds.setAttr(data['hair_sys_shape'] + ".stretchResistance", 100)
        cmds.setAttr(data['hair_sys_shape'] + ".damp", 0.1)
        cmds.setAttr(data['hair_sys_shape'] + ".drag", 0.01)

        # cmds.parentConstraint(self.parent, self.follicle, mo=True)
        self.curve_grp = cmds.rename(data['dyn_curve_grp'], self.name + 'DynCurve_grp')
        cmds.parent(self.curve_grp, self.rig_grp)
        self.dyn_curve = cmds.rename(data['dyn_curve'], self.name + 'Dyn_curve')
        self.haer_sys_grp = cmds.rename(data['hair_sys'], self.name + 'HairSys_grp')
        cmds.parent(self.haer_sys_grp, self.rig_grp)

    def verification(self):
        if not self.parent:
            self.parent = cmds.listRelatives(self.jnt, parent=True)[0]
            if not self.parent:
                om.MGlobal.displayError('Dynamic joint must have a parent object!')
                return False
        if not self.jnt_end:
            self.jnt_end = cmds.listRelatives(self.jnt, children=True)[0]
            if not self.jnt_end or not cmds.nodeType(self.jnt_end) == u'joint':
                om.MGlobal.displayError('Dynamic joint must have a children joint!')
                return False
        self.name = unique_names_generator(self.name + self.sfx)[:-len(self.sfx)]
        self.points_num = 5 if self.points_num < 5 else self.points_num
        return True


class PandantDyn_Ui(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(PandantDyn_Ui, self).__init__()
        self.setWindowTitle("Pandant rigging system v.01")
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
        self.help_label.setMaximumSize(QSize(1000, 50))
        self.verticalLayout.addWidget(self.help_label)

        # option_box
        self.option_box = QGroupBox("Options:")
        self.option_box_layout = QVBoxLayout(self.option_box)

        self.name_line_edit = TextFieldButtonGrp(label="System name:", button=False)
        self.option_box_layout.addWidget(self.name_line_edit)

        self.size_float_grp = FloatSliderGrp("Global scale")
        self.option_box_layout.addWidget(self.size_float_grp)
        self.size_float_grp.setRange(0.1, 3.0)
        self.size_float_grp.setValue(0.2)

        self.rad_btn_grp = RadioButtonGrp("Up axis", labelArray=["Z", "Y"])
        self.option_box_layout.addWidget(self.rad_btn_grp)
        self.verticalLayout.addWidget(self.option_box)

        # buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(3)
        self.button_close = QPushButton("Close")
        self.buttons_layout.addWidget(self.button_close)
        self.button_close.clicked.connect(self.close)

        self.create_button = QPushButton("Create dynamics system")
        self.buttons_layout.addWidget(self.create_button)
        self.verticalLayout.addLayout(self.buttons_layout)
        self.create_button.clicked.connect(self.create)

    def create(self):
        jnt = cmds.ls(sl=True)[0] if cmds.ls(sl=True) else None
        data = {
            "name": self.name_line_edit.text(),
            "size": float(self.size_float_grp.value()[1]),
            "up_axis": self.rad_btn_grp.select(),
            "jnt": jnt
        }
        DynamicsPendantSys(**data)

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
        logger.debug(" executed")

def dynamics_pendant():
    win = PandantDyn_Ui()
    win.show()


if __name__ == '__main__':
    dynamics_pendant()
