import re
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya

from corrective_joints_module.maya_widgets import *
import maya.cmds as cmds
import maya.OpenMaya as om
import pymel.core as pm

PFX = {'L_': 'R_', 'l_': 'r_', 'left_': 'right_', 'Left_': 'Right_'}
ABOUT_SCRIPT = '\n' \
               'Latest updates:                                     \n' \
               '19.08.2024    -Add prefix verification              \n' \
               '13.08.2024    -Edit prefix                          \n' \
               '07.08.2024    -Fix mirrow error                     \n' \
               '21.10.2022    -Fix matchTransform error             \n' \
               '                                                    \n' \
               'Created by Andrey Belyaev                           \n' \
               'andreikin@mail.ru'
HELP_LABEL = '- Specify the bone that will bend and the parent bone. \n' \
             '- If right and left parts are needed, the system and joints\n' \
             '    names must include one of the prefixes: L_ l_ left_ Left_'
HELP_TEXT = '\n' \
            '- Specify the name of the system (if the right side is required, \n' \
            '      a prefix must be used)\n\n' \
            '- Specify the joint to be bent and the parent joint.\n\n' \
            '- Specify the direction of the bend that will control the \n' \
            '      corrective joint\n\n' \
            '- The received controller has special attributes that control the\n' \
            '      sensitivity of the system in manual and automatic modes.'
RIG_VISIBILITY_ATTR = 'rig_visibility'
DEL_LIST_ATTRIBUTE = 'delList'
PFX_PATTERN = '^(L_|R_|l_|r_|left_|right_|Left_|Right_)'
DIGIT_PATTERN = r'\d{1,}$'


def an_connectRigVis(ctrlObject, objList):
    if not cmds.objExists(ctrlObject + '.rigVis'):  cmds.addAttr(ctrlObject, ln="rigVis", at="enum", en="off:on",
                                                                 keyable=True)
    for each in objList:
        if not cmds.connectionInfo(each + ".v", id=True) and not cmds.objExists(each + '.rigVis'):
            cmds.connectAttr(ctrlObject + '.rigVis', each + ".v")
        if cmds.objExists(each + '.rigVis'):
            cmds.connectAttr(ctrlObject + '.rigVis', each + '.rigVis')


def add_devide_attr(name):
    attrName = '_'
    while cmds.objExists(name + '. ' + attrName):
        attrName = attrName + '_'
    cmds.addAttr(name, ln=attrName, keyable=True)
    cmds.setAttr(name + '. ' + attrName, lock=True)


def namespace_off(func):
    """
    decorator that disables namespaces for the function being decorated
    """

    def wrapper(*args, **kwargs):
        current = cmds.namespaceInfo(currentNamespace=True)
        if not current == u':':
            cmds.namespace(setNamespace=u':')
        return_value = func(*args, **kwargs)
        cmds.namespace(setNamespace=current)
        return return_value

    return wrapper


def rig_visibility(controller, objects_list, dv=False):
    """
    Hides auxiliary rigging objects whose visibility can be changed using an attribute 'rig_visibility'
    """
    if not cmds.objExists(controller + '.' + RIG_VISIBILITY_ATTR):
        cmds.addAttr(controller, ln=RIG_VISIBILITY_ATTR, dv=dv, k=True, at='enum', en='off:on')
    for v_each in objects_list:
        if not cmds.connectionInfo(v_each + '.v', id=True):
            cmds.connectAttr(controller + '.' + RIG_VISIBILITY_ATTR, v_each + '.v')


def unique_names_generator(in_name, name_index_padding=3):
    """
    Generates a unique name that is not in the scene
    """
    new_name = in_name
    num_str = '{0:0' + str(name_index_padding) + 'd}'
    pref, name, num, sfx = divide_name(in_name)
    num = int(num) if num else 0
    while not len(cmds.ls(new_name)) == 0:
        num += 1
        str_new_num = num_str.format(num)
        new_name = pref + name + str_new_num + sfx
    return new_name


def rename_shape(obj):
    """
    Renames all shapes controllers to unique names.
    """
    if not len(cmds.ls(obj)) == 1:
        om.MGlobal.displayError(
            'There is either no object named {} in the scene or there is more than one of them'.format(obj))
        return

    pref, name, num, sfx = divide_name(obj)
    for shape in cmds.listRelatives(obj, s=True, fullPath=True):
        shape_new_name = pref + name + num + 'Shape001'
        cmds.rename(shape, unique_names_generator(shape_new_name))


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


