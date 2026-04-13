#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from random import uniform
import maya.cmds as cmds
import maya.mel as mm

from .utilities import distance

"""
        an_skinProcedures
    -get_skin_claster()
    -getSkin() 
    -setSkin ()
    -copySkin ()
    -swapSkin()
    -copySkinToSelVertex()
    -selectMissingRightSideJnt()
    -editSelectedJntWeights():  - run paint skin Char_DPT_tools an lock unselected jnts weights -
    -copyAndMirrowWeights()
    - get_jnt_in_same_pos()    
"""

def get_skin_claster(geo):
    skin_cluster = cmds.ls(cmds.listHistory(geo), type='skinCluster')
    if not skin_cluster:
        shape = cmds.listRelatives(geo, s = True)[0]
        skin_cluster = cmds.ls(cmds.listHistory(shape), type='skinCluster')
    if skin_cluster:
        return skin_cluster[0]
    else:
        return None


def getSkin(geo):
    skinCluster = get_skin_claster(geo)
    jnts = cmds.skinCluster(skinCluster, query=True, inf=True)
    jnts = [jnt for jnt in jnts if not cmds.connectionInfo(jnt + '.worldInverseMatrix[0]', isSource=True)]
    weight = {}
    jointIndex, skinClusterIndex, skinClusterConnect, skinClusterConnectPart = [], '', '', ''  # get jnt index and weight
    sizeArray = cmds.getAttr(geo + ".cp", size=True)
    for i in xrange(len(jnts)):
        skinClusterConnect = cmds.listConnections(jnts[i] + ".worldMatrix", type='skinCluster', plugs=True)
        flag = 0
        for skinClusterIndex in xrange(len(skinClusterConnect)):
            skinClusterConnectPart = skinClusterConnect[skinClusterIndex].split("[")
            if skinCluster + ".matrix" == skinClusterConnectPart[0]:
                flag = 1
                break
        jointIndex = skinClusterConnectPart[1][:-1]
        weight[jnts[i]] = cmds.getAttr(skinCluster + ".weightList[0:" + str(sizeArray - 1) + "].w[" + jointIndex + "]")
    weight["skinningMethod"] = cmds.getAttr(skinCluster + ".skinningMethod")
    weight["paint_weights"] = cmds.getAttr(skinCluster + ".paintWeights")  # cmds.getAttr(skinCluster+'.bw[%d]'%i)
    return weight


def setSkin(geo, weight):
    bland_attr = weight.pop("paint_weights")
    skinning_method = weight.pop("skinningMethod")

    if get_skin_claster(geo):  # unbind skin Cluster if it exists
        skCluster = get_skin_claster(geo)
        cmds.skinCluster(skCluster, e=True, unbind=True)
    cmds.select(cl=True)

    # sort	jnt forvard
    jnt = [x for x in weight.keys() if cmds.objectType(x) == 'joint'] + [x for x in weight.keys() if
                                                                         not cmds.objectType(x) == 'joint']
    skCluster = cmds.skinCluster(jnt[0], geo, tsb=True, normalizeWeights=True)[0]  # skinning

    useGeoFlag = True if [x for x in jnt if not cmds.objectType(x) == 'joint'] else False  # influense geo test
    if useGeoFlag:  cmds.setAttr(skCluster + ".useComponents", 1)
    cmds.skinCluster(skCluster, e=True, useGeometry=useGeoFlag, addInfluence=jnt[1:], wt=0.0)  # add influenses
    pointsList = range(len(weight[jnt[0]]))  # point number list
    jntAndPos = []  # joint and pos in claster list
    for jn in jnt[1:]:
        jntAndPos.append([jn,
                          [x for x in cmds.connectionInfo(jn + '.worldMatrix[0]', dfs=True) if skCluster in x][0].split(
                              ']')[0].split('[')[1]])  # get position in clasters jnt list
    for jn, pos in jntAndPos:  # go through all the joints except the first one and it positions in skin claster
        for i in pointsList:  # go through all points for carrent joint
            if weight[jn][i] > 0:  # if point weight larger than 0
                oldWeight = cmds.getAttr(
                    skCluster + ".weightList[" + str(i) + "].w[0]")  # get point weight for first joint
                cmds.setAttr(skCluster + ".weightList[" + str(i) + "].w[0]",
                             oldWeight - weight[jn][i])  # correct and set point weight for first joint
                cmds.setAttr(skCluster + ".weightList[" + str(i) + "].w[" + pos + "]",
                             weight[jn][i])  # set point weight for carrent joint

    # rebuilds dq weights
    cmds.setAttr(skCluster + ".skinningMethod", skinning_method)
    for i, each in enumerate(bland_attr):
        mm.eval('setAttr ' + skCluster + '.bw[%d] %s' % (i, each))
    return skCluster


