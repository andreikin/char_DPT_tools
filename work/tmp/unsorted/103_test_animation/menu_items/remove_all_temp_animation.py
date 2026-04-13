import maya.cmds as cmds


cmds.currentTime(0)
for node in cmds.ls(type="animCurve"):
    if cmds.objExists(node + '.tmp'):
        cmds.delete(node)