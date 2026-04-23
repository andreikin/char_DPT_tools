

"""
Main Procedure:

attribute_visibility

Creation Date:
    10.04.2024

Authors:
    Belyaev Andrey
    andreikin@mail.ru

Description:
The script works with selected objects in Autodesk Maya and their attributes from the Channel Box.
If specific attributes are selected in the Channel Box, it makes them non-animatable by hiding them from keyable and locking them.
If no attributes are selected, the script instead unlocks and makes keyable the main transform channels of the object.
"""


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


