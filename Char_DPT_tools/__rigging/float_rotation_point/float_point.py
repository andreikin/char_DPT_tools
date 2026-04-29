import maya.cmds as cmds


def float_point (ctrl, pfx = None):
    cmds.delete(ctrl, ch=True)
    pfx = "" if not pfx else pfx
    ctrlShape = cmds.listRelatives(ctrl, s=True)[0]
    # solve ct size
    st_size = 0
    for i in (0, 1, 2):
        mn = cmds.getAttr(ctrlShape + '.boundingBoxMin')[0][i]
        mx = cmds.getAttr(ctrlShape + '.boundingBoxMax')[0][i]
        if st_size < (mx - mn):
            st_size = (mx - mn)

    # create up locator, out_circle and copy of controller
    up_loc = cmds.spaceLocator(n=pfx + "Up_loc")[0]
    out_circle = cmds.circle(n=pfx + "OutCircle_crv", ch=False, o=True, nr=[0, 1, 0], r=st_size * 5)[0]
    up_loc_grp = cmds.group(up_loc, name=pfx + "Locator_grp")
    cmds.setAttr(up_loc + ".ty", st_size * 5)
    ctrl_copy = cmds.duplicate(ctrl, n=pfx + "Solve_crv", renameChildren=True)[0]
    ctrl_copy_shape = cmds.listRelatives(ctrl_copy, s=True)[0]

    # get points number and connect two curves
    p_num = cmds.getAttr(ctrlShape + ".spans")
    for i in range(p_num):
        cmds.connectAttr(ctrlShape + ".controlPoints[" + str(i) + "]",
                         ctrl_copy_shape + ".controlPoints[" + str(i) + "]")

        # move poin to tefresh
        cmds.select(ctrl + ".cv[" + str(i) + "]", r=True)
        cmds.move(-0.01, 0, 0, r=True)
        cmds.move(0.01, 0, 0, r=True)

    # if ctrl_copy has parent - unparent ctrl_copy
    if cmds.listRelatives(ctrl_copy, p=True):
        cmds.parent(ctrl_copy, world=True)

    # moove ctrl_copy to centre
    for d in (".t", ".r"):
        cmds.setAttr(ctrl_copy + d, 0, 0, 0)

    POnCurve1 = cmds.createNode("nearestPointOnCurve", n=pfx + "POnCurve1")
    POnCurve2 = cmds.createNode("nearestPointOnCurve", n=pfx + "POnCurve2")
    cmds.connectAttr(ctrl + ".rotate", up_loc_grp + ".rotate", force=True)
    cmds.connectAttr(up_loc + "Shape.worldPosition[0]", POnCurve2 + ".inPosition", force=True)
    cmds.connectAttr(out_circle + "Shape.worldSpace[0]", POnCurve2 + ".inputCurve", force=True)
    cmds.connectAttr(POnCurve2 + ".position", POnCurve1 + ".inPosition", force=True)
    cmds.connectAttr(ctrl_copy_shape + ".worldSpace[0]", POnCurve1 + ".inputCurve", force=True)
    cmds.connectAttr(POnCurve1 + ".position", ctrl + ".rotatePivot", force=True)

    # lock attr
    for attr in (".tx", ".ty", ".tz", ".ry", ".sx", ".sy", ".sz", ".v"):
        cmds.setAttr(ctrl + attr, lock=True, keyable=False)
    rig_grp = cmds.group(out_circle, up_loc_grp, ctrl_copy, name=pfx + "FlP_grp")

    if not cmds.objExists(ctrl + ".rigVis"):
        cmds.addAttr(ctrl, ln="rigVis", at="enum", en="off:on", keyable=False)
    cmds.connectAttr(ctrl + ".rigVis", rig_grp + ".v", force=True)

    return rig_grp, ctrl_copy