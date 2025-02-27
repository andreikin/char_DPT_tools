import maya.cmds as cmds

attributes = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
objects = cmds.ls(sl=True)

if attributes:  # if attr selected
    for obj in objects:
        for attr in attributes:
            if cmds.objExists(obj + '.' + attr) and cmds.getAttr(obj + '.' + attr, settable=True):
                cmds.setAttr(obj + '.' + attr, 0)  # set attr to 0

else:  # else set all transform to 0
    for obj in cmds.ls(sl=True):
        for attr in cmds.listAttr(obj, r=True, k=True):
            if attr in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
                cmds.setAttr(obj + '.' + attr, 0)
