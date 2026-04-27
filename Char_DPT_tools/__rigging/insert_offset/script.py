# -*- coding: utf-8 -*-
# Maya Python 2.7 compatible

import maya.cmds as cmds


class InsertOffsetTool(object):

    WINDOW = "InsertOffsetWin"

    NODE_CONFIG = {
        "plusMinusAverage": {
            "type": "plusMinusAverage",
            "in": ".input1D[0]",
            "out": ".output1D",
            "offset": ".input1D[1]",
        },
        "multiplyDivide": {
            "type": "multiplyDivide",
            "in": ".input1X",
            "out": ".outputX",
            "offset": ".input2X",
        },
        "reverse": {
            "type": "reverse",
            "in": ".inputX",
            "out": ".outputX",
            "offset": None,
        },
    }

    # ---------------- UI ---------------- #

    @classmethod
    def show_ui(cls):
        if cmds.window(cls.WINDOW, exists=True):
            cmds.deleteUI(cls.WINDOW)

        cmds.window(cls.WINDOW, title="Insert Offset v3.0", sizeable=False, wh=[435, 60])
        cmds.columnLayout(adj=True)

        cmds.radioButtonGrp(
            "io_position",
            label="Insert position:",
            labelArray2=["Before", "After"],
            numberOfRadioButtons=2,
            select=1,
        )

        cmds.radioButtonGrp(
            "io_operation",
            label="Operation:",
            labelArray3=cls.NODE_CONFIG.keys(),
            numberOfRadioButtons=3,
            select=1,
        )

        # Кнопки во всю ширину
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 225), (2, 225)])

        cmds.button(
            label="Delete connection",
            command=lambda *_: cls.delete_offset()
        )
        cmds.button(
            label="Make connection",
            command=lambda *_: cls.make_offset()
        )

        cmds.setParent("..")
        cmds.showWindow(cls.WINDOW)

    # ---------------- Helpers ---------------- #

    @staticmethod
    def _get_selected_plug():
        sel = cmds.ls(selection=True)
        if len(sel) != 1:
            cmds.error("Select exactly ONE object.")

        attrs = cmds.channelBox("mainChannelBox", q=True, selectedMainAttributes=True) or \
                cmds.channelBox("mainChannelBox", q=True, selectedHistoryAttributes=True)

        if not attrs or len(attrs) != 1:
            cmds.error("Select exactly ONE channel in Channel Box.")

        return "%s.%s" % (sel[0], attrs[0])

    @staticmethod
    def _incoming_connections(plug):
        conns = cmds.listConnections(
            plug, plugs=True, connections=True,
            source=True, destination=False
        ) or []
        return zip(conns[::2], conns[1::2])  # (src, dst)

    @staticmethod
    def _outgoing_connections(plug):
        conns = cmds.listConnections(
            plug, plugs=True, connections=True,
            source=False, destination=True
        ) or []
        return zip(conns[::2], conns[1::2])  # (src, dst)

    # ---------------- Core Logic ---------------- #

    @classmethod
    def make_offset(cls):
        plug = cls._get_selected_plug()

        position = cmds.radioButtonGrp("io_position", q=True, select=True)
        op_index = cmds.radioButtonGrp("io_operation", q=True, select=True)
        op_name = cls.NODE_CONFIG.keys()[op_index - 1]
        config = cls.NODE_CONFIG[op_name]

        if position == 1:  # BEFORE
            connections = cls._incoming_connections(plug)
            if not connections:
                cmds.error("No incoming connection to insert BEFORE.")
            source_plug = connections[0][0]
            dest_plugs = [plug]
        else:  # AFTER
            connections = cls._outgoing_connections(plug)
            if not connections:
                cmds.error("No outgoing connection to insert AFTER.")
            source_plug = plug
            dest_plugs = [dst for _, dst in connections]

        node_name = plug.split(".")[0] + "_offset"
        node = cmds.createNode(config["type"], name=node_name)

        cmds.connectAttr(source_plug, node + config["in"], force=True)

        for dst in dest_plugs:
            cmds.connectAttr(node + config["out"], dst, force=True)

        # Create offset attribute if needed
        if config["offset"]:
            obj, attr = plug.split(".")
            attr_name = attr + "Offset"

            if not cmds.attributeQuery(attr_name, node=obj, exists=True):
                cmds.addAttr(obj, ln=attr_name, keyable=True)

            cmds.connectAttr(
                "%s.%s" % (obj, attr_name),
                node + config["offset"],
                force=True,
            )

        print "%s inserted successfully." % config['type']

    @classmethod
    def delete_offset(cls):
        plug = cls._get_selected_plug()
        position = cmds.radioButtonGrp("io_position", q=True, select=True)

        if position == 1:
            conns = cls._incoming_connections(plug)
        else:
            conns = cls._outgoing_connections(plug)

        if not conns:
            cmds.error("No inserted node found.")

        node = conns[0][0].split(".")[0]

        node_conns = cmds.listConnections(node, plugs=True, connections=True) or []
        pairs = zip(node_conns[::2], node_conns[1::2])

        inputs = [src for src, dst in pairs if dst.startswith(node)]
        outputs = [dst for src, dst in pairs if src.startswith(node)]

        if inputs and outputs:
            for out in outputs:
                cmds.connectAttr(inputs[0], out, force=True)

        obj, attr = plug.split(".")
        attr_name = attr + "Offset"

        if cmds.attributeQuery(attr_name, node=obj, exists=True):
            cmds.deleteAttr("%s.%s" % (obj, attr_name))

        cmds.delete(node)
        print "Offset node deleted."


InsertOffsetTool.show_ui()