class ControllerLibrary(object):
    def __init__(self):
        self.lib = dict()
        self.lib['sphere'] = [{'degree': 3,
                               'knot': [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 10.0],
                               'periodic': False,
                               'point': [(0.0, 0.003, -0.506), (0.0, -0.123, -0.501), (0.0, -0.28, -0.418),
                                         (0.0, -0.448, -0.261), (0.0, -0.52, 0.021), (0.0, -0.374, 0.367),
                                         (0.0, 0.003, 0.524), (0.0, 0.38, 0.367), (0.0, 0.526, 0.021),
                                         (0.0, 0.443, -0.251), (0.0, 0.295, -0.418), (0.0, 0.118, -0.501),
                                         (0.0, 0.003, -0.501)]},
                              {'degree': 3,
                               'knot': [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 10.0],
                               'periodic': False,
                               'point': [(0.0, 0.5, -0.009), (-0.126, 0.494, -0.009), (-0.282, 0.41, -0.009),
                                         (-0.45, 0.254, -0.009), (-0.523, -0.029, -0.009), (-0.377, -0.374, -0.009),
                                         (0.0, -0.531, -0.009), (0.377, -0.374, -0.009), (0.523, -0.029, -0.009),
                                         (0.44, 0.243, -0.009), (0.292, 0.41, -0.009), (0.115, 0.494, -0.009),
                                         (0.0, 0.494, -0.009)]},
                              {'degree': 3,
                               'knot': [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 10.0],
                               'periodic': False,
                               'point': [(0.0, 0.003, -0.506), (-0.126, 0.003, -0.501), (-0.282, 0.003, -0.418),
                                         (-0.45, 0.003, -0.261), (-0.523, 0.003, 0.021), (-0.377, 0.003, 0.367),
                                         (0.0, 0.003, 0.524), (0.377, 0.003, 0.367), (0.523, 0.003, 0.021),
                                         (0.44, 0.003, -0.251), (0.292, 0.003, -0.418), (0.115, 0.003, -0.501),
                                         (0.0, 0.003, -0.501)]}]

        self.lib['arrowed_pin'] = [{'degree': 3,
                                    'knot': [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
                                    'periodic': True,
                                    'point': [(0.052, 0.0, -0.03), (-0.0, 0.0, -0.06), (-0.052, 0.0, -0.03),
                                              (-0.052, -0.0, 0.03),
                                              (-0.0, -0.0, 0.06), (0.052, -0.0, 0.03), (0.052, 0.0, -0.03),
                                              (-0.0, 0.0, -0.06),
                                              (-0.052, 0.0, -0.03)]},
                                   {'degree': 1, 'knot': [0.0, 1.0, 2.0, 3.0, 4.0], 'periodic': False,
                                    'point': [(0.05, 0.0, 0.0), (0.992, 0.0, 0.0), (0.854, 0.0, -0.052),
                                              (0.992, 0.0, 0.0),
                                              (0.854, 0.0, 0.052)]}]

    def shape_presets(self, shape_type):
        return self.lib[shape_type]


class Controller(ControllerLibrary):
    global_scale = 1
    SFX = "_ctrl"
    SFX_CON = 'Con_grp'
    SFX_ORI = 'Ori_grp'

    def __init__(self, **kwargs):
        ControllerLibrary.__init__(self)
        self.pfx = kwargs.setdefault("name", 'Controller')
        self.name, self.conGrp, self.oriGrp = [self.pfx + x for x in (self.SFX, self.SFX_CON, self.SFX_ORI)]

        self.name_verification()
        self.shape = kwargs.setdefault("shape", 'sphere')
        self.shape_rotation_offset = kwargs.setdefault("rotate", [0, 0, 0])
        self.shape_translation_offset = kwargs.setdefault("translate", [0, 0, 0])
        self.color = kwargs.setdefault("color", 17)
        self.size = kwargs.setdefault("size", 1)
        self.hid_attr = kwargs.setdefault("hid_attr", None)
        self.parent = kwargs.setdefault("parent", None)
        self.align_obj = kwargs.setdefault("align_obj", None)
        self.pole_vec = kwargs.setdefault('pole_vec', None)
        self.prt_constraint = None
        self.prt_const_targets = kwargs.setdefault('parent_constrained_to', None)

    def name_verification(self):
        current_namespace = cmds.namespaceInfo(currentNamespace=True)
        namespace = current_namespace + ':' if ':' not in current_namespace else ""

        # if there is at least one object, then we generate a new set of names
        if any([cmds.objExists(namespace + x) for x in (self.name, self.conGrp, self.oriGrp)]):
            for i in range(1, 100):
                new_pfx = self.pfx + '{0:03d}'.format(i)
                if all([not cmds.objExists(namespace + new_pfx + x) for x in (self.SFX, self.SFX_CON, self.SFX_ORI)]):
                    self.name, self.conGrp, self.oriGrp = [new_pfx + x for x in (self.SFX, self.SFX_CON, self.SFX_ORI)]
                    break

    def create(self, size=None, hid_attr=None, align_obj=None, ):
        shape_data = self.shape_presets(self.shape)
        self.name = self.build_ct(shape_data, self.name)
        self.set_shape_rotation_offset()
        self.set_size(Controller.global_scale)
        self.set_size(size)
        self.set_shape_translation_offset()
        self.add_color(self.name, self.color)
        self.group_ct()
        self.align_to(align_obj)
        self.set_to_pole_vec_pos(self.oriGrp, self.pole_vec)
        self.parent_constraint()
        self.parent_to()
        self.hide_attributes(hid_attr)
        return self

    @staticmethod
    def add_color(ctrl, color):
        color = color if color else 17
        shape = cmds.listRelatives(ctrl, s=True, fullPath=True)
        for eachShape in shape:
            cmds.setAttr(eachShape + ".overrideEnabled", 1)
            cmds.setAttr(eachShape + ".overrideColor", color)

    # @namespace_off
    def group_ct(self):
        self.conGrp = cmds.group(name=self.conGrp, empty=True)
        self.oriGrp = cmds.group(self.conGrp, name=self.oriGrp)
        cmds.parent(self.name, self.conGrp)

    def set_size(self, size):
        size = size if size else self.size
        size = size if type(size) == list else [size, size, size]
        cmds.setAttr(self.name + ".scale", float(size[0]), float(size[0]), float(size[0]))
        cmds.makeIdentity(self.name, apply=True)

    def set_shape_rotation_offset(self):
        cmds.setAttr(self.name + ".rotate", *self.shape_rotation_offset)
        cmds.makeIdentity(self.name, apply=True)

    def set_shape_translation_offset(self):
        cmds.setAttr(self.name + ".translate", *self.shape_translation_offset)
        cmds.makeIdentity(self.name, apply=True)
        cmds.move(0, 0, 0, self.name + '.scalePivot', self.name + '.rotatePivot', absolute=True)

    def hide_attributes(self, hid_attr):
        hid_attr = hid_attr if hid_attr else self.hid_attr
        if hid_attr:
            for attr in hid_attr:
                cmds.setAttr(self.name + "." + attr, lock=True, keyable=False)

    def parent_constraint(self):
        if self.prt_const_targets:
            self.prt_constraint = cmds.parentConstraint(self.prt_const_targets, self.oriGrp, mo=True)[0]

    def align_to(self, align_obj, orient=True, point=True):
        align_obj = align_obj if align_obj else self.align_obj
        if align_obj:
            if orient:
                cmds.delete(cmds.orientConstraint(align_obj, self.oriGrp, mo=False))
            if point:
                cmds.delete(cmds.pointConstraint(align_obj, self.oriGrp, mo=False))

    def parent_to(self, parent=None):
        parent = parent if parent else self.parent
        if parent:
            try:
                cmds.parent(self.oriGrp, parent)
            except Exception as message:
                print(message)

    @staticmethod
    def get_pole_vec_pos(ik_handle=None, joint_list=None, offset=0.5):
        if ik_handle:
            joint_list = cmds.ikHandle(ik_handle, q=True, jointList=True)
            endEffector = cmds.ikHandle(ik_handle, q=True, endEffector=True)
            end_jnt = cmds.connectionInfo(endEffector + ".tx", sourceFromDestination=True).split(".")[0]
            joint_list.append(end_jnt)
        elif joint_list:
            pass
        else:
            print("Required a handler or a list of bones")
        root_pos = cmds.xform(joint_list[0], q=True, ws=True, t=True)
        mid_pos = cmds.xform(joint_list[1], q=True, ws=True, t=True)
        end_pos = cmds.xform(joint_list[2], q=True, ws=True, t=True)
        root_joint_vec = om.MVector(root_pos[0], root_pos[1], root_pos[2])
        mid_joint_vec = om.MVector(mid_pos[0], mid_pos[1], mid_pos[2])
        end_joint_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])
        line = (end_joint_vec - root_joint_vec)
        point = (mid_joint_vec - root_joint_vec)
        scale_value = (line * point) / (line * line)
        proj_vec = line * scale_value + root_joint_vec
        root_to_mid_len = (mid_joint_vec - root_joint_vec).length()
        mid_to_end_len = (end_joint_vec - mid_joint_vec).length()
        total_length = (root_to_mid_len + mid_to_end_len)
        pole_vec_pos = (mid_joint_vec - proj_vec).normal() * total_length * offset + mid_joint_vec
        return pole_vec_pos

    @staticmethod
    def set_to_pole_vec_pos(ctrl, joints):
        if joints:
            pos = Controller.get_pole_vec_pos(joint_list=joints)
            cmds.move(pos[0], pos[1], pos[2], ctrl, worldSpace=True)

    @staticmethod
    def build_ct(input_data, name):
        for i, data in enumerate(input_data):
            crv = cmds.curve(per=data['periodic'], d=data['degree'], p=data['point'], k=data['knot'])
            if not i:
                name = cmds.rename(crv, name)
            else:
                Controller.combine_curves(crv, name)
        rename_shape(name)
        pm.select(name)
        return name

    @staticmethod
    @namespace_off
    def combine_curves(serse, terget):
        serse_shapes = cmds.listRelatives(serse, shapes=True)
        for shape in serse_shapes:
            new_name = unique_names_generator(shape)
            cmds.rename(shape, new_name)
            cmds.parent(new_name, terget, s=True, r=True)
        cmds.delete(serse)
        rename_shape(terget)
        return terget

    @staticmethod
    @namespace_off
    def mirrow_shape(source, target):
        sourse_shapes = [x for x in cmds.listRelatives(source, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        target_shapes = [x for x in cmds.listRelatives(target, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        for i in range(len(sourse_shapes)):
            point_num = cmds.getAttr(sourse_shapes[i] + '.spans') + cmds.getAttr(sourse_shapes[i] + '.degree')
            for pn in xrange(point_num):
                pos = cmds.xform(sourse_shapes[i] + '.controlPoints[' + str(pn) + ']', q=True, t=True, ws=True)
                cmds.xform(target_shapes[i] + '.controlPoints[' + str(pn) + ']', t=[pos[0] * -1, pos[1], pos[2]],
                           ws=True)


class CorrectiveJointsUi(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(CorrectiveJointsUi, self).__init__()
        jnt, up_jnt = None, None
        if cmds.ls(sl=True) and len(cmds.ls(sl=True)) == 2:
            up_jnt, jnt = cmds.ls(sl=True)

        self.setWindowTitle('Corrective joint system v.08')
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)

        # menu_bar
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        menu = QMenu('Help')
        menu_bar.addMenu(menu)
        help_action = QAction('Help', self)
        menu.addAction(help_action)
        help_action.triggered.connect(lambda: self.text_dialog('Help'))
        about_script_action = QAction('About script', self)
        menu.addAction(about_script_action)
        about_script_action.triggered.connect(lambda: self.text_dialog('ABOUT_PROGRAM'))

        # text
        self.help_label = QLabel(HELP_LABEL)
        self.help_label.setMaximumSize(QSize(1000, 90))
        self.verticalLayout.addWidget(self.help_label)

        # option_box
        self.option_box = QGroupBox('Options:')
        self.option_box_layout = QVBoxLayout(self.option_box)
        self.option_box_layout.insertSpacing(0, 20)
        self.option_box_layout.setSpacing(10)

        self.size_float_grp = FloatSliderGrp('Global scale')
        self.option_box_layout.addWidget(self.size_float_grp)
        self.size_float_grp.setRange(0.1, 3.0)
        self.size_float_grp.setValue(0.2)

        self.name_line_edit = TextFieldButtonGrp(label='System name', button=True)
        self.option_box_layout.addWidget(self.name_line_edit)
        self.name_line_edit.button.setText('Add existing')
        self.name_line_edit.line_edit.setPlaceholderText('Type system name')
        self.name_line_edit.button.clicked.connect(self.add_sel_sys)

        self.up_jnt_grp = TextFieldButtonGrp(label='Up joint', button=True, add_selected=True)
        self.up_jnt_grp.line_edit.setPlaceholderText('Add up joint name')
        self.option_box_layout.addWidget(self.up_jnt_grp)

        self.jnt_grp = TextFieldButtonGrp(label='Base joint', button=True, add_selected=True)
        self.jnt_grp.line_edit.setPlaceholderText('Add base joint name')
        self.option_box_layout.addWidget(self.jnt_grp)

        for grp in self.name_line_edit, self.up_jnt_grp, self.jnt_grp:
            grp.button.setFixedSize(120, 30)

        if jnt and up_jnt:
            self.jnt_grp.setText(jnt)
            self.up_jnt_grp.setText(up_jnt)

        self.rad_btn_grp = RadioButtonGrp('Control angle', labelArray=['+Y', '-Y', '+Z', '-Z'])
        self.option_box_layout.addWidget(self.rad_btn_grp)

        self.check_box_grp = CheckBoxGrp('Made right side')
        self.option_box_layout.addWidget(self.check_box_grp)
        self.check_box_grp.check_box.setCheckState(Qt.Checked)
        self.check_box_grp.check_box.stateChanged.connect(self.checkbox_changed)

        self.mirror_grp = RadioButtonGrp('Mirror across', labelArray=['YZ', 'XY', 'XZ'])
        self.option_box_layout.addWidget(self.mirror_grp)

        self.verticalLayout.addWidget(self.option_box)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(3)

        self.template_ct = QPushButton('Template controller')
        self.buttons_layout.addWidget(self.template_ct)
        self.template_ct.clicked.connect(self.template_controller)

        self.up_jnt_btn = QPushButton('Up joint')
        self.buttons_layout.addWidget(self.up_jnt_btn)
        self.up_jnt_btn.clicked.connect(lambda: self.create('up'))

        self.dw_jnt_btn = QPushButton('Dw joint')
        self.dw_jnt_btn.clicked.connect(lambda: self.create('dw'))

        self.buttons_layout.addWidget(self.dw_jnt_btn)
        self.verticalLayout.addLayout(self.buttons_layout)

        self.setFixedWidth(500)

        style_sheet = ''' 
                   QLineEdit { border-radius: 3 ; 
                       background-color: rgb(40, 40, 40); 
                       border:1px solid rgb(40, 40, 40);
                       }
                   QLineEdit:hover  { 
                       border:1px solid rgb(118, 118, 118);
                       }
                   QGridLayout { margin: 0; }     
                   QPushButton { 
                       border-radius: 3px;
                       border: 1px solid rgb(60, 60, 60);
                       height: 30px;
                       background-color: rgb(100, 100, 100); 
                       border-style: outset;} 
                   QPushButton:pressed { background-color: rgb(0, 0, 0); }
                   QPushButton:hover { background-color: rgb(130, 130, 130);}

                   QGroupBox { border-radius: 3 ;
                       padding-top: 15 px;
                       background-color: rgb(80, 80, 80); }
                   QGroupBox::title {
                       subcontrol-origin: margin;
                       font-weight: bold;
                       subcontrol-position: top left;  
                       padding: 5 10px;
                       }
                   QComboBox {
                       border-radius: 3px;
                       background-color: rgb(40, 40, 40); }
                       }
                   '''
        self.setStyleSheet(style_sheet)

    def checkbox_changed(self):
        self.mirror_grp.setEnabled(self.check_box_grp.value()[1])

    def add_sel_sys(self):
        if not cmds.ls(sl=True):
            om.MGlobal.displayError('Error: You must select the corrective joint system')
        else:
            jcs = cmds.ls(sl=True)[0]
            name = ''.join(divide_name(jcs)[:-1])
            self.name_line_edit.line_edit.setText(name)
            if cmds.objExists(jcs + '.jcs'):
                loc, base_jnt, up_jnt, = cmds.listConnections(jcs + '.jcs', s=True, d=False)
                self.up_jnt_grp.line_edit.setText(up_jnt)
                self.jnt_grp.line_edit.setText(base_jnt)

    def get_data(self):
        data = dict()
        widgets_list = [self.rad_btn_grp, self.size_float_grp, self.name_line_edit, self.up_jnt_grp, self.jnt_grp,
                        self.check_box_grp, self.mirror_grp]
        for widget in widgets_list:
            text, val = widget.value()
            data[text] = val
        return data

    def template_controller(self):
        data = self.get_data()
        if not data['Base joint']:
            om.MGlobal.displayError('Error: You must add objects!')
            return

        ct_data = {'name': unique_names_generator('template'),
                   'shape': 'arrowed_pin',
                   'size': data['Global scale'],
                   'align_obj': data['Base joint']}

        if cmds.getAttr(data['Base joint'] + '.tx') < 0.001:
            ct_data['rotate'] = [0, 180, 0]
        self.tmp_ctrl = Controller(**ct_data)
        self.tmp_ctrl.create()
        cmds.setAttr(self.tmp_ctrl.name + '.tz', float(ct_data['size']) / 5.0)
        cmds.select(self.tmp_ctrl.name)

    def create(self, parent_to):
        data = self.get_data()

        if not self.verification(data):
            return

        data['parent_to'] = parent_to
        corrective_sys = CorrectiveJoints(**data)
        corrective_sys.corrective_joint(self.tmp_ctrl.name)
        if data['Made right side']:
            r_data = self.get_right_data(data)
            self.r_tmp_ctrl = self.right_template_controller(data)
            r_corrective_sys = CorrectiveJoints(**r_data)
            r_corrective_sys.corrective_joint(self.r_tmp_ctrl)
            cmds.delete(self.r_tmp_ctrl)
        cmds.delete(self.tmp_ctrl.oriGrp)
        return True

    def verification(self, data):

        has_prefix = all([divide_name(x)[0] for x in [data['System name'], data['Base joint'], data['Up joint']]])
        if data['Made right side'] and not has_prefix:
            om.MGlobal.displayError('Error: You must input system and joints names with side prefix')
            return False
        if not data['Up joint']:
            om.MGlobal.displayError('Error: You must add objects!')
            return False
        return True

    def right_template_controller(self, data):
        cmds.select(cl=True)
        tmp_joint = cmds.joint(n='l_tmp')
        cmds.joint(n='l_tmp_end')
        cmds.delete(cmds.parentConstraint(self.tmp_ctrl.name, tmp_joint, mo=False))

        if data['Mirror across'] == 'XY':
            rt_jnt = cmds.mirrorJoint(tmp_joint, mirrorXY=True, mirrorBehavior=True, sr=['l_', 'r_'])[0]
        elif data['Mirror across'] == 'YZ':
            rt_jnt = cmds.mirrorJoint(tmp_joint, mirrorYZ=True, mirrorBehavior=True, sr=['l_', 'r_'])[0]
        else:
            rt_jnt = cmds.mirrorJoint(tmp_joint, mirrorXZ=True, mirrorBehavior=True, sr=['l_', 'r_'])[0]

        r_jnt_end = cmds.listRelatives(rt_jnt, children=True)[0]
        cmds.setAttr(r_jnt_end + '.ry', 180)
        cmds.parent(r_jnt_end, world=True)
        cmds.delete(tmp_joint, rt_jnt)
        return r_jnt_end

    def get_right_data(self, data):
        r_data = data.copy()
        for key in [u'Base joint', u'Up joint', u'System name']:
            for pfx in PFX:
                if pfx == data[key][:len(pfx)]:
                    r_data[key] = PFX[pfx] + data[key][len(pfx):]
        return r_data

    def text_dialog(self, text_type):
        '''
        'Help window' or 'About program' text dialog
        '''
        help_dialog = QMessageBox()
        help_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        if text_type == 'Help':
            help_dialog.setWindowTitle('Help window')
            help_dialog.setText(HELP_TEXT)
        else:
            help_dialog.setWindowTitle('About program')
            help_dialog.setText(ABOUT_SCRIPT)
        help_dialog.setStandardButtons(QMessageBox.Cancel)
        help_dialog.exec_()


class CorrectiveJoints:
    def __init__(self, **kwargs):
        self.size = float(kwargs.setdefault('Global scale', 1.0))
        self.name = kwargs.setdefault('System name', 'jcs001')
        self.up_jnt = kwargs.setdefault('Up joint', '')
        self.base_jnt = kwargs.setdefault('Base joint', '')
        self.control_angle = kwargs.setdefault('Control angle', None)
        self.parent_to = kwargs.setdefault('parent_to', 'dw')
        self.made_right_side = kwargs.setdefault('Made right side', False)

        self.x_dir = 1 if cmds.getAttr(self.base_jnt + '.tx') > 0.001 else -1
        self.loc = self.name + '_loc'
        self.rig_grp = self.name + '_grp'
        self.solver_grp = self.name + 'Solver_grp'
        self.ctrl_grp = self.name + 'Controllers_grp'

        if not cmds.objExists(self.name + '_grp.jcs'):
            self.solver()

    def corrective_joint(self, tmp_ctrl):
        const_obj = self.up_jnt if self.parent_to == 'up' else self.base_jnt

        ct_data = {'name': unique_names_generator(self.name + '001_ctrl'),
                   'shape': 'sphere',
                   'size': self.size / 6.0,
                   'parent_constrained_to': const_obj,
                   'parent': self.ctrl_grp,
                   'hid_attr': ['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'],
                   'align_obj': tmp_ctrl}

        if Controller.SFX in ct_data['name']:
            ct_data['name'] = ct_data['name'][:-len(Controller.SFX)]

        ctrl = Controller(**ct_data)
        ctrl.create()
        pref, name, num, sfx = divide_name(ctrl.name)
        cmds.select(cl=True)
        cs_joint = cmds.joint(n=pref + name + num + '_skinned')
        auto_grp = cmds.group(cs_joint, n=pref + name + 'Auto' + num + '_grp')
        manual_grp = cmds.group(auto_grp, n=pref + name + 'Manual' + num + '_grp')
        cmds.delete(cmds.parentConstraint(ctrl.name, manual_grp, mo=False))
        cmds.parent(cs_joint, self.base_jnt)
        cmds.parent(manual_grp, ctrl.conGrp)
        cmds.parentConstraint(auto_grp, cs_joint, mo=False)

        cmds.addAttr(ctrl.name, longName='auto', keyable=True, defaultValue=2)
        cmds.addAttr(ctrl.name, longName='manual', keyable=True, defaultValue=5)

        connect_attr = {'+Y': 'pos_y_val', '-Y': 'neg_y_val', '+Z': 'pos_z_val', '-Z': 'neg_z_val'}[self.control_angle]

        multiplyDivide = cmds.createNode('multiplyDivide', n=self.name + 'multiplyDivide')
        cmds.connectAttr(self.loc + '.' + connect_attr, multiplyDivide + '.input1X')
        cmds.connectAttr(ctrl.name + '.auto', multiplyDivide + '.input2X')
        cmds.connectAttr(multiplyDivide + '.outputX', auto_grp + '.tx')

        multiplyDivide2 = cmds.createNode('multiplyDivide', n=self.name + 'multiplyDivideB')
        cmds.connectAttr(ctrl.name + '.t', multiplyDivide2 + '.input1')
        cmds.connectAttr(ctrl.name + '.manual', multiplyDivide2 + '.input2X')
        cmds.connectAttr(ctrl.name + '.manual', multiplyDivide2 + '.input2Y')
        cmds.connectAttr(ctrl.name + '.manual', multiplyDivide2 + '.input2Z')
        cmds.connectAttr(multiplyDivide2 + '.output', manual_grp + '.t')

    def solver(self):
        cmds.group(n=self.rig_grp, em=True)
        cmds.group(n=self.solver_grp, em=True)
        cmds.group(n=self.ctrl_grp, em=True)
        self.base_locator()

        z_neg_data = {'dir': 'neg_z', 'start_sweep': 0, 'end_sweep': 180, 'p_offset': [0, -0.005, 0]}
        y_poz_data = {'dir': 'pos_y', 'start_sweep': 90, 'end_sweep': 270, 'p_offset': [0, 0, -0.005]}
        z_poz_data = {'dir': 'pos_z', 'start_sweep': 180, 'end_sweep': 360, 'p_offset': [0, 0.005, 0]}
        y_neg_data = {'dir': 'neg_y', 'start_sweep': 270, 'end_sweep': 450, 'p_offset': [0, 0, 0.005]}

        for kwargs in [z_neg_data, z_poz_data, y_neg_data, y_poz_data]:
            plane = self.dirrection(**kwargs)
            cmds.parent(plane, self.solver_grp)

        # place solver
        cmds.delete(cmds.parentConstraint(self.base_jnt, self.solver_grp, mo=False))

        cmds.parentConstraint(self.up_jnt, self.solver_grp, mo=True)
        cmds.parentConstraint(self.base_jnt, self.loc, mo=True)
        cmds.parent(self.loc, self.solver_grp, self.ctrl_grp, self.rig_grp)
        cmds.scaleConstraint(self.base_jnt, self.ctrl_grp)

        cmds.addAttr(self.rig_grp, ln='jcs', at='message', multi=True, keyable=False)
        cmds.connectAttr(self.loc + '.message', self.rig_grp + '.jcs[0]')
        cmds.connectAttr(self.base_jnt + '.message', self.rig_grp + '.jcs[1]')
        cmds.connectAttr(self.up_jnt + '.message', self.rig_grp + '.jcs[2]')

        an_connectRigVis(self.rig_grp, [self.solver_grp, self.loc])

    def base_locator(self):
        self.loc = cmds.spaceLocator(n=self.loc)[0]
        loc_size = self.size / 5.0
        cmds.setAttr(self.loc + '.localScale', loc_size, loc_size, loc_size)
        cmds.setAttr(self.loc + '.tx', self.size / 2.0)
        cmds.parent(self.loc, self.solver_grp)
        add_devide_attr(self.loc)

    def dirrection(self, **kwargs):
        dir = kwargs.setdefault('dir', 'negative_z')
        start_sweep = kwargs.setdefault('start_sweep', 45)
        end_sweep = kwargs.setdefault('end_sweep', 135)
        p_offset = kwargs.setdefault('p_offset', [0, 0, 0])

        nurbs_plane = cmds.sphere(name=self.name + '_' + dir,
                                  radius=self.size / 2.0,
                                  spans=3,
                                  sections=3,
                                  startSweep=start_sweep,
                                  endSweep=end_sweep,
                                  axis=[-1, 0, 0],
                                  constructionHistory=False)[0]

        cmds.select(nurbs_plane + '.cv[5][1:4]', r=True)
        cmds.move(p_offset[0], p_offset[1], p_offset[2], r=True)

        cmds.setAttr(nurbs_plane + '.template', 1)
        cmds.addAttr(self.loc, ln=dir + '_val', dv=1, keyable=True)

        point_on_surface = cmds.createNode('closestPointOnSurface', n=self.name + 'PointOnSurface')
        cmds.connectAttr(self.loc + '.translate', point_on_surface + '.inPosition')
        cmds.connectAttr(cmds.listRelatives(nurbs_plane, s=True)[0] + '.worldSpace[0]',
                         point_on_surface + '.inputSurface')

        setRange = cmds.createNode('setRange', n=self.name + 'SetRange')
        cmds.connectAttr(point_on_surface + '.parameterV', setRange + '.valueX')
        cmds.setAttr(setRange + '.minX', -1)
        cmds.setAttr(setRange + '.maxX', 1)
        cmds.setAttr(setRange + '.oldMaxX', 3)

        multiplyDivide = cmds.createNode('multiplyDivide', n=self.name + 'multiplyDivide')
        cmds.setAttr(multiplyDivide + '.operation', 3)
        cmds.setAttr(multiplyDivide + '.input2X', 2)
        cmds.connectAttr(setRange + '.outValueX', multiplyDivide + '.input1X')

        revers = cmds.createNode('reverse', n=self.name + 'Revers')
        cmds.connectAttr(multiplyDivide + '.outputX', revers + '.inputX')
        multiplyDivide2 = cmds.createNode('multiplyDivide', n=self.name + 'multiplyDivide2')
        cmds.connectAttr(revers + '.outputX', multiplyDivide2 + '.input1X')
        cmds.connectAttr(point_on_surface + '.parameterU', multiplyDivide2 + '.input2X')

        multiplyDivide3 = cmds.createNode('multiplyDivide', n=self.name + 'multiplyDivide3')
        cmds.connectAttr(multiplyDivide2 + '.outputX', multiplyDivide3 + '.input1X')
        cmds.setAttr(multiplyDivide3 + '.input2X', 1.0)
        cmds.connectAttr(multiplyDivide3 + '.outputX', self.loc + '.' + dir + '_val')

        return nurbs_plane


def corrective_joints():
    win = CorrectiveJointsUi()
    win.show()



corrective_joints()




