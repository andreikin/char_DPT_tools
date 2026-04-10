import math
import tempfile
import webbrowser
import maya.cmds as cmds
import maya.mel as mm
import pymel.core as pm
import os

from math import sqrt
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya


ABOUT_SCRIPT = "\n" \
               "Latest updates:                                     \n" \
               "14.03.2025    -refaktoring                          \n" \
               "15.12.2022    -add 'Build fk hierarchy'             \n" \
               "15.12.2022    -fix proportional stretch             \n" \
               "19.05.2021    -add proportional stretch             \n" \
               "                                                    \n" \
               "Created by Andrey Belyaev                           \n" \
               "andreikin@mail.ru"

HELP_LABEL = "To create a flexible control system, sequentially \nselect a chain of joints\n"

HELP_TEXT = "\n" \
            "1 Necessary to select a chain of bones in the order of their hierarchy.\n\n" \
            '2 If it is necessary for the chain to proportionally change the distance \n' \
            "    between the joints during deformation, select 'Proportional stretch' \n"

URL ="https://youtu.be/EhfJjGni6N4"

DEFAULT_PREFIX = "ribbon"
RIBBON_PROPORTION = 15
MAX_CONTROLS_NUM = 20
DEFAULT_CONTROLS_NUM = 5
CONTROLS_SIZE = 1

LEFT_PART_SIZE = 200