def copySkin(geo, dest_geo):
    sourceSkin = cmds.ls(cmds.listHistory(geo, pruneDagObjects=True), type='skinCluster')[0]
    influences = cmds.skinCluster(sourceSkin, query=True, influence=True)
    joints = cmds.ls(influences, type='joint')  # getting joints list on source skinCluster
    nurbs = list(set(influences) - set(joints))  # getting nurbs list on source skinCluster
    # getting state   on source skinCluster
    useComp = cmds.getAttr(sourceSkin + '.useComponents')
    skin_method = cmds.getAttr(sourceSkin + '.skinningMethod')

    # try to find history on the destination object
    hist = cmds.listHistory(dest_geo, pruneDagObjects=True)
    # try to find skinCluster on the destination object
    dest_geoSkin = cmds.ls(hist, type='skinCluster')[0] if cmds.ls(hist, type='skinCluster') else None
    if dest_geoSkin:
        cmds.skinCluster(dest_geoSkin, e=True, unbind=True)  # unbind skinCluster with deleting history
    tempJoint = None  # create new skinCluster on destination object with joints influences
    if not joints:
        cmds.select(clear=True)
        tempJoint = cmds.joint()
        joints = tempJoint
    destSkin = cmds.skinCluster(dest_geo, joints, toSelectedBones=True, useGeometry=True, dropoffRate=4,
                                polySmoothness=False, nurbsSamples=25, rui=False, mi=5, omi=False,
                                normalizeWeights=True)[0]
    if nurbs:  # add nurbs influences in new skinCluster
        cmds.skinCluster(destSkin, edit=True, useGeometry=True, dropoffRate=4, polySmoothness=False, nurbsSamples=25,
                         lockWeights=False, weight=0, addInfluence=nurbs)

    # set state  attribute
    cmds.setAttr((destSkin + '.useComponents'), useComp)
    cmds.setAttr((destSkin + '.skinningMethod'), skin_method)

    # copy skin weights from source object to destination
    cmds.copySkinWeights(sourceSkin=sourceSkin, destinationSkin=destSkin, noMirror=True,
                         surfaceAssociation='closestPoint', influenceAssociation='oneToOne', normalize=True)
    if tempJoint:
        cmds.delete(tempJoint)  # clear template joints

    if cmds.getAttr('%s.deformUserNormals' % destSkin):  # setting up userNormals
        cmds.setAttr('%s.deformUserNormals' % destSkin, 0)


def swapSkin(s_geo='', t_geo='', setSkinWeights=True):  # source_geo, target_geo
    if not s_geo:
        s_geo, t_geo = cmds.ls(sl=True)
    s_geo_weight = getSkin(s_geo)
    t_geo_weight = getSkin(t_geo)
    base_jnt = [x for x in s_geo_weight.keys() if sum(s_geo_weight[x]) == 0][0]
    mutualJoints = list(set(s_geo_weight.keys()) & set(t_geo_weight.keys()))

    if len(mutualJoints) == 1:  # insert
        copySkin(s_geo, t_geo)
        pasted_weight = getSkin(t_geo)
        base_jnt_weight = t_geo_weight.pop(base_jnt)
        for jnt in pasted_weight.keys():
            t_geo_weight[jnt] = [pasted_weight[jnt][i] * base_jnt_weight[i] for i in range(len(base_jnt_weight))]
        if setSkinWeights:
            setSkin(t_geo, t_geo_weight)
            cmds.select(s_geo, t_geo)
        return t_geo_weight
    else:  # extract
        jnts = [x for x in s_geo_weight.keys() if not x == base_jnt]
        for v in xrange(len(t_geo_weight[base_jnt])):
            t_geo_weight[base_jnt][v] = sum([t_geo_weight[jn][v] for jn in jnts])
        for jn in jnts:
            t_geo_weight.pop(jn)
        if setSkinWeights:
            setSkin(t_geo, t_geo_weight)
            cmds.select(s_geo, t_geo)
        return t_geo_weight


