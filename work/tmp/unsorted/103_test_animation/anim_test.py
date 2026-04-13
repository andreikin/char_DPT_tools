# -*- coding: utf-8 -*-

import math
import maya.OpenMaya as om
import maya.cmds as cmds

TIME_RANGE = 10


def test_animation():
    joints_list = cmds.ls(sl=True)
    if not len(joints_list):
        om.MGlobal.displayError('Joint must be selected')
        return
    if cmds.keyframe(joints_list[0], query=True, keyframeCount=True) == 0:
        curent_time = 0
        for jnt in joints_list:
            set_key(jnt, curent_time)
            curent_time += TIME_RANGE * 8
        cmds.playbackOptions(minTime=0, maxTime=curent_time)
    else:
        for i, jnt in enumerate(joints_list):
            remove_anim_for_selected(jnt)


def set_key(joint, curent_time):
    """
    Sets test for animation keys
    """
    cmds.setKeyframe(joint, attribute='rz', t=curent_time, v=0)
    cmds.setKeyframe(joint, attribute='rz', t=curent_time + TIME_RANGE, v=90)
    cmds.setKeyframe(joint, attribute='rz', t=curent_time + TIME_RANGE * 3, v=-90)
    cmds.setKeyframe(joint, attribute='rz', t=curent_time + TIME_RANGE * 4, v=0)

    cmds.setKeyframe(joint, attribute='ry', t=curent_time + TIME_RANGE * 4, v=0)
    cmds.setKeyframe(joint, attribute='ry', t=curent_time + TIME_RANGE * 5, v=90)
    cmds.setKeyframe(joint, attribute='ry', t=curent_time + TIME_RANGE * 7, v=-90)
    cmds.setKeyframe(joint, attribute='ry', t=curent_time + TIME_RANGE * 8, v=0)

    # Add a special attribute for subsequent search and deletion of the node
    for attr in ['.rz', '.ry']:
        anim_curve = cmds.listConnections(joint + attr, type="animCurve")[0]
        cmds.addAttr(anim_curve, longName='tmp', keyable=False)


def remove_anim_for_selected(obj):
    """
    Removes test animation
    """
    animated_attrs = cmds.listAnimatable(obj)
    if animated_attrs:
        for attr in ['.rz', '.ry']:
            cmds.cutKey(obj, attribute=attr)
            cmds.setAttr(obj + attr, 0)


def remove_all_temp_animation():
    """
    Removes all curves for test animation
    """
    for node in cmds.ls(type="animCurve"):
        if cmds.objExists(node + '.tmp'):
            cmds.delete(node)


if __name__ == '__main__':
    test_animation()