class UiTemplate(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(UiTemplate, self).__init__()
        self.widget_list = list()
        self.settings_file = None

    def add_menu(self):
        # menu_bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.menu = QMenu("Help")
        self.menu_bar.addMenu(self.menu)

        self.help_action = QAction("Help", self)
        self.menu.addAction(self.help_action)

        self.about_script_action = QAction("About script", self)
        self.menu.addAction(self.about_script_action)

    def get_data(self, widget_list):
        data = dict()
        for widget in widget_list:
            text, val = widget.value()
            data[text] = val
        return data

    def load_settings(self, set_settings):
        """
        If settings not exist - load default settings
        """
        try:
            if self.settings_file:
                settings = QSettings(self.settings_file, QSettings.IniFormat)
                if settings.contains("ui settings"):
                    data = settings.value("ui settings")
                    set_settings(data)
                if settings.contains("ui position"):
                    x, y = settings.value("ui position")
                    self.move(int(x), int(y))
        except Exception as message:
            print(message)

    def closeEvent(self, evt):
        """
        When window closed it save fields settings
        """
        if self.settings_file:
            settings = QSettings(self.settings_file, QSettings.IniFormat)
            data = self.get_data(self.widget_list)
            settings.setValue("ui settings", data)
            settings.setValue("ui position", [self.x(), self.y()])

    @staticmethod
    def text_dialog(text_data):
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


class RibbonRigSystemUi(UiTemplate, MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(RibbonRigSystemUi, self).__init__()
        self.setWindowTitle("Ribbon rigging system v.04")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)

        # menu_bar
        self.add_menu()
        self.help_action.triggered.connect(lambda: self.text_dialog(HELP_TEXT))
        self.about_script_action.triggered.connect(lambda: self.text_dialog(ABOUT_SCRIPT))

        video_action = QAction("Show help video", self)
        self.menu.insertAction(self.about_script_action, video_action)
        video_action.triggered.connect(lambda: webbrowser.open_new(URL))

        # text
        self.help_label = QLabel(HELP_LABEL)
        self.verticalLayout.addWidget(self.help_label)

        # option_box
        self.option_box = QGroupBox("Options:")
        self.option_box_layout = QVBoxLayout(self.option_box)
        self.option_box_layout.setSpacing(15)
        #self.form_layout = QFormLayout()

        # text line Prefix
        self.pfx_lineEdit = TextFieldButtonGrp(label="Prefix:", button=False)
        self.option_box_layout.addWidget(self.pfx_lineEdit)

        self.ct_number = intSliderGrp("Controllers number :")
        self.option_box_layout.addWidget(self.ct_number)
        self.ct_number.setRange(0.1, MAX_CONTROLS_NUM)
        self.ct_number.setValue(DEFAULT_CONTROLS_NUM)

        self.size_float_grp = FloatSliderGrp("Controller size :")
        self.option_box_layout.addWidget(self.size_float_grp)
        self.size_float_grp.setRange(0.1, 5.0)
        self.size_float_grp.setValue(CONTROLS_SIZE)

        self.stretch_check = CheckBoxGrp("Proportional stretch :")
        self.stretch_check.check_box.setCheckState(Qt.Checked)
        self.option_box_layout.addWidget(self.stretch_check)

        self.fk_check_box = CheckBoxGrp("Build fk hierarchy :")
        self.fk_check_box.check_box.setCheckState(Qt.Checked)
        self.option_box_layout.addWidget(self.fk_check_box)
        self.verticalLayout.addWidget(self.option_box)

        self.h_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.h_layout.addWidget(close_button)

        create_button = QPushButton("Create system")
        create_button.clicked.connect(self.create_rig)
        self.h_layout.addWidget(create_button)
        self.verticalLayout.addLayout(self.h_layout)

        self.widget_list = self.pfx_lineEdit, self.ct_number, self.size_float_grp, self.stretch_check, self.fk_check_box

        # object for save settings
        self.settings_file = os.path.join(tempfile.gettempdir(), 'ribbon_rig_system_v2_settings.ini')
        self.load_settings(self.set_settings)


    def set_settings(self, data):
        if not data['Prefix:']:
            data['Prefix:'] = DEFAULT_PREFIX

        self.pfx_lineEdit.setText(data['Prefix:'])
        self.ct_number.setValue(data['Controllers number :'])
        self.size_float_grp.setValue(data['Controller size :'])

        val = Qt.Checked if data['Proportional stretch :'] else Qt.Unchecked
        self.stretch_check.check_box.setCheckState(val)

        val = Qt.Checked if data['Build fk hierarchy :'] else Qt.Unchecked
        self.fk_check_box.check_box.setCheckState(val)




class RibbonRigSystemRig(RibbonRigSystemUi):
    def create_rig(self):
        """
        main rigging function
        """
        data = self.get_data([self.pfx_lineEdit, self.ct_number, self.size_float_grp, self.stretch_check,
                              self.fk_check_box])

        self.prefx = data['Prefix:']
        self.ctrl_number = data["Controllers number :"]
        self.build_fk = data["Build fk hierarchy :"]
        self.ctrl_size = data["Controller size :"]

        self.joints = cmds.ls(sl=True)
        self.rig_grp = cmds.group(empty=True, name=self.prefx + 'Rig_grp')

        self.create_nurbs()
        self.create_controls()
        if data["Proportional stretch :"]:
            self.create_proportional_stretch()
        self.create_follicles()

        cmds.setAttr(self.rig_grp + ".v", 0)

    def create_nurbs(self):
        """
        in places of bones, curves are created on the basis of which a nurbs surface is created
        """
        length = distance(self.joints[0], self.joints[-1])
        width = length / RIBBON_PROPORTION
        base_crv = cmds.curve(d=1, p=([0, 0, width / 2], [0, 0, width / -2]))
        loft_curves = []
        for jnt in self.joints:
            l_curve = cmds.duplicate(base_crv)[0]
            cmds.delete(cmds.parentConstraint(jnt, l_curve))
            loft_curves.append(l_curve)
        self.nurbs = cmds.loft(loft_curves, n=self.prefx + 'Nurbs_geo', ch=False, rn=True, ar=True)[0]
        cmds.rebuildSurface(self.nurbs, constructionHistory=False, replaceOriginal=True, rebuildType=0,
                            endKnots=1, keepRange=0, keepControlPoints=0, keepCorners=0, spansU=self.ctrl_number - 1,
                            degreeU=3, spansV=0, degreeV=1, tol=0.01, fr=0, dir=2)
        cmds.delete(loft_curves, base_crv)
        cmds.parent(self.nurbs, self.rig_grp)

    def create_controls(self):
        """
        With the help of the follicle, we find the U coordinate on the nurbs surface.
        In this place we place the controller
        """
        self.ctrl_grp = cmds.group(empty=True, name=self.prefx + 'Controls_grp')
        folic = self.create_follicle_on_nurbs(self.nurbs, uPos=0.0, vPos=0.5)
        f_transf = folic.getParent().name()
        self.ctrl_jnts_list = []
        self.ctrl_list = []
        self.grp_list = []
        for i in range(self.ctrl_number):
            folic.parameterU.set(1.0 / (self.ctrl_number - 1) * i)
            ctrl, oriGrp, jnt = self.ctrl(name=self.prefx + str(i), place_obj=f_transf, size=self.ctrl_size)
            self.ctrl_jnts_list.append(jnt)
            self.ctrl_list.append(ctrl)
            self.grp_list.append(oriGrp)
            cmds.parent(oriGrp, self.ctrl_grp)
            if self.build_fk and i:
                cmds.parent(oriGrp, self.ctrl_list[i - 1])

        cmds.delete(f_transf)
        cmds.skinCluster(self.ctrl_jnts_list, self.nurbs, tsb=True, normalizeWeights=True)

    def create_proportional_stretch(self):
        """
        Based on the nurbs surface creates a polygonal, based on the edges of which another nurbs surface is created.
        """
        plane = cmds.nurbsToPoly(self.nurbs, ch=True, mnd=1, f=2, pt=1, pc=200, chr=0.9, ft=0.01, mel=0.001, d=0.1,
                                 ut=1, un=self.ctrl_number * 3, vt=1, vn=1, uch=0, ucr=0, cht=0.2, es=0, ntr=0,
                                 name=self.prefx + 'Poly_geo', mrt=0, uss=1)[0]
        cmds.select(plane + ".e[0]")
        mm.eval('performSelContiguousEdges(0);')
        curve_a = mm.eval('polyToCurve -form 2 -degree 3 -conformToSmoothMeshPreview 1;')[0]
        cmds.select(plane + ".e[2]")
        mm.eval('performSelContiguousEdges(0);')
        curve_b = mm.eval('polyToCurve -form 2 -degree 3 -conformToSmoothMeshPreview 1;')[0]
        self.nurbs = cmds.loft([curve_a, curve_b], ch=True, rn=True, ar=True, reverseSurfaceNormals=True)[0]
        cmds.parent(plane, self.nurbs, curve_a, curve_b, self.rig_grp)

    def create_follicles(self):
        """
        Create a set of follicles to which we constrain the bones
        """
        # get global length
        jnt_length = self.jnt_len_sum(self.joints)

        for i, jnt in enumerate(self.joints):
            pos = self.jnt_len_sum(self.joints[i:])
            u_val = 1 - 1 / (jnt_length / pos) if pos else 1.0
            folic = self.create_follicle_on_nurbs(self.nurbs, uPos=u_val, vPos=0.5)

            if not jnt == self.joints[-1]:
                cmds.parentConstraint(folic.getParent().name(), jnt, mo=True)
            else:
                cmds.parentConstraint(self.ctrl_list[-1], jnt, mo=True)
            cmds.parent(folic.getParent().name(), self.rig_grp)

    @staticmethod
    def ctrl(name, place_obj=None, size=1):
        """
        create fk controller
        """
        ctrl = cmds.circle(nr=(1, 0, 0), r=size / 2.0, ch=False, n=name + "_CT")[0]
        oriGrp = cmds.group(ctrl, n=name + '_ori')
        cmds.select(cl=True)
        jnt = cmds.joint(n=name + '_jnt')
        cmds.setAttr(jnt + ".v", 0)
        cmds.parent(jnt, ctrl)

        if place_obj:
            cmds.delete(cmds.parentConstraint(place_obj, oriGrp, mo=False))
        for attr in ['sx', 'sy', 'sz', 'v']:
            cmds.setAttr(ctrl + "." + attr, lock=True, keyable=False)
        cmds.setAttr(ctrl + ".overrideEnabled", 1)
        cmds.setAttr(ctrl + ".overrideColor", 17)
        return ctrl, oriGrp, jnt

    @staticmethod
    def create_follicle_on_nurbs(nurbs, uPos=0.0, vPos=0.0):
        """
        creates a follicle on the nurbs surface
        """
        nurbs = pm.ls(nurbs, type='transform')[0]
        nurbs = nurbs.getShape()
        pName = '_'.join((nurbs.name(), 'follicle', '#'.zfill(2)))
        folic = pm.createNode('follicle', name=pName)
        nurbs.local.connect(folic.inputSurface)
        nurbs.worldMatrix[0].connect(folic.inputWorldMatrix)
        folic.outRotate.connect(folic.getParent().rotate)
        folic.outTranslate.connect(folic.getParent().translate)
        folic.parameterU.set(uPos)
        folic.parameterV.set(vPos)
        folic.getParent().t.lock()
        folic.getParent().r.lock()
        return folic

    @staticmethod
    def create_follicle_on_poly(mesh, u_pos=0.5, v_pos=0.5):
        follicle = cmds.createNode('follicle')
        follicleTrans = cmds.listRelatives(follicle, p=True)
        cmds.connectAttr(follicle + '.outRotate', follicleTrans[0] + '.rotate')
        cmds.connectAttr(follicle + '.outTranslate', follicleTrans[0] + '.translate')
        cmds.connectAttr(mesh + '.worldMatrix', follicle + '.inputWorldMatrix')
        cmds.connectAttr(mesh + '.outMesh', follicle + '.inputMesh')
        cmds.setAttr(follicle + '.simulationMethod', 0)
        cmds.setAttr(follicle + '.parameterU', u_pos)
        cmds.setAttr(follicle + '.parameterV', v_pos)
        return follicleTrans

    @staticmethod
    def jnt_len_sum(joints):
        """
        measures the length of a chain of bones
        """
        out_sum = 0.0
        if len(joints) > 1:
            for i in range(1, len(joints)):
                out_sum += distance(joints[i - 1], joints[i])
            return out_sum
        else:
            return 0.0


class TextFieldButtonGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, label='Label', button=True, buttonLabel='Button', add_selected=False, parent=None,  ):
        QWidget.__init__(self, parent)
        self.label = label
        self.buttonLabel = buttonLabel

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(label)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.line_edit = QLineEdit()
        self.line_edit.setClearButtonEnabled(True)
        self.layout.addWidget(self.line_edit)
        if button:
            self.button = QPushButton(self.buttonLabel)
            self.layout.addWidget(self.button)
        if add_selected:
            self.button.setText("Add selected")
            self.button.clicked.connect(self.add_sel_object)

    def add_sel_object(self):
        sel = cmds.ls(sl=True)[0]
        self.line_edit.setText(sel)

    def value(self):
        return self.lebel.text(), self.line_edit.text()

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

    def set_fixed_hight(self, val):
        self.button.setFixedHeight(val)
        self.line_edit.setFixedHeight(val)
        self.lebel.setFixedHeight(val)


class FloatSliderGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(attribut)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.slider = QSlider()
        self.slider.setRange(1, 50)
        self.slider.setSliderPosition(10)
        self.slider.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        self.line_edit = QLineEdit()
        # self.line_edit.setMaximumSize(QSize(49, 20))
        self.line_edit.setFixedWidth(50)
        self.layout.addWidget(self.line_edit)
        self.line_edit.setText(str(1.0))
        self.slider.valueChanged.connect(self.valueHandler)

    def valueHandler(self, value):
        scaledValue = float(value) / 10
        self.line_edit.setText(str(scaledValue))

    def value(self):
        return self.lebel.text(), float(self.line_edit.text())

    def setRange(self, start, end):
        self.slider.setRange(start * 10, end * 10)

    def setValue(self, value):
        self.slider.setValue(value * 10)


class intSliderGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, value=1, parent=None):
        QWidget.__init__(self, parent, )

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(attribut)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.slider = QSlider()
        self.slider.setRange(1, 50)
        self.slider.setSliderPosition(value)
        self.slider.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        self.spin_box = QSpinBox()
        self.layout.addWidget(self.spin_box)
        self.spin_box.setValue(value)

        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)

    def value(self):
        return self.lebel.text(), self.spin_box.value()

    def setRange(self, start, end):
        self.slider.setRange(start, end)

    def setValue(self, value):
        self.slider.setValue(value )
        self.spin_box.setValue(value)


class CheckBoxGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(attribut)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.check_box  = QCheckBox()
        self.layout.addWidget(self.check_box )

    def value(self):
        return self.lebel.text(), bool(self.check_box.checkState())

def distance(start, end):
    """
    Calculate the distance between two objects or coordinates
    """
    a = cmds.xform(start, q=True, t=True, ws=True) if type(start) in (str, unicode) else start
    b = cmds.xform(end, q=True, t=True, ws=True) if type(end) in (str, unicode) else end
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


def ribbon_rig_system_v3():
    # global dyn_win
    # try:
    #     dyn_win.deleteLater()
    #     pass
    # except NameError:
    #     pass
    dyn_win = RibbonRigSystemRig()
    dyn_win.resize(600, 400)
    dyn_win.show()





if __name__ == '__main__':
    ribbon_rig_system_v3()
