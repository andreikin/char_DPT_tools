# -*- coding: utf-8 -*-
import webbrowser
import maya.cmds as cmds
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya
from Controller import Controller
from attributes import move_up_attribute, move_down_attribute
from maya_widgets import *
from utilities import rename_shape

ABOUT_SCRIPT = "\n" \
               "Latest updates:                                     \n" \
               "16.12.2022    -Add help video                       \n" \
               "16.12.2022    -Add attribut Char_DPT_tools                   \n" \
               "30.11.2022    -Made the first version               \n" \
               "                                                    \n" \
               "Created by Andrey Belyaev                           \n" \
               "andreikin@mail.ru"

HELP_TEXT = "\n" \
            "- Specify size (in scene units)\n\n" \
            "- Specify the name of the controller (without suffix)\n\n" \
            "- Specify the desired shape "

COLORS = [6, 12, 13, 17, 18, 20, 23]
URL = 'https://www.youtube.com/watch?v=9KPDRA_cV4k'


class ColorButton(QPushButton):
    def __init__(self, color):
        QPushButton.__init__(self)

        self.color = color
        rgb = [int(x*255) for x in cmds.colorIndex(color, q=True)]
        style_sheet = "QPushButton { " \
                      "background-color: rgb(" + str(rgb[0]) + ", " + str(rgb[1]) + ", " + str(rgb[2]) + ")}" \
                      "QPushButton:hover { " \
                      "border: 2px solid rgb(80, 80, 80);}"
        self.clicked.connect(self.set_color)
        self.setStyleSheet(style_sheet)

    def set_color(self):
        for ct in cmds.ls(sl=True):
            Controller.add_color(ct, self.color)


class CreateControlUI(UiTemplate, MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(CreateControlUI, self).__init__()
        self.setWindowTitle("Controller Char_DPT_tools v.02")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)

        self.add_menu()
        self.help_action.triggered.connect(lambda: self.text_dialog(HELP_TEXT))
        self.about_script_action.triggered.connect(lambda: self.text_dialog(ABOUT_SCRIPT))
        video_action = QAction("Show help video", self)
        self.menu.insertAction(self.about_script_action, video_action)
        video_action.triggered.connect(lambda: webbrowser.open_new(URL))

        self.color_palette_ui()
        self.move_attribut_ui()
        self.additional_ui()
        self.control_creator()
        style_sheet = """         QPushButton { 
                                      border-radius: 3px;
                                      border: 1px solid rgb(60, 60, 60);
                                      height: 30px;
                                      background-color: rgb(100, 100, 100); 
                                      border-style: outset;} 
                                  QPushButton:pressed { background-color: rgb(0, 0, 0); }
                                  QPushButton:hover { background-color: rgb(130, 130, 130);}

                                  QGroupBox { border-radius: 3 ;
                                      background-color: rgb(80, 80, 80); }
                                  QGroupBox::title {
                                      subcontrol-origin: margin;
                                      font-weight: bold;
                                      subcontrol-position: top left;  
                                      padding: 5px 10px 5px 10px;
                                      
                                      }
                                  QLabel { padding: 5 0px;}                              
                                  QComboBox {
                                      border-radius: 3px;
                                      background-color: rgb(40, 40, 40); }
                                      }
                                  """
        self.setStyleSheet(style_sheet)

        # set_right_controls_width
        # for widget in (self.add_attr_grp.lable):
        #     widget.setFixedWidth(150)



    def move_attribut_ui(self):

        self.move_attr_grp = QGroupBox("Selected attribute:")
        self.move_attr_grp_layout = QVBoxLayout(self.move_attr_grp)
        self.move_attr_grp_layout.setContentsMargins(4, 35, 4, 4)

        self.btn_move_attr_grp = ButtonGrp(labelArray=["Up", "Down", "Hide/Show"])
        self.btn_move_attr_grp.button_list[0].clicked.connect(move_up_attribute)
        self.btn_move_attr_grp.button_list[1].clicked.connect(move_down_attribute)
        self.btn_move_attr_grp.button_list[2].clicked.connect(self.hide_show_attr)

        self.move_attr_grp_layout.addWidget(self.btn_move_attr_grp)

        self.add_attr_grp = TextFieldButtonGrp("Add attribute", buttonLabel='Add')
        self.add_attr_grp.button.setFixedWidth(70)
        #self.add_attr_grp.label.setFixedWidth(170)
        self.add_attr_grp.button.clicked.connect(self.add_attribute)
        self.move_attr_grp_layout.addWidget(self.add_attr_grp)

        self.verticalLayout.addWidget(self.move_attr_grp)
        
    def add_attribute(self):
        attr = self.add_attr_grp.text()
        for sel in cmds.ls(sl=True):
            cmds.addAttr(sel, longName=attr, keyable=True)

    def color_palette_ui(self):
        self.color_grp = QGroupBox("Add colors:")
        self.color_grp_layout = QHBoxLayout(self.color_grp)

        self.color_grp_layout.setContentsMargins(4, 35, 4, 4)
        self.color_grp_layout.setSpacing(2)

        for color in COLORS:
            btn = ColorButton(color)
            self.color_grp_layout.addWidget(btn)
        self.verticalLayout.addWidget(self.color_grp)

    def additional_ui(self):
        self.tools_grp = QGroupBox("Additional Char_DPT_tools:")
        self.tools_grp_layout = QVBoxLayout(self.tools_grp)
        self.tools_grp_layout.setContentsMargins(4, 35, 4, 4)

        self.btn_tools_grp = ButtonGrp(labelArray=["Mirror shape", "Combine curves"])

        self.btn_tools_grp.button_list[0].clicked.connect(self.mirrow_func)
        self.btn_tools_grp.button_list[1].clicked.connect(self.combine_func)
        self.tools_grp_layout.addWidget(self.btn_tools_grp)

        self.verticalLayout.addWidget(self.tools_grp)

    def control_creator(self):
        self.option_box = QGroupBox("Create controller:")
        self.option_box_layout = QVBoxLayout(self.option_box)
        self.option_box_layout.setContentsMargins(4, 35, 4, 4)

        self.size_float_grp = FloatSliderGrp("Controll size:")
        self.option_box_layout.addWidget(self.size_float_grp)
        self.size_float_grp.setRange(0.1, 3.0)
        self.size_float_grp.setValue(1.0)
        self.size_float_grp.line_edit.setFixedWidth(70)

        self.name_line_edit = TextFieldButtonGrp(label="Controller name:", button=False)
        # self.name_line_edit.setText("Controller")
        self.option_box_layout.addWidget(self.name_line_edit)

        self.typeComboBox = ComboBoxGrp("Controller type:")
        self.typeComboBox.combo_box.setCurrentText("hand_ik")
        self.option_box_layout.addWidget(self.typeComboBox)
        items = sorted(Controller().shape_list())
        self.typeComboBox.addItems(items)
        
        self.constraint_check = CheckBoxGrp("Add constraint:")
        self.constraint_check.check_box.setCheckState(Qt.Checked)
        self.option_box_layout.addWidget(self.constraint_check)

        self.btn_grp = ButtonGrp(labelArray=["Close", "Create controller"])
        self.btn_grp.button_list[1].clicked.connect(self.create)
        self.btn_grp.button_list[0].clicked.connect(self.close)
        self.option_box_layout.addWidget(self.btn_grp)
        self.verticalLayout.addWidget(self.option_box)

