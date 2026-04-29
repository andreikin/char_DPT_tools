#!/usr/bin/env python
# -*- coding: utf-8 -*-
import maya.cmds as cmds

"""
        connect
      
an_connectRigVis()         -  criete attr 'rigVis' , and connect all obj.v in objList
an_connectReversAttr()     -  connect Attributes via revers node
an_connectByMultiplier ()  - connect Attributes via multiplier node
an_connectAttrToAttrList(obgAttr, inAttrs)   - connectAttrToAttrList('general_CT.s', 's')
an_madeInfoConnection ()   - add connection to get list controllers or joints list

"""


def an_connectRigVis(ctrlObject, objList):
    if not cmds.objExists(ctrlObject + '.rigVis'):  cmds.addAttr(ctrlObject, ln="rigVis", at="enum", en="off:on",
                                                                 keyable=True)
    for each in objList:
        if not cmds.connectionInfo(each + ".v", id=True) and not cmds.objExists(each + '.rigVis'):
            cmds.connectAttr(ctrlObject + '.rigVis', each + ".v")
        if cmds.objExists(each + '.rigVis'):
            cmds.connectAttr(ctrlObject + '.rigVis', each + '.rigVis')


def an_connectReversAttr(input, output):
    prefix = input.split('.')[0]
    revers = cmds.createNode('reverse', n=prefix + 'Revers')
    cmds.connectAttr(input, revers + ".inputX")
    cmds.connectAttr(revers + ".outputX", output)
    return revers


def an_connectByMultiplier(inputAttr, outputAttr, val):
    unConvers = cmds.createNode('unitConversion')
    cmds.setAttr(unConvers + ".conversionFactor", val)
    cmds.connectAttr(inputAttr, unConvers + '.input')
    cmds.connectAttr(unConvers + '.output', outputAttr)
    return unConvers


def an_connectAttrToAttrList(obgAttr, inAttrs):
    for each in sl:
        cmds.connectAttr(obgAttr, each + '.' + inAttrs)


def an_madeInfoConnection(storObject, dict):  # add connection to get list controllers or joints list
    if cmds.objExists(storObject + '.' + dict.keys()[0]): cmds.deleteAttr(
        storObject + '.' + dict.keys()[0])  # if attr Exists - create it
    cmds.addAttr(storObject, ln=dict.keys()[0], at="message", multi=True, keyable=False)
    for i, ct in enumerate(dict[dict.keys()[0]]):
        cmds.connectAttr(ct + '.message', storObject + '.' + dict.keys()[0] + '[' + str(i) + ']')
