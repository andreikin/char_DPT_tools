import maya.cmds as cmds

geomertry_list = cmds.ls(type='transform')

lod_geomertry_list = [x for x in geomertry_list if 'LOD' in x]

if lod_geomertry_list:
    val = cmds.getAttr(lod_geomertry_list[0] + '.v')
    val = 1 if val ==0 else 0

for geomertry in lod_geomertry_list:
        cmds.setAttr(geomertry + '.v', val)