class CreateControl(CreateControlUI):

    def hide_show_attr(self):
        objs = cmds.ls(sl=True)
        attributes = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)

        for obj in objs:
            if attributes:
                for atr in attributes:
                    cmds.setAttr(obj + "." + atr, e=True, k=False, l=True)
            else:
                for atr in [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz", ".v"]:
                    cmds.setAttr(obj + atr, e=True, k=True, l=False)

    def create(self):
        data = self.get_data([self.name_line_edit, self.size_float_grp, self.typeComboBox, self.constraint_check])
        data['Controller name:'] = data['Controller name:'] if data['Controller name:'] else "Controller001"
        ct_attr = {'name': data['Controller name:'],
                   'shape': data['Controller type:'],
                   'size': data['Controll size:'],
                   'hid_attr': ['sx', 'sy', 'sz', 'v']}

        # if has selection align control to it
        sel = cmds.ls(sl=True)
        if sel:
            ct_attr["align_obj"] = sel[0]
            ct_attr["rotate"] = [0, 0, 90]

        ctrl = Controller(**ct_attr)
        ctrl.create()

        if data['Add constraint:'] and sel:
            cmds.parentConstraint(ctrl.name, sel[0])

    def combine_func(self):
        ct_a, ct_b = cmds.ls(sl=True)
        rename_shape(ct_b)
        Controller.combine_curves(ct_a, ct_b)

    def mirrow_func(self):
        ct_a, ct_b = cmds.ls(sl=True)
        rename_shape(ct_b)
        Controller.mirrow_shape(ct_a, ct_b)




def controller_tools():
    win = CreateControl()
    win.show()


if __name__ == '__main__':
    controller_tools()
