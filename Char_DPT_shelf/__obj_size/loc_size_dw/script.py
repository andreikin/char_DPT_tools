import maya.cmds as cmds

# Find all locator shapes in the scene
locators = cmds.ls(type='locator')

for loc in locators:
    # Each locator has localScaleX/Y/Z
    for axis in ['X', 'Y', 'Z']:
        attr = loc + '.localScale' + axis
        if cmds.objExists(attr):
            current = cmds.getAttr(attr)
            cmds.setAttr(attr, current * 0.8)