def copySkinToSelVertex(sourceObj, destVert):  # copy Skin Weights from object to list of vertex on over object
    destObj = destVert[0].split('.')[0]
    sourceSkin = cmds.ls(cmds.listHistory(sourceObj, pruneDagObjects=True), type='skinCluster')[0]
    influences = cmds.skinCluster(sourceSkin, query=True, influence=True)
    joints = cmds.ls(influences, type='joint')  # getting joints list on source skinCluster
    nurbs = list(set(influences) - set(joints))  # getting nurbs list on source skinCluster
    useComp = cmds.getAttr(
        sourceSkin + '.useComponents')  # getting state of "useComponents" attribute on source skinCluster
    destObjSkin = cmds.ls(cmds.listHistory(destObj, pruneDagObjects=True), type='skinCluster')[
        0]  # find skinCluster on the destination object
    destInfluences = cmds.skinCluster(destObjSkin, query=True, influence=True)
    for inf in influences:
        if cmds.nodeType(inf) == 'joint' and not inf in destInfluences:
            cmds.skinCluster(destObjSkin, edit=True, lockWeights=False, weight=0, addInfluence=inf)
    cmds.select(sourceObj, destVert)
    cmds.copySkinWeights(noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne',
                         normalize=True)
    cmds.select(cl=True)


def selectMissingRightSideJnt():
    objectName = cmds.ls(sl=True)[0]
    skinClusterName = cmds.ls(cmds.listHistory(objectName, pdo=1), type='skinCluster')[0]  ### if claster sel
    history = cmds.listHistory(objectName)
    clustersName = cmds.ls(history, type='skinCluster')
    skinClusterSetName = cmds.listConnections(skinClusterName, type='objectSet')
    jointName = cmds.ls(cmds.listHistory(skinClusterName, levels=1), type='transform')
    rSidJnt = ['r_' + x[2:] for x in jointName if 'l_' == x[:2]]
    missingJnt = []
    for jnt in rSidJnt:
        if not jnt in jointName:
            missingJnt.append(jnt)
    cmds.select(missingJnt)


def editSelectedJntWeights():
    geo = cmds.ls(sl=True)[-1]
    jnts = cmds.ls(sl=True)[:-1]
    skinClusterV = cmds.ls(cmds.listHistory(geo), type='skinCluster')[0]
    jointName = cmds.ls(cmds.listHistory(skinClusterV, levels=1), type='transform')

    for jnt in [x for x in jointName if not x in jnts]:  cmds.setAttr(jnt + '.liw', 1)
    for jnt in jnts:  cmds.setAttr(jnt + '.liw', 0)

    cmds.select(geo)
    mm.eval("ArtPaintSkinWeightsToolOptions;")
    mm.eval('setSmoothSkinInfluence ' + jnts[0] + ' ;artSkinRevealSelected artAttrSkinPaintCtx;')


def copyAndMirrowWeights(s_geo='', t_geo=''):
    if not s_geo:  s_geo, t_geo = cmds.ls(sl=True)
    if cmds.ls(cmds.listHistory(t_geo), type='skinCluster'):  # unbind skin Cluster if it exists
        skCluster = cmds.ls(cmds.listHistory(t_geo), type='skinCluster')[0]
        cmds.skinCluster(skCluster, e=True, unbind=True)
    hist = cmds.listHistory(s_geo, pruneDagObjects=True)  # try to find history on the destination object
    s_geoSkin = cmds.ls(hist, type='skinCluster')[0] if cmds.ls(hist, type='skinCluster') else None
    jointName = cmds.ls(cmds.listHistory(s_geoSkin, levels=1), type='transform')
    rSidJnt = []
    for jnt in jointName:
        if 'l_' == jnt[:2]:
            rSidJnt.append('r_' + jnt[2:])
        else:
            rSidJnt.append(jnt)

    jnt = [x for x in rSidJnt if cmds.objectType(x) == 'joint'] + [x for x in rSidJnt if not cmds.objectType(
        x) == 'joint']  # sort	jnt forvard
    skCluster = cmds.skinCluster(rSidJnt, t_geo, tsb=True, normalizeWeights=True)[0]  # skinning
    cmds.select(s_geo, t_geo)
    mm.eval('MirrorSkinWeights')


def get_jnt_in_same_pos(geometry, accuracy=0.01):
    """
    Returns a list of joints from a skin cluster located at the same point.
    Used for correct copying of scales
    """

    skin_cluster = cmds.ls(cmds.listHistory(geometry, pdo=1), type='skinCluster')[0]
    joints_list = cmds.ls(cmds.listHistory(skin_cluster, levels=1), type='joint')

    right_joints = list()
    for jnt in joints_list:
        pos = cmds.xform(jnt, q=True, t=True, ws=True)
        if pos[0] > 0 + accuracy:
            right_joints.append(jnt)
    wrong_joints = list()

    while right_joints:
        jntA = right_joints.pop(0)
        if [x for x in right_joints if distance(jntA, x) < accuracy]:
            wrong_joints.append(jntA)

    return wrong_joints


def get_non_centr_points(vertices, accuracy):
    """
    Returns a list of geometry vertices excluding those centered on the x-axis (used for mirroring weights)
    """
    result = []
    for vertex in vertices:
        x_pos = cmds.pointPosition(vertex)[0]
        if abs(x_pos) > accuracy:
            result.append(vertex)
    return result


