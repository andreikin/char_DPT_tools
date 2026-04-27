"""
Main Procedure:
    an_insertOffset()

Creation Date:
    January 22, 2014

Authors:
    Belyaev Andrey
    andreikin@mail.ru
    www.3drigging.com

Description:
    The script allows you to insert at the input or output of the selected attribute
    in the channel box, one of the nodes: 'plusMinusAverage', 'multiplyDivide' or 'reverse'.
    Selected channel must have appropriate connection.

Installation:

    1. Copy the [an_insertOffset] to your local user/scripts folder
		 		example: ..\my documents\maya\scripts\
	2. Start Maya
	4. Type:    import an_insertOffset
                from an_insertOffset import *
	   into the Maya Script Editor (Pithon mod), and hit enter.

How to Use:
    1. Select one channel in the channel box
	2. Select the node type and its insert position
	3. Press "make connection"
	4. To delete nod - Select its insert position, select the same attribut in the channel box and press "delete connection"

Notes:
    **** When you choose "reverse" node, "Offset" attribute is not created.
    **** Be careful when working with rotation attributes (because the Maya inserts "unitConversion" nodes automatically)

Comments or suggestions? E-mail me!!!
Good luck!!!


*************************************************************************************************************************
 version History
*************************************************************************************************************************
	v2.0
	- Add script description.
	- Add opportunity to insert a "Revers" node.
	- Add comments in the code.

*************************************************************************************************************************
 Modify at your own risk
"""

from maya.cmds import *
import maya.cmds as cmds


def an_insertOffset():  # user interface
    vWin = "an_insertOffsetWin"
    if window(vWin, exists=True):
        deleteUI(vWin, window=True)
    window(vWin, t="Insert Offset  v 2.00", menuBar=True, sizeable=False, wh=[432, 99])
    menu(label="Help")
    menuItem(label='About script', c='an_help("open")')
    columnLayout()
    separator(h=2)
    frameLayout(label='Additional tools:', lv=False)
    radioButtonGrp("PosRBG", label='Insert position:    ', labelArray2=['before', 'after'], numberOfRadioButtons=2,
                   sl=1)
    radioButtonGrp("OperRBG", label='Operation:    ', labelArray3=['plusMinusAverage', 'multiplyDivide', 'revers'],
                   numberOfRadioButtons=3, sl=1)
    setParent('..')
    rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 213), (2, 214)])
    button(label='delete connection', command='an_delOffset()')
    button(label='make connection', command="an_makeInsertOffset()")
    setParent('..')
    separator(h=5)
    text("   The script allows you to insert at the input or output of the selected attribute")
    text("   in the channel box, one of the nodes: 'plusMinusAverage', 'multiplyDivide' or 'reverse'. ")
    text("   Selected channel must have appropriate connection")
    rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 350), (2, 50)])
    text("                www.3drigging.com   Belyaev Andrey")
    button(label='Close', w=50, c='an_help("v_action")')
    showWindow(vWin)




def an_delOffset():  # procedure delete inserted node
    if not ls(sl=True): cmds.error(" Please select one object and one channel!")
    vObj = ls(sl=True)[0]
    vAttr = channelBox('mainChannelBox', q=True, selectedMainAttributes=True)[0]  # get selected attribut in channelBox
    if not vAttr: vAttr = channelBox("mainChannelBox", q=True, selectedHistoryAttributes=True)[0]
    if radioButtonGrp("PosRBG", q=True, sl=True) == 1:
        v_Node = connectionInfo(vObj + '.' + vAttr, sourceFromDestination=True).split('.')[0]
    else:
        v_Node = connectionInfo(vObj + '.' + vAttr, destinationFromSource=True)[0].split('.')[0]  # get nod name
    v_usedAttr = []
    if nodeType(v_Node) == 'plusMinusAverage': v_usedAttr = ['.input1D[0]', '.output1D']  # get nod attributes
    if nodeType(v_Node) == 'multiplyDivide': v_usedAttr = ['.input1X', '.outputX']
    if nodeType(v_Node) == 'reverse': v_usedAttr = ['.inputX', '.outputX']
    vStartAttr = connectionInfo(v_Node + v_usedAttr[0], sourceFromDestination=True)  # get attributes destination
    vEndAttr = connectionInfo(v_Node + v_usedAttr[1], destinationFromSource=True)
    for v_eachAttr in vEndAttr:
        connectAttr(vStartAttr, v_eachAttr, force=True)  # connect attributes
    if not nodeType(v_Node) == 'reverse': deleteAttr(vObj + '.' + vAttr + 'Offset')
    delete(v_Node)  # delete node


