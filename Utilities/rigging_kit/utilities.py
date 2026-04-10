import json
import math
import re
import sys

import maya.OpenMaya as om
import maya.cmds as cmds

from rigging_kit.names import namespace_off

PFX_PATTERN = '^(L_|R_|l_|r_|left_|right_|Left_|Right_)'
DIGIT_PATTERN = r'\d{1,}$'
RIG_VISIBILITY_ATTR = 'rig_visibility'
DEL_LIST_ATTRIBUTE = 'delList'
NON_ANIMATED_ATTRIBUTES = ['scaleX', 'scaleY', 'scaleZ', 'lockInfluenceWeights', 'visibility', 'blendOrient',
                           'blendParent', 'blendPoint']

def connect_via_reverse(input, output):
    """
    Connects two attributes through a reverse node that inverts the transmitted value
    """
    reverse = cmds.createNode('reverse')
    cmds.connectAttr(input, reverse + '.inputX')
    cmds.connectAttr(reverse + '.outputX', output)
    return reverse

@namespace_off
def copy_joints_chain(jnts_list):
    """
    Copies only the specified chain of bones from the hierarchy without other child objects
    """
    out = list()
    for jnt in jnts_list:
        copy_jnt = cmds.duplicate(jnt, renameChildren=True)
        if len(copy_jnt) > 1:
            cmds.delete(copy_jnt[1:])
        out.append(copy_jnt[0])
    for i in range(len(out) - 1):
        cmds.parent(out[i + 1], out[i])
    return out


def distance(start, end):
    """
    Calculate the distance between two objects or coordinates
    """
    types = [str] if sys.version[0] == '3' else [str, unicode]
    a = cmds.xform(start, q=True, t=True, ws=True) if type(start) in types else start
    b = cmds.xform(end, q=True, t=True, ws=True) if type(end) in types else end
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))

def rig_visibility(controller, objects_list, dv=False):
    """
    Hides auxiliary rigging objects whose visibility can be changed using an attribute 'rig_visibility'
    """
    if not cmds.objExists(controller + '.' + RIG_VISIBILITY_ATTR):
        cmds.addAttr(controller, ln=RIG_VISIBILITY_ATTR, dv=dv, k=True, at='enum', en='off:on')
    for v_each in objects_list:
        if not cmds.connectionInfo(v_each + '.v', id=True):
            cmds.connectAttr(controller + '.' + RIG_VISIBILITY_ATTR, v_each + '.v')


def delete_sys(ctrlObject, objList):
    """
    Creates a system of connections to remove the rig without leaving garbage
    """
    if objList:
        delObgList = []
        if cmds.objExists(ctrlObject + '.' + DEL_LIST_ATTRIBUTE):
            # If the attribute exists, read data from it
            delObgList = cmds.listConnections(ctrlObject + '.' + DEL_LIST_ATTRIBUTE, s=True, d=False)
        else:
            # if the attribute does not exist, creates it
            cmds.addAttr(ctrlObject, ln=DEL_LIST_ATTRIBUTE, at='message', multi=True, keyable=False)

        # We create connections taking into account existing ones
        for index, obj in enumerate(objList):
            cmds.connectAttr(obj + '.message',
                             ctrlObject + '.' + DEL_LIST_ATTRIBUTE + '[' + str(index + len(delObgList)) + ']')


def activate_delete_sys(ctrlObject):
    """
    Removes  rig system without unwanted garbage
    """
    if cmds.objExists(ctrlObject + '.' + DEL_LIST_ATTRIBUTE):  # if del object has attribute
        del_obj_list = cmds.listConnections(ctrlObject + '.' + DEL_LIST_ATTRIBUTE, s=True, d=False)  # get del attr list
        if ctrlObject in del_obj_list:
            del_obj_list.remove(ctrlObject)
        for obj in del_obj_list:
            if cmds.objExists(obj + '.' + DEL_LIST_ATTRIBUTE):
                # if the object to be deleted has an attribute, recursion is started
                activate_delete_sys(obj)
            else:
                if cmds.objExists(obj):
                    cmds.delete(obj)
        if cmds.objExists(ctrlObject):
            cmds.delete(ctrlObject)
    else:
        if cmds.objExists(ctrlObject):
            cmds.delete(ctrlObject)


def save_data_on_rig(data, scene_object, attribute):
    """
    Stores the necessary information on object within a scene
    """
    if not cmds.objExists(scene_object + '.' + attribute):
        cmds.addAttr(scene_object, ln=attribute, dt="string", keyable=False)
    cmds.setAttr(scene_object + '.' + attribute, json.dumps(data), type="string")


def get_data_from_rig(scene_object, attribute):
    """
    Reads the required information from object inside the scene
    """
    if not cmds.objExists(scene_object + '.' + attribute):
        return None
    data_string = cmds.getAttr(scene_object + '.' + attribute)
    return json.loads(data_string)


def add_additional_settings(settings, additional_settings, need_changelog=True, path =''):
    """
    Adds settings from the second dictionary to the first one and also makes changes to the settings data.
    printing log of changing
    :param settings: dictionary. old settings
    :param additional_settings: dictionary. changes in settings
    :param need_changelog: bool. variable - whether it is necessary to print changelog
    :param path: service variable. string. Contains change paths for changelog
    :return: dictionary. Updated list of settings
    """

    if settings == additional_settings or type(settings) != dict:
        if settings != additional_settings and need_changelog:
            print('Change in -', path[:-1])
        return additional_settings

    keys_source = settings.keys()

    for key in additional_settings.keys():
        if key in keys_source:
            settings[key] = add_additional_settings(settings[key], additional_settings[key], need_changelog, path + key + '/')
        else:
            settings[key] = additional_settings[key]
            if need_changelog:
                print('Add in -', path[1:] + key)
    return settings


def remove_all_animation(obj):
    """
    Removes all animation from the specified object.
    """
    attributes = cmds.listAttr(obj, keyable=True)
    if attributes:
        for attr in attributes:
            full_attr = "{}.{}".format(obj, attr)
            if cmds.keyframe(full_attr, query=True):
                cmds.cutKey(full_attr, clear=True)


def remove_redundant_keys(obj, accuracy=0.001):
    """
    if the channel is static, delete all keys except the first and last.
    """
    anim_curves = cmds.listConnections(obj, type='animCurve')
    if not anim_curves:
        return

    for curve in anim_curves:
        # check for more than two keys
        key_count = cmds.keyframe(curve, query=True, keyframeCount=True)
        if key_count <= 2:
            continue
        # We get keys and values, remove unnecessary ones
        times = cmds.keyframe(curve, query=True, timeChange=True)
        values = cmds.keyframe(curve, query=True, valueChange=True)
        if (max(values) - min(values)) < accuracy:
            cmds.cutKey(curve, time=(times[1], times[-2]))


