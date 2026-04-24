# -*- coding: utf-8 -*-
import maya.cmds as cmds
import maya.OpenMaya as om
import math
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya

ABOUT_SCRIPT = "\n" \
               "Latest updates:                                     \n" \
               "11.03.2025    -release                              \n" \
               "                                                    \n" \
               "Created by Andrey Belyaev                           \n" \
               "andreikin@mail.ru"

HELP_LABEL = "Create a proxy skinning system, for a set of selected joints"

HELP_TEXT = "\n" \
            "To create proxy geometry, you need to sequentially select the required" \
            "joints and click the corresponding button.' \n"

LEFT_PART_SIZE = 150

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


class SkinProxySystemUi(UiTemplate, MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(SkinProxySystemUi, self).__init__()
        self.setWindowTitle("Skin proxy system v.01")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.layout = QVBoxLayout(self.centralwidget)

        # menu_bar
        self.add_menu()
        self.help_action.triggered.connect(lambda: self.text_dialog(HELP_TEXT))
        self.about_script_action.triggered.connect(lambda: self.text_dialog(ABOUT_SCRIPT))

        # text
        self.help_label = QLabel(HELP_LABEL)
        self.layout.addWidget(self.help_label)

        # tube option_box
        self.tube_option_box = QGroupBox("   Create proxy tube:")
        self.tube_option_box.setFlat(True)
        self.option_box_layout = QVBoxLayout(self.tube_option_box)  # Контейнер для группы
        self.option_box_layout.setContentsMargins(8, 20, 4, 4)

        self.slider = intSliderGrp('Subdivisions:', value=6)
        self.option_box_layout.addWidget(self.slider)

        self.tube_radius = FloatSliderGrp('Radius:')
        self.option_box_layout.addWidget(self.tube_radius)

        self.tube_btn_layout = QHBoxLayout()
        self.tube_btn_layout.addWidget(QWidget())

        self.tube_button = QPushButton('Create proxy tube')
        self.tube_btn_layout.addWidget(self.tube_button)
        self.tube_button.clicked.connect(self.create_tube)

        self.option_box_layout.addLayout(self.tube_btn_layout)
        self.layout.addWidget(self.tube_option_box)

        # plane option_box
        self.plane_option_box = QGroupBox("  Create proxy plane:")
        self.plane_option_box_layout = QVBoxLayout(self.plane_option_box)  # Контейнер для группы
        self.plane_option_box_layout.setContentsMargins(8, 20, 4, 4)

        self.plane_width = FloatSliderGrp('Width:')
        self.plane_option_box_layout.addWidget(self.plane_width)

        self.plane_up = RadioButtonGrp('Up vector', labelArray=['Z', 'Y'])
        self.plane_option_box_layout.addWidget(self.plane_up)

        self.plane_btn_layout = QHBoxLayout()
        self.plane_btn_layout.addWidget(QWidget())
        self.plane_button = QPushButton('Create proxy plane')
        self.plane_button.clicked.connect(self.create_plane)

        self.plane_btn_layout.addWidget(self.plane_button)
        self.plane_option_box_layout.addLayout(self.plane_btn_layout)

        self.layout.addWidget(self.plane_option_box)

        self.setStyleSheet("""
                            QGroupBox{
                                background-color: rgb(60, 60, 60);
                                border-radius: 0px;
                                padding-top: 20px;
                                }
                            QGroupBox::title {
                                font-weight: bold;
                                background-color: rgb(60, 60, 60);
                                margin: 10px;
                                }""")
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.layout.addWidget(close_button)

    def create_tube(self):
        joints_list = cmds.ls(sl=True)
        if len(joints_list) < 2:
            om.MGlobal.displayError('More than one joint must be selected')
            return
        x_subdivisions = self.slider.value()[1]
        tub_radius = self.tube_radius.value()[1]
        SkinProxySystem().create_proxy_tube(joints_list, x_subdivisions=x_subdivisions, tub_radius=tub_radius)

    def create_plane(self):
        joints_list = cmds.ls(sl=True)
        if len(joints_list) < 2:
            om.MGlobal.displayError('More than one joint must be selected')
            return
        width = self.plane_width.value()[1]
        up_vector = self.plane_up.value()[1]

        SkinProxySystem().create_proxy_plane(joints_list, width=width, up=up_vector)
        print('create_plane', width, up_vector)


class SkinProxySystem():

    @staticmethod
    def set_weight(geo, weight):
        # sort	jnt forvard
        jnt = [x for x in weight.keys() if cmds.objectType(x) == 'joint'] + [x for x in weight.keys() if
                                                                             not cmds.objectType(x) == 'joint']
        skCluster = cmds.skinCluster(jnt[0], geo, tsb=True, normalizeWeights=True)[0]  # skinning

        useGeoFlag = True if [x for x in jnt if not cmds.objectType(x) == 'joint'] else False  # influense geo test
        if useGeoFlag:  cmds.setAttr(skCluster + '.useComponents', 1)
        cmds.skinCluster(skCluster, e=True, useGeometry=useGeoFlag, addInfluence=jnt[1:], wt=0.0)  # add influenses
        pointsList = range(len(weight[jnt[0]]))  # point number list
        jntAndPos = []  # joint and pos in claster list
        for jn in jnt[1:]:
            jntAndPos.append([jn,
                              [x for x in cmds.connectionInfo(jn + '.worldMatrix[0]', dfs=True) if skCluster in x][
                                  0].split(']')[0].split('[')[1]])  # get position in clasters jnt list
        p = 0
        for jn, pos in jntAndPos:  # go through all the joints except the first one and it positions in skin claster
            p += 1
            for i in pointsList:  # go through all points for carrent joint
                if weight[jn][i] > 0:  # if point weight larger than 0
                    oldWeight = cmds.getAttr(
                        skCluster + '.weightList[' + str(i) + '].w[0]')  # get point weight for first joint
                    cmds.setAttr(skCluster + '.weightList[' + str(i) + '].w[0]',
                                 oldWeight - weight[jn][i])  # correct and set point weight for first joint
                    cmds.setAttr(skCluster + '.weightList[' + str(i) + '].w[' + pos + ']',
                                 weight[jn][i])  # set point weight for carrent joint
        return skCluster

    @staticmethod
    def __distance(start, end):
        """
        Calculate the distance between two objects or coordinates
        """
        a = cmds.xform(start, q=True, t=True, ws=True) if type(start) in (str, unicode) else start
        b = cmds.xform(end, q=True, t=True, ws=True) if type(end) in (str, unicode) else end
        return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


    def create_proxy_tube(self, joints_list, x_subdivisions=6, tub_radius=None):
        """
        Creates a proxy skin geometry (a polygonal cylinder) that follows a given joint hierarchy
        """
        # if the list is not from root to end, then reverse it
        if not cmds.listRelatives(joints_list[0], children=True) == [joints_list[1]]:
            joints_list = list(reversed(joints_list))

        tub_length = sum([self.__distance(joints_list[x], joints_list[x + 1]) for x in range(len(joints_list) - 1)])
        tub_radius = tub_radius if tub_radius else tub_length / 20
        geo = cmds.polyCylinder(radius=tub_radius, height=tub_length, subdivisionsY=len(joints_list) - 1,
                                subdivisionsX=x_subdivisions, axis=[1, 0, 0])[0]
        del_list = list()

        weights = {x: [] for x in joints_list}

        for i in range(len(joints_list)):
            start_point = i * x_subdivisions
            end_point = start_point + x_subdivisions - 1
            cluster = cmds.cluster(geo + '.vtx[' + str(start_point) + ':' + str(end_point) + ']')
            del_list.append(cluster[1])
            if i:
                cmds.pointConstraint(joints_list[i], cluster, mo=False)
                cmds.orientConstraint(joints_list[i], joints_list[i - 1], cluster, mo=False)
            else:
                cmds.parentConstraint(joints_list[i], cluster, mo=False)

            # set weights for jnt
            for j in range(len(joints_list) * x_subdivisions):
                if start_point <= j <= end_point:
                    val = 1.0 if i == 0 else 0.5
                    weights[joints_list[i]].append(val)
                elif start_point + x_subdivisions - 1 <= j <= end_point + x_subdivisions:
                    weights[joints_list[i]].append(0.5)
                else:
                    weights[joints_list[i]].append(0)

        cmds.delete(geo, constructionHistory=True)
        cmds.delete(del_list)
        self.set_weight(geo, weights)


    def create_proxy_plane(self, joints_list, width=1, up='Z'):
        subdivisions = 2
        geo = cmds.polyPlane(axis=[1, 0, 0], width=width, sx=1, sy=len(joints_list) - 1)[0]
        if up != 'Z':
            cluster = cmds.cluster(geo)[1]
            cmds.setAttr(cluster + '.rx', 90)
            cmds.delete(geo, constructionHistory=True)
        del_list = list()
        weights = {x: [] for x in joints_list}
        for i in range(len(joints_list)):
            start_point = i * subdivisions
            end_point = start_point + subdivisions - 1
            print(joints_list[i], start_point, end_point)
            cluster = cmds.cluster(geo + '.vtx[' + str(start_point) + ':' + str(end_point) + ']')
            del_list.append(cluster[1])
            if i:
                cmds.pointConstraint(joints_list[i], cluster, mo=False)
                cmds.orientConstraint(joints_list[i], joints_list[i - 1], cluster, mo=False)
            else:
                cmds.parentConstraint(joints_list[i], cluster, mo=False)

            # set weights for jnt
            for j in range(len(joints_list) * subdivisions):
                if start_point <= j <= end_point:
                    val = 1.0 if i == 0 else 0.5
                    weights[joints_list[i]].append(val)
                elif start_point + subdivisions - 1 <= j <= end_point + subdivisions:
                    weights[joints_list[i]].append(0.5)
                else:
                    weights[joints_list[i]].append(0)

        cmds.delete(geo, constructionHistory=True)
        cmds.delete(del_list)
        self.set_weight(geo, weights)


class RadioButtonGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, label='test', labelArray=[], parent=None):
        QWidget.__init__(self, parent)
        self.label = label

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(label)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.grp = QButtonGroup()
        for i, lbl in enumerate(labelArray):
            button = QRadioButton(lbl)
            if not i:
                button.setChecked(True)
            self.layout.addWidget(button)
            self.grp.addButton(button)

    def value(self):
        return self.lebel.text(), self.grp.checkedButton().text()

    def select(self):
        return self.grp.checkedButton().text()


class intSliderGrp(QWidget):

    def __init__(self, attribut, value=1, parent=None):
        QWidget.__init__(self, parent, )

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.lebel = QLabel(attribut)
        self.lebel.setFixedWidth(LEFT_PART_SIZE)
        self.layout.addWidget(self.lebel)

        self.slider = QSlider()
        self.slider.setRange(3, 10)
        self.slider.setSliderPosition(value)
        self.slider.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        self.spin_box = QSpinBox()
        self.spin_box.setFixedWidth(50)
        self.layout.addWidget(self.spin_box)
        self.spin_box.setValue(value)

        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)

    def value(self):
        return self.lebel.text(), self.spin_box.value()

    def setRange(self, start, end):
        self.slider.setRange(start, end)

    def setValue(self, value):
        self.slider.setValue(value)
        self.spin_box.setValue(value)


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


def skin_proxy_geometry():
    dyn_win = SkinProxySystemUi()
    dyn_win.resize(600, 300)
    dyn_win.show()


if __name__ == '__main__':
    skin_proxy_geometry()
