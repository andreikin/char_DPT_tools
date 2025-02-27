import maya.cmds as cmds

objects = cmds.ls(sl=True)
attributes = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)

for obj in objects:
    if attributes:
        for atr in attributes:
            cmds.setAttr(obj + "." + atr, e=True, k=False, l=True)
    else:
        for vObj in cmds.ls(sl=True):
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
                cmds.setAttr(obj + "." + attr, lock=False, keyable=True)
