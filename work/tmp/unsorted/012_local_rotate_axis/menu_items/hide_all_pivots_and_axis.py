import maya.cmds as cmds

objects = cmds.ls()
for obj in objects:
    for attr in ['displayRotatePivot', 'displayLocalAxis']:
        try:
            cmds.setAttr(obj + "." + attr, 0)
        except Exception as e:
            pass
