import maya.cmds as cmds

mods = cmds.getModifiers()
attr = 'displayRotatePivot' if (mods & 1) > 0 else 'displayLocalAxis'
sel = cmds.ls(sl=True)
for each in sel:
    val = 1 if not cmds.getAttr(each + "." + attr) else 0
    cmds.setAttr(each + "." + attr, val)
