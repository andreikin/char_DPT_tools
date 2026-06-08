
"""
Main Procedure:
    an_mixTwoAttr()

Creation Date:
    March 24, 2014

Authors:
    Belyaev Andrey
    andreikin@mail.ru
    www.3drigging.com

Description:
    The script creates a node "blendTwoAttr", and connect attributes to input channels , and attribute "attributesBlender".

Installation:

    1. Copy the [an_mixTwoAttr] to your local user/scripts folder
		 		example: ..\my documents\maya\scripts\
	2. Start Maya
	4. Type:    import an_insertOffset
                from an_mixTwoAttr import *
	   into the Maya Script Editor (Pithon mod), and hit enter.

Comments or suggestions? E-mail me!!!
Good luck!!!

*************************************************************************************************************************
 version History
*************************************************************************************************************************
	v2.0
	- Add script description.
	- Add ability to work with Python scripts
	- Add comments in the code.

*************************************************************************************************************************
 Modify at your own risk
"""

import maya.cmds as cmds


def mix_two_attr():
    win = "an_mixTwoAttr"
    if  cmds.window (win, exists=True ): cmds.deleteUI (win)
    cmds.window (win, t="Attribut mix system.v02", rtf=True ,menuBar=True )
    cmds.menu (label="Edit" )
    cmds.menu (label="Help" )
    vCLayout =cmds.columnLayout()
    for vFild, vI in zip (["Input A:  ", "Input B:  ", "output Attr:  ", "mix Attr:  "], range(0,4)):
         vRCLayout = cmds.rowColumnLayout ( numberOfColumns=4, columnWidth=[(1, 80), (2, 180), (3, 90), (4, 90)])
         cmds.text (l=vFild, align="right")
         cmds.textField ("mixTF"+str(vI))
         cmds.button (label='<- add to field', c="an_adAttrAndChangField(\"mixTF"+str(vI)+"\", \"-field\" )" )
         cmds.button (label='add to object ->', c= "an_adAttrAndChangField(\"mixTF"+str(vI)+"\", \"-addAttr\" )")
         cmds.setParent( '..')
    cmds.separator(h=3)
    cmds.rowColumnLayout ( numberOfColumns=3, columnWidth=[(1, 80), (2, 180  ), (3, 180)])
    cmds.text (l="", align="right")
    cmds.button (label="Connect A to B", c= "cmds.connectAttr(  cmds.textField (\"mixTF0\", q=1, text=1),  cmds.textField (\"mixTF1\", q=1, text=1))" )
    cmds.button (label="Blend A and B", c= "an_connect()")
    cmds.showWindow (win)


def an_adAttrAndChangField( vField, vAct ):
    if (vAct == "-field"):
        vText = an_returnSelObjAndAttr()
        cmds.textField (vField, e=True, tx= vText)
    if (vAct == "-addAttr"):
        vAttr = cmds.textField (vField, q=1, text=1)
        if   len(vAttr)== 0  : cmds.error ( "Please input attribute!")
        obj = cmds.ls (sl=True)
        if   len(obj)== 0  : cmds.error ( "Please select objekt!")
        cmds.addAttr( ln = vAttr, k=1 )
        cmds.textField (vField, e=True, text= obj[0]+"."+vAttr)


def an_returnSelObjAndAttr():
    if not  cmds.ls (sl=True) : cmds.error (" Please select one object and one channel!")
    vObj = cmds.ls (sl=True ) [0]
    vAttr, v_out =[],[]
    try: vAttr = cmds.channelBox  ('mainChannelBox', q = True, selectedMainAttributes = True )
    except TypeError: pass
    if not vAttr:
        try:vAttr =  cmds.channelBox ("mainChannelBox", q=True,  selectedHistoryAttributes=True )   # get selected attribut in channelBox
        except TypeError: pass
    if not  vAttr : cmds.error ("  Please select one channel!")
    for v_eachAttr in vAttr: v_out.append(vObj+'.'+v_eachAttr)
    return  v_out[0]

def an_getFildVal(vField):
    vField=cmds.textField (vField, q=1, text=1)
    try:
        vField = float(vField)
        return vField, "float"
    except ValueError:
        return vField, "string"

def an_connect():
    an_mixTwoAttrUiTest()
    vFildA  = an_getFildVal("mixTF0")
    vFildB  = an_getFildVal("mixTF1")
    vFildOut= an_getFildVal("mixTF2")[0]
    vFildMix= an_getFildVal("mixTF3")[0]

    v_Prefix = vFildOut.split('.')[0]
    vPMA = cmds.createNode ('blendTwoAttr', n = v_Prefix+'_PMA')
    cmds.connectAttr (vPMA+'.output', vFildOut)
    cmds.connectAttr (vFildMix, vPMA+'.attributesBlender')
    if vFildA[1]== 'string': cmds.connectAttr (vFildA[0], vPMA+".input[0]")
    else: cmds.setAttr( vPMA+".input[0]", vFildA[0] )
    if vFildB[1]== 'string': cmds.connectAttr (vFildB[0], vPMA+".input[1]")
    else: cmds.setAttr( vPMA+".input[1]", vFildB[0] )

def an_mixTwoAttrUiTest():
    for vFild, vI in zip (["Input A:  ", "Input B:  ", "output Attr:  ", "mix Attr:  "], range(0,4)):
        data = cmds.textField ("mixTF"+str(vI), q=True, text = True)
        if not data:
            cmds.error ( "Please fill the fields!")


mix_two_attr()
