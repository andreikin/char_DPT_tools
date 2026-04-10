import os

import maya.cmds as cmds
import json



TOOL_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
CONTROLLERS_LIBRARY_NAME = 'controllers_library.json'
CONTROLLERS_LIBRARY_PATH = os.path.join(TOOL_DIRECTORY, CONTROLLERS_LIBRARY_NAME)

class ControllerLibrary(object):
    """
    Class library of various forms of controllers
    """
    def __init__(self):
        self.lib = dict()

        with open(CONTROLLERS_LIBRARY_PATH, 'r') as f:
            self.lib = json.load(f)

    def shape_presets(self, shape_type):
        return self.lib[shape_type]

    def shape_list(self):
        return self.lib.keys()

    @staticmethod
    def get_ct_shape(curve_name, accuracy=3):
        """
        Returns the parameters needed to create a curve
        """
        output_data = list()
        ct_shape_list = cmds.listRelatives(curve_name, shapes=True)
        for shape in ct_shape_list:
            degrees = cmds.getAttr(shape + '.degree')
            periodic = True if cmds.getAttr(shape + '.form') == 2 else False
            curve_info = cmds.createNode('curveInfo')
            cmds.connectAttr(shape + '.worldSpace', curve_info + '.inputCurve')
            knots = cmds.getAttr(curve_info + '.knots[*]')
            cmds.delete(curve_info)
            cvs = list()
            for i in range(cmds.getAttr(shape + '.spans')):
                pos = cmds.xform(curve_name + '.cv[' + str(i) + ']', q=True, t=True, ws=True)
                cvs.append([round(pos[0], accuracy), round(pos[1], accuracy), round(pos[2], accuracy)])
            data = {'degree': degrees, 'periodic': periodic, 'point': cvs, 'knot': knots}
            output_data.append(data)
        return output_data
