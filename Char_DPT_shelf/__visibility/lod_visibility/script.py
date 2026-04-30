import maya.cmds as cmds

geomertry_list = cmds.ls(type='transform')

for geomertry in geomertry_list:

    if 'LOD' in geomertry:
        print (geomertry)
        cmds.setAttr(geomertry + '.v', 0)