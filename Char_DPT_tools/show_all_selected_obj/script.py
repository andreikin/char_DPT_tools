import os
import sys
import maya.cmds as cmds
import maya.mel as mel


def an_showAllSelectedObj():
    import maya.cmds as cmds
    import maya.mel as mel

    # Warning dialog
    result = cmds.confirmDialog(
        title='Warning',
        message=(
            'This operation may BREAK visibility connections on objects.\n\n'
            'It is STRONGLY recommended to SAVE the scene before continuing.\n\n'
            'Continue?'),
        button=['Continue', 'Cancel'],
        defaultButton='Cancel',
        cancelButton='Cancel',
        dismissString='Cancel',
        icon='warning')
    if result != 'Continue':
        return

    mel.eval('SelectHierarchy')

    for vObj in cmds.ls(sl=True):
        try:
            if cmds.objExists(vObj + '.tx'):
                showTransAttrs(vObj)
                cmds.setAttr(vObj + '.v', lock=False)

                if cmds.connectionInfo(vObj + '.v', isDestination=True):
                    source = cmds.connectionInfo(vObj + '.v', sourceFromDestination=True)
                    cmds.disconnectAttr(source, vObj + '.v')

                cmds.setAttr(vObj + '.v', 1)
                cmds.setAttr(vObj + '.overrideVisibility', 1)

            if cmds.nodeType(vObj) == u'joint':
                cmds.setAttr(vObj + '.drawStyle', 0)

        except Exception:
            pass
    cmds.select(cl=True)



def showTransAttrs(name):
    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
        cmds.setAttr(name + "." + attr, lock=False, keyable=True)


an_showAllSelectedObj()
