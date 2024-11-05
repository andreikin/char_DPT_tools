#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import re
import shutil
import subprocess
import sys
from pprint import pprint

import maya.cmds as cmds

SHELF_NAME = "Char_DPT_tools"
TOOLS_FOLDER_NAME = "tools"
DATA_FILE_NAME = 'data.json'
ICON_FILE_NAME = 'icon.png'


def onMayaDroppedPythonFile(obj):
    for i in range(3):
        print('\n')

    maya_version = cmds.about(version=True)
    pattern_shelves = r'.+' + maya_version + '/prefs/shelves'
    shelves_path = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_shelves, x)][0]

    pattern_scripts = r'.+' + maya_version + '/prefs/scripts'
    scripts_path = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_scripts, x)][0]

    pattern_icons = r'.+' + maya_version + '/prefs/icons'
    icon_path = [x for x in os.environ['XBMLANGPATH'].split(';') if re.match(pattern_icons, x)][0]

    distrib_path = os.path.dirname(__file__)

    # Проверяем и создаем новую полку
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME, layout=True)

    cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")
    cmds.shelfTabLayout("ShelfLayout", edit=True, selectTab=SHELF_NAME)

    tools_folders = os.listdir(os.path.join(distrib_path, TOOLS_FOLDER_NAME))

    for tool_folder in tools_folders:
        tool_path = os.path.join(distrib_path, TOOLS_FOLDER_NAME, tool_folder)

        add_buttons(tool_folder_path=tool_path, icon_path=icon_path)


def add_buttons(tool_folder_path=None, scripts_path=None, icon_path=None):
    with open(os.path.join(tool_folder_path, DATA_FILE_NAME), 'r') as file:
        json_data = json.load(file)

    data = {'parent': SHELF_NAME, 'overlayLabelColor': [1, 1, 1], 'overlayLabelBackColor': [0, 0, 0, 1]}
    for k, v in json_data.items():
        data[k.encode('utf-8')] = v.encode('utf-8')

    # add icon
    source_icon_file = os.path.join(tool_folder_path, ICON_FILE_NAME)
    if os.path.exists(source_icon_file):
        dest_icon_name = os.path.basename(tool_folder_path)+".png"
        dest_icon_path = os.path.join(icon_path, dest_icon_name)
        shutil.copy2(source_icon_file, dest_icon_path)
        data["image"] = dest_icon_path

    cmds.shelfButton(**data)