def get_opposite_jnt(jnt, accuracy=0.001):
    """
    Finds a joint matching by name and position on the right side
    """
    if not jnt:
        return None

    patterns = {r'(.*:)Left(\d{0,3}_?.*)': r'\1Right\2',  # jpn_yakuza_skeleton:Left_hand_hold
                r'Left(\d{0,3}_?.*)': r'Right\1',  # jpn_yakuza_skeleton:Left_hand_hold
                r'(.*)L\b': r'\1R',  # jpn_yakuza_skeleton:ARMupL, forearm_L
                r':L(\d{0,3})': r':R\1',  # jpn_yakuza_skeleton:Ltit, jpn_yakuza_skeleton:L4_fng1
                r'^L(\d{0,3}_?.*)': r'R\1'}  # L4_fng1, Ltit
    r_jnt = None

    # get opposite name
    for l_pattern in patterns.keys():
        if re.search(l_pattern, jnt):
            r_pattern = patterns[l_pattern]
            r_jnt = re.sub(l_pattern, r_pattern, jnt)
            # print(l_pattern, r_jnt)
            break
    # test opposite position
    if r_jnt and cmds.objExists(r_jnt):
        l_pos = cmds.xform(jnt, q=True, t=True, ws=True)
        r_pos = cmds.xform(r_jnt, q=True, t=True, ws=True)
        r_pos[0] = abs(r_pos[0])
        if distance(l_pos, r_pos) > accuracy:
            return None
    else:
        return None
    return r_jnt

def temp_joints(l_jnt, r_jnt):
    cmds.select(cl=True)
    SFX = '_tmp_jnt'
    pos = cmds.xform(l_jnt, q=True, t=True, ws=True)
    pos[1] += uniform(0.02, 0.2)
    l_tmp_jnt = cmds.joint(n=l_jnt+SFX, p=pos)
    r_tmp_jnt = None
    if r_jnt:
        pos[0] *= -1
        cmds.select(cl=True)
        r_tmp_jnt = cmds.joint(n=r_jnt + SFX, p=pos)
    return l_tmp_jnt, r_tmp_jnt


def mirror_weight(geo, accuracy=0.001):
    # todo: DQ Blend Weight delete error
    weight = getSkin(geo)

    vertices = cmds.ls(geo + '.vtx[*]', fl=True)
    if accuracy:
        vertices = get_non_centr_points(vertices, accuracy)

    l_joints = get_jnt_in_same_pos(geo)

    joints = list()
    for jnt in l_joints:
        opposite_jnt = get_opposite_jnt(jnt)
        joints.append([jnt, opposite_jnt])

    for l_jnt, r_jnt in joints:
        l_tmp_jnt, r_tmp_jnt = temp_joints(l_jnt, r_jnt)
        weight[l_tmp_jnt] = weight.pop(l_jnt)
        if r_tmp_jnt:
            weight[r_tmp_jnt] = weight.pop(r_jnt)

    setSkin(geo, weight)
    skin_cluster = cmds.ls(cmds.listHistory(geo, pdo=1), type='skinCluster')[0]
    cmds.copySkinWeights(ss=skin_cluster, ds=skin_cluster, mirrorMode='YZ', mirrorInverse=False)
    weight = getSkin(geo)

    for l_jnt, r_jnt in joints:
        weight[l_jnt] = weight.pop(l_jnt + '_tmp_jnt')
        if r_jnt + '_tmp_jnt' in weight.keys():
            weight[r_jnt] = weight.pop(r_jnt + '_tmp_jnt')

    setSkin(geo, weight)

    for each in joints:
        for jnt in each:
            if cmds.objExists(jnt + '_tmp_jnt'):
                cmds.delete(jnt + '_tmp_jnt')


def right_side_joints_test(geo, accuracy=0.01):
    skin_cluster = cmds.ls(cmds.listHistory(geo, pdo=1), type='skinCluster')[0]
    joints_list = cmds.ls(cmds.listHistory(skin_cluster, levels=1), type='joint')

    not_skinned_joints = list()
    for jnt in joints_list:
        pos = cmds.xform(jnt, q=True, t=True, ws=True)
        if pos[0] > 0 + accuracy:
            r_jnt = get_opposite_jnt(jnt)
            #print jnt, r_jnt
            if r_jnt not in joints_list:
                not_skinned_joints.append(r_jnt)

    return [x for x in not_skinned_joints if x]






if __name__ == '__main__':
    #mirror_weight("pPlane1")
    not_skinned_joints = right_side_joints_test('jacket')
    print not_skinned_joints
    #right_side_joints_test("pPlane1")
