import maya.cmds as cmds
import maya.mel as mm
import maya.OpenMaya as om

if len(cmds.ls(sl=True)) < 3:
    mm.eval("ArtPaintSkinWeightsTool;")
else:
    geo = cmds.ls(sl=True)[-1]
    jnts = cmds.ls(sl=True)[:-1]
    skinClusterV = cmds.ls(cmds.listHistory(geo), type='skinCluster')[0]
    jointName = cmds.ls(cmds.listHistory(skinClusterV, levels=1), type='transform')  # jnt

    for jnt in [x for x in jointName if not x in jnts]:
        cmds.setAttr(jnt + '.liw', 1)
    for jnt in jnts:
        cmds.setAttr(jnt + '.liw', 0)

    cmds.select(geo)
    mm.eval("ArtPaintSkinWeightsToolOptions;")
    mm.eval('setSmoothSkinInfluence ' + jnts[0] + ' ;artSkinRevealSelected artAttrSkinPaintCtx;')
