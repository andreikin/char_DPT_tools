import maya.cmds as cmds


def rivet(seurface='', edges=[], out='locator'):
    if not seurface:
        sel = cmds.filterExpand(sm=32)
        if not sel:
            cmds.error("You mast select 2 edges")
        seurface = sel[0].split('.')[0]
        edges = [x.split('[')[1].split(']')[0] for x in sel]

    nameCFME1 = cmds.createNode('curveFromMeshEdge', n=seurface + "rivetCurveFromMeshEdge1")
    cmds.setAttr(".ihi", 1)
    cmds.setAttr(".ei[0]", int(edges[0]))
    nameCFME2 = cmds.createNode('curveFromMeshEdge', n=seurface + "rivetCurveFromMeshEdge2")
    cmds.setAttr(".ihi", 1)
    cmds.setAttr(".ei[0]", int(edges[1]))
    nameLoft = cmds.createNode('loft', n=seurface + "rivetLoft1")
    cmds.setAttr(nameLoft + ".ic", s=2)
    cmds.setAttr(nameLoft + ".u", True)
    cmds.setAttr(nameLoft + ".rsn", True)
    namePOSI = cmds.createNode('pointOnSurfaceInfo', n=seurface + "rivetPointOnSurfaceInfo1")
    cmds.setAttr(".turnOnPercentage", 1)
    cmds.setAttr(".parameterU", 0.5)
    cmds.setAttr(".parameterV", 0.5)
    cmds.connectAttr(nameLoft + ".os", namePOSI + ".is", f=True)
    cmds.connectAttr(nameCFME1 + ".oc", nameLoft + ".ic[0]")
    cmds.connectAttr(nameCFME2 + ".oc", nameLoft + ".ic[1]")
    cmds.connectAttr(seurface + ".w", nameCFME1 + ".im")
    cmds.connectAttr(seurface + ".w", nameCFME2 + ".im")
    if out == 'locator':
        nameLocator = cmds.createNode('transform')
        cmds.createNode('locator', n=nameLocator + "Shape", p=nameLocator)
    else:
        nameLocator = cmds.createNode('joint')

    nameAC = cmds.createNode('aimConstraint', p=nameLocator, n=nameLocator + "_rivetAimConstraint1")
    cmds.setAttr(".tg[0].tw", 1)
    cmds.setAttr(".a", 0, 1, 0)
    cmds.setAttr(".u", 0, 0, 1)
    for attr in [".v", ".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz"]: cmds.setAttr(nameLocator + attr,
                                                                                                    k=False)
    cmds.connectAttr(namePOSI + ".position", nameLocator + ".translate")
    cmds.connectAttr(namePOSI + ".n", nameAC + ".tg[0].tt")
    cmds.connectAttr(namePOSI + ".tv", nameAC + ".wu")
    for d in ('x', 'y', 'z'): cmds.connectAttr(nameAC + ".cr" + d, nameLocator + ".r" + d)
    return nameLocator


def an_convertSliceToList(pList):
    output = list()
    for pName in pList:
        if '.' in pName:
            iRenge = pName.split(']')[0].split('[')[1]
            if ':' in iRenge:
                for i in range(int(iRenge.split(':')[0]), int(iRenge.split(':')[1]) + 1):
                    output.append(pName.split('[')[0] + '[' + str(i) + ']')
            else:
                output.append(pName)
        else:
            output.append(pName)
    return output


def getNum(comp):
    return int(comp.split('[')[1][:-1])


def do_rivet():
    surface = cmds.ls(sl=1)[0].split('.')[0]
    sel = cmds.filterExpand(sm=32)  # get edge
    if sel:
        print surface, getNum(sel[0]), getNum(sel[1])
        rivet(surface, [getNum(sel[0]), getNum(sel[1])])
    else:
        sel = cmds.filterExpand(sm=34)  # get face
        edges = an_convertSliceToList(cmds.polyListComponentConversion(sel, te=True))  # get edges
        data = dict()
        for edg in edges:
            pt = an_convertSliceToList(cmds.polyListComponentConversion(edg, tv=True))
            data[edg] = [getNum(x) for x in pt]
        egesCapl = [x for x in edges[1:] if
                    (data[edges[0]][0] not in data[x]) and (data[edges[0]][1] not in data[x])] + [edges[0]]
        print surface, getNum(egesCapl[0]), getNum(egesCapl[1])
        rivet(surface, edges=[getNum(egesCapl[0]), getNum(egesCapl[1])])

do_rivet()