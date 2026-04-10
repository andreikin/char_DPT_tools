import maya.cmds as cmds
import maya.OpenMaya as om
import logging


from controller_library import ControllerLibrary
from utilities import namespace_off, suffix_minus, rename_shape, unique_names_generator

logger = logging.getLogger(__name__)
logger.handlers = []
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s  %(levelname)s  %(filename) 17s.%(funcName)s() %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class Controller(ControllerLibrary):
    global_scale = 1
    SFX = "_CT"
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
        namespace = current_namespace+':' if ':' not in current_namespace else ""

        # if there is at least one object, then we generate a new set of names
        if any([cmds.objExists(namespace+x) for x in (self.name, self.conGrp, self.oriGrp)]):
            for i in range(1, 100):
                new_pfx = self.pfx + '{0:03d}'.format(i)
                if all([not cmds.objExists(namespace+new_pfx+x) for x in (self.SFX, self.SFX_CON, self.SFX_ORI)]):
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
        logger.debug("Controller " + self.name + " successfully created \n \n")
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
        pfx = suffix_minus(self.name)
        self.conGrp = cmds.group(name=self.conGrp, empty=True)
        self.oriGrp = cmds.group(self.conGrp, name=self.oriGrp)
        cmds.parent(self.name, self.conGrp)
        logger.debug(" executed")

    def set_size(self, size):
        size = size if size else self.size
        size = size if type(size) == list else [size, size, size]
        cmds.setAttr(self.name + ".scale", float(size[0]), float(size[0]), float(size[0]))
        cmds.makeIdentity(self.name, apply=True)
        # logger.debug(" executed")

    def set_shape_rotation_offset(self):
        cmds.setAttr(self.name + ".rotate", *self.shape_rotation_offset)
        cmds.makeIdentity(self.name, apply=True)
        logger.debug(" executed")

    def set_shape_translation_offset(self):
        cmds.setAttr(self.name + ".translate", *self.shape_translation_offset)
        cmds.makeIdentity(self.name, apply=True)
        cmds.move(0, 0, 0, self.name + '.scalePivot', self.name + '.rotatePivot', absolute=True)
        logger.debug(" executed")

    def hide_attributes(self, hid_attr):
        hid_attr = hid_attr if hid_attr else self.hid_attr
        if hid_attr:
            for attr in hid_attr:
                cmds.setAttr(self.name + "." + attr, lock=True, keyable=False)
            logger.debug(" executed")

    def parent_constraint(self):
        if self.prt_const_targets:
            self.prt_constraint = cmds.parentConstraint(self.prt_const_targets, self.oriGrp, mo=True)[0]
            logger.debug(" executed")

    def align_to(self, align_obj, orient=True, point=True):
        align_obj = align_obj if align_obj else self.align_obj
        if align_obj:
            if orient:
                cmds.delete(cmds.orientConstraint(align_obj, self.oriGrp, mo=False))
            if point:
                cmds.delete(cmds.pointConstraint(align_obj, self.oriGrp, mo=False))
            logger.debug(" executed")

    def parent_to(self, parent=None):
        parent = parent if parent else self.parent
        if parent:
            try:
                cmds.parent(self.oriGrp, parent)
                logger.debug(self.oriGrp + " parented to " + parent)
            except Exception as message:
                logger.debug(message)


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
            logger.error("Required a handler or a list of bones")
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
        logger.debug(" executed")
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
    @namespace_off
    def mirrow_shape(source, target):
        sourse_shapes = [x for x in cmds.listRelatives(source, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        target_shapes = [x for x in cmds.listRelatives(target, s=True) if cmds.nodeType(x) == u'nurbsCurve']
        for i in range(len(sourse_shapes)):
            point_num = cmds.getAttr(sourse_shapes[i] + '.spans') + cmds.getAttr(sourse_shapes[i] + '.degree')
            for pn in xrange(point_num):
                pos = cmds.xform(sourse_shapes[i] + '.controlPoints[' + str(pn) + ']', q=True, t=True, ws=True)
                cmds.xform(target_shapes[i] + '.controlPoints[' + str(pn) + ']', t=[pos[0] * -1, pos[1], pos[2]], ws=True)

logger.debug(" executed")


# cod for testing Controller class

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
