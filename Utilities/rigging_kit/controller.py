import re
import maya.cmds as cmds
import maya.OpenMaya as om

from .names import suffix_minus, rename_shape, unique_names_generator, namespace_off
from .utilities import connect_via_reverse, distance
from .controllers_library import ControllerLibrary


GLOBAL_SIZE = 1
SFX = '_CT'
SPACE_ATTRIBUTE = 'Space'
COLOR_CENTRE = 17

class Controller(ControllerLibrary):
    """
    The class is responsible for creating, placing and configuring the character's controllers
    """
    SFX = SFX
    SFX_AXIS = 'Axis_grp'
    SFX_CON = 'Con_grp'
    SFX_ORI = 'Ori_grp'

    def __init__(self, **kwargs):
        ControllerLibrary.__init__(self)
        self.pfx = kwargs.setdefault('name', 'controller')
        if re.search(self.SFX+r'$', self.pfx):
            self.pfx = re.sub(self.SFX+r'$', '', self.pfx)
        self.name, self.conGrp, self.oriGrp = [self.pfx + x for x in (self.SFX, self.SFX_CON, self.SFX_ORI)]
        self.axisGrp = self.pfx + self.SFX_AXIS
        self.shape = kwargs.setdefault('shape', 'sphere')
        self.shape_rotation_offset = kwargs.setdefault('rotate', [0, 0, 0])
        self.shape_translation_offset = kwargs.setdefault('translate', [0, 0, 0])
        self.color = kwargs.setdefault('color', COLOR_CENTRE)
        self.size = kwargs.setdefault('size', 1)
        self.hid_attr = kwargs.setdefault('hid_attr', None)
        self.parent = kwargs.setdefault('parent', None)
        self.align_data = kwargs.setdefault('align_data', None)
        self.bake_data = kwargs.setdefault('bake_data', self.align_data)
        self.space_data = kwargs.setdefault('space', None)
        self.rotate_axis = kwargs.setdefault("rotate_axis", None)

    def add_space(self, space_grp, default=1):
        """
        Method creates a system that allows, using constraint, to set the space
        in which it moves
        """
        cmds.addAttr(self.name, ln=SPACE_ATTRIBUTE, at='enum', en='World:Local', dv=default, keyable=True)
        # _______________________ constrained setup groups
        sp_grp = list()
        for i, grp in enumerate(['Local_grp', 'World_grp']):
            grp = cmds.group(n=self.name.replace(self.SFX, grp), em=True)
            cmds.delete(cmds.parentConstraint(self.oriGrp, grp, mo=False))
            cmds.parent(grp, space_grp)
            sp_grp.append(grp)

        cmds.setAttr(sp_grp[1] + '.r', 0, 0, 0)

        constraint = cmds.parentConstraint(sp_grp[0], sp_grp[1], self.conGrp, mo=False)[0]
        attr_list = cmds.parentConstraint(constraint, q=True, weightAliasList=True)
        cmds.connectAttr(self.name + '.' + SPACE_ATTRIBUTE, constraint + '.' + attr_list[0])
        connect_via_reverse(self.name + '.' + SPACE_ATTRIBUTE, constraint + '.' + attr_list[1])

    def create(self, size=None, hid_attr=None, align_obj=None, ):
        if self.name_verification():
            shape_data = self.shape_presets(self.shape)
            self.name = self.build_ct(shape_data, self.name)
            self.set_shape_rotation_offset()
            self.set_size(GLOBAL_SIZE)
            self.set_size(size)
            self.add_color(self.name, self.color)
            self.group_ct()
            self.set_axis_offset()
            self.set_shape_translation_offset()
            self.align()
            self.hide_attributes(hid_attr)
            return self

    def preparation_for_baking(self):
        """
        function of binding to objects of various types before baking controllers
        """
        if not self.bake_data:
            return None
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
            cmds.setAttr(self.name + '.' + attr, lock=False, keyable=True)

        if self.bake_data.get('type') == 'pole_vec':
            constraint = cmds.parentConstraint(self.bake_data.get('joints')[0], self.name, mo=True)[0]
        else:
            constraint = cmds.parentConstraint(self.bake_data.get('obj'), self.name, mo=True)[0]
            cmds.setAttr(constraint+'.interpType', 0)

        self.hide_attributes(hid_attr=None)
        return constraint

    def align(self):
        if self.align_data:
            align_type = self.align_data.get('type')
            if align_type == 'parent' and self.align_data.get('obj') and cmds.objExists(self.align_data.get('obj')):
                #cmds.delete(cmds.parentConstraint(self.align_data.get('obj'), self.oriGrp, mo=False))
                world_position = cmds.xform(self.align_data.get('obj'), query=True, worldSpace=True, translation=True)
                world_rotation = cmds.xform(self.align_data.get('obj'), query=True, worldSpace=True, rotation=True)
                cmds.xform(self.oriGrp, worldSpace=True, translation=world_position)
                cmds.xform(self.oriGrp, worldSpace=True, rotation=world_rotation)

            elif align_type == 'orient' and self.align_data.get('obj') and cmds.objExists(self.align_data.get('obj')):
                cmds.delete(cmds.orientConstraint(self.align_data['obj'], self.oriGrp, mo=False))

            elif align_type == 'point' and self.align_data.get('obj') and cmds.objExists(self.align_data.get('obj')):
                cmds.delete(cmds.pointConstraint(self.align_data['obj'], self.oriGrp, mo=False))

            elif align_type == 'pole_vec' and self.align_data.get('joints'):
                self.set_to_pole_vec_pos(self.oriGrp, self.align_data.get('joints'))

            elif align_type == 'leg_ik' and self.align_data.get('joints'):
                self.set_to_leg_ik_pos(self.oriGrp, self.align_data.get('joints'))

    def name_verification(self):
        current_namespace = cmds.namespaceInfo(currentNamespace=True)
        ns = current_namespace + ':' if not current_namespace == ':' else ''
        if all([not cmds.objExists(ns + x) for x in (self.name, self.conGrp, self.oriGrp)]):
            return True
        else:
           om.MGlobal.displayError('Name error. Perhaps a controller with the same name already exists!')

    @staticmethod
    def add_color(ctrl, color):
        color = color if color else COLOR_CENTRE
        shape = cmds.listRelatives(ctrl, s=True, fullPath=True)
        for eachShape in shape:
            cmds.setAttr(eachShape + '.overrideEnabled', 1)
            cmds.setAttr(eachShape + '.overrideColor', color)

    def group_ct(self):
        pfx = suffix_minus(self.name)
        self.conGrp = cmds.group(name=self.conGrp, empty=True)
        self.oriGrp = cmds.group(self.conGrp, name=self.oriGrp)
        cmds.parent(self.name, self.conGrp)

    def set_size(self, size):
        size = size if size else self.size
        size = size if type(size) == list else [size, size, size]
        cmds.setAttr(self.name + '.scale', float(size[0]), float(size[0]), float(size[0]))
        cmds.makeIdentity(self.name, apply=True)

    def set_shape_rotation_offset(self):
        cmds.setAttr(self.name + '.rotate', *self.shape_rotation_offset)
        cmds.makeIdentity(self.name, apply=True)

    def set_shape_translation_offset(self):
        cmds.setAttr(self.name + '.translate', *self.shape_translation_offset)
        cmds.makeIdentity(self.name, apply=True)
        cmds.move(0, 0, 0, self.name + '.scalePivot', self.name + '.rotatePivot', absolute=True)

    def hide_attributes(self, hid_attr):
        hid_attr = hid_attr if hid_attr else self.hid_attr
        if hid_attr:
            for attr in hid_attr:
                cmds.setAttr(self.name + '.' + attr, lock=True, keyable=False)

    def parent_to(self, parent=None):
        parent = parent if parent else self.parent
        if parent:
            try:
                cmds.parent(self.oriGrp, parent)
            except Exception as message:
                print(message)

    @staticmethod
    def build_ct(input_data, name):
        for i, data in enumerate(input_data):
            crv = cmds.curve(per=data['periodic'], d=data['degree'], p=data['point'], k=data['knot'])
            if not i:
                name = cmds.rename(crv, name)
            else:
                Controller.combine_curves(crv, name)
        rename_shape(name)
        cmds.select(name)
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
    def mirrow_shape(source, target):
        sourse_shapes = [x for x in cmds.listRelatives(source, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        target_shapes = [x for x in cmds.listRelatives(target, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        for i in range(len(sourse_shapes)):
            point_num = cmds.getAttr(sourse_shapes[i] + '.spans') + cmds.getAttr(sourse_shapes[i] + '.degree')
            for pn in xrange(point_num):
                pos = cmds.xform(sourse_shapes[i] + '.controlPoints[' + str(pn) + ']', q=True, t=True, ws=True)
                cmds.xform(target_shapes[i] + '.controlPoints[' + str(pn) + ']', t=[pos[0] * -1, pos[1], pos[2]], ws=True)

    def set_to_leg_ik_pos(self, obj, joints):
        cmds.delete(cmds.pointConstraint(joints[-1], joints[-3], obj, mo=False, skip='y'))
        pos = cmds.xform(joints[-1], q=True, t=True, ws=True)
        lc = cmds.spaceLocator()
        cmds.move(pos[0], 0, pos[2])
        aim = cmds.aimConstraint(lc, obj, mo=False, aim=[1, 0, 0], u=[0, 1, 0],  worldUpType='scene')
        cmds.delete(aim, lc)

    @staticmethod
    def get_pole_vec_pos(ik_handle=None, joint_list=None, offset=0.5):
        if ik_handle:
            joint_list = cmds.ikHandle(ik_handle, q=True, jointList=True)
            endEffector = cmds.ikHandle(ik_handle, q=True, endEffector=True)
            end_jnt = cmds.connectionInfo(endEffector + '.tx', sourceFromDestination=True).split('.')[0]
            joint_list.append(end_jnt)

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
    def get_poly_vector_through_corner(jnt_list):
        """Finds the position empirically"""
        val_list = [cmds.getAttr(x + '.r') for x in jnt_list]
        trsf = cmds.group(em=True)
        cmds.delete(cmds.pointConstraint(jnt_list[2], trsf))
        solver = cmds.createNode('ikRPsolver')
        handle = cmds.ikHandle(sol=solver, sj=jnt_list[0], ee=jnt_list[2], shf=False)[0]
        cmds.delete(cmds.pointConstraint(jnt_list[0], trsf, handle))
        pos = cmds.xform(jnt_list[1], q=True, t=True, ws=True)
        cmds.delete(handle, trsf, solver)
        for jnt, coord in zip(jnt_list, val_list):
            cmds.setAttr(jnt + '.r', *coord[0])
        return pos

    def set_to_pole_vec_pos(self, ctrl, joints):
        if joints:
            if self.is_jnt_on_line(joints[:3]):
                pos = Controller.get_poly_vector_through_corner(joints[:3])
            else:
                # Sets by three points not lying on the same straight line
                pos = Controller.get_pole_vec_pos(joint_list=joints)

            cmds.move(pos[0], pos[1], pos[2], ctrl, worldSpace=True)

    @staticmethod
    def is_jnt_on_line(jnt_list, accuracy=0.009):
        """
        Calculates whether a character's limb is straight
        """
        dist_A = distance(jnt_list[0], jnt_list[1])
        dist_B = distance(jnt_list[2], jnt_list[1])
        t_obj = cmds.group(em=True)
        const = cmds.pointConstraint(jnt_list[0], jnt_list[2], t_obj, mo=False)[0]
        attr_list = cmds.pointConstraint(const, q=True, weightAliasList=True)
        cmds.setAttr(const + '.' + attr_list[0], dist_B)
        cmds.setAttr(const + '.' + attr_list[1], dist_A)
        val = distance(t_obj, jnt_list[1]) / distance(jnt_list[2], jnt_list[0])
        cmds.delete(t_obj)
        return val < accuracy

    def set_axis_offset(self):
        if self.rotate_axis:
            self.axisGrp = cmds.group(self.name, name=self.axisGrp)
            cmds.setAttr(self.axisGrp+'.r', *self.rotate_axis)

if __name__ == '__main__':
    elbow_loc_R = {'name': 'jj',
                   'color': 17,
                   'shape': 'roll',
                   'size': 1,
                   'translate': [1, 0, 0],
                   "rotate": [0, 0, 0],
                   'hid_attr': ['sx', 'sy', 'sz', 'v']
                   }

    ctrl = Controller(**elbow_loc_R)

    ctrl.create()