def an_makeInsertOffset():
    if not len(ls(sl=True)) == 1: cmds.error(" Please select one object and one channel!")
    vObj = ls(sl=True)[0]
    vAttr = channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    if not vAttr: vAttr = channelBox("mainChannelBox", q=True,
                                     selectedHistoryAttributes=True)  # get selected attribut in channelBox
    if not len(vAttr) == 1: cmds.error("  Please select one channel!")

    v_operation = radioButtonGrp("OperRBG", q=True, sl=True)  # getting the operation value
    if radioButtonGrp("PosRBG", q=True, sl=True) == 1:
        v_Connection = [connectionInfo(vObj + '.' + vAttr[0], sourceFromDestination=True),
                        vObj + '.' + vAttr[0]]  # getting incoming connection
        if not v_Connection[0]: error("No incoming connection!")
    else:
        v_Connection = [vObj + '.' + vAttr[0]] + connectionInfo(vObj + '.' + vAttr[0],
                                                                destinationFromSource=True)  # or getting outgoing connection
        if len(v_Connection) < 2: error("No outgoing connection!")
    v_retCon = []
    if v_operation == 1:  # insert the appropriate node
        v_retCon = an_doInsertOffset(v_Connection, 'add')
        print "Node 'plusMinusAverage' successfully inserted"
    if v_operation == 2:
        v_retCon = an_doInsertOffset(v_Connection, 'multiply')
        print "Node 'multiplyDivide' successfully inserted"
    if v_operation == 3:
        an_doInsertOffset(v_Connection, 'revers')
        print "Node 'reverse' successfully inserted"
    if not v_operation == 3:  # connecting attribute 'Offset' to node
        select(vObj)
        addAttr(ln=vAttr[0] + 'Offset', keyable=True)
        connectAttr(vObj + '.' + vAttr[0] + 'Offset', v_retCon, force=True)


def an_doInsertOffset(v_Connection, v_type):  # between v_Connection[0] and v_Connection[n]
    v_name = v_Connection[1].split('.')[0] if radioButtonGrp("PosRBG", q=True, sl=True) == 1 else \
    v_Connection[0].split('.')[0]
    if v_type == 'add':
        vPMA = createNode('plusMinusAverage', n=v_name + 'Ofs_PMA')
        connectAttr(v_Connection[0], vPMA + '.input1D[0]', force=True)
        for v_eachConect in v_Connection[1:]:  connectAttr(vPMA + '.output1D', v_eachConect, force=True)
        return vPMA + '.input1D[1]'
    if v_type == 'multiply':
        vPMA = createNode('multiplyDivide', n=v_name + 'Ofs_MDV')
        connectAttr(v_Connection[0], vPMA + '.input1X', force=True)
        for v_eachConect in v_Connection[1:]: connectAttr(vPMA + '.outputX', v_eachConect, force=True)
        return vPMA + '.input2X'
    if v_type == 'revers':
        vPMA = createNode('reverse', n=v_name + 'Ofs_Revers')
        connectAttr(v_Connection[0], vPMA + '.inputX', force=True)
        for v_eachConect in v_Connection[1:]:  connectAttr(vPMA + '.outputX', v_eachConect, force=True)
        return ''


def an_help(v_action):  # procedure shows or hides the description of the script
    if v_action == "open":
        window("an_insertOffsetWin", e=True, wh=[432, 175])
    else:
        window("an_insertOffsetWin", e=True, wh=[432, 99])


an_insertOffset()