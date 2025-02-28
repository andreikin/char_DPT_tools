#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import re
import shutil
import maya.cmds as cmds

SHELF_NAME = "Char_DPT_tools"
COMMAND_FILE_NAME = 'command'
TOOLS_FOLDER_NAME = "tools"
DATA_FILE_NAME = 'data.json'
ICON_FILE_NAME = 'icon.png'
SCRIPT_FILE_NAME = 'script.py'
ITEMS_FOLDER_NAME = 'menu_items'


def onMayaDroppedPythonFile(obj):
    """
    Function launched when a file is dropped into the Maya program
    """
    install_Char_DPT_tools()


def install_Char_DPT_tools(distrib_path=None):
    """
    Creates shelves and buttons
    """
    # ----------------------- get maya paths
    if not distrib_path:
        distrib_path = os.path.dirname(__file__)
    maya_version = cmds.about(version=True)
    pattern_shelves = r'.+' + maya_version + '/prefs/shelves'
    shelves_path = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_shelves, x)][0]

    pattern_scripts = r'.+' + maya_version + '/prefs/scripts'
    scripts_path = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_scripts, x)][0]

    pattern_icons = r'.+' + maya_version + '/prefs/icons'
    icon_path = [x for x in os.environ['XBMLANGPATH'].split(';') if re.match(pattern_icons, x)][0]

    # ----------------------- remove old version if exists and create new one
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME, layout=True)

    cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")
    cmds.shelfTabLayout("ShelfLayout", edit=True, selectTab=SHELF_NAME)

    # ----------------------- get tools folders list and create buttons
    tools_folders = os.listdir(os.path.join(distrib_path, TOOLS_FOLDER_NAME))
    for tool_folder in tools_folders:
        tool_path = os.path.join(distrib_path, TOOLS_FOLDER_NAME, tool_folder)
        add_buttons(tool_folder_path=tool_path, scripts_path = scripts_path, icon_path=icon_path)


def add_buttons(tool_folder_path=None, scripts_path=None, icon_path=None):
    pass
    """
        Description of the json file with button creation settings:
            "label": label for label display mode
            "imageOverlayLabel": over button text
            "command": command that runs the code (if there is a file 'command.py', it is loaded)
            "annotation": "pop-up text with annotation",
            "image": icon type (if there is a file 'icon.png', it is loaded)
            "sourceType": "python",
            "scripts_list":  list of scripts that need to be copied to the Maya scripts folder 
    """

    if tool_folder_path[-9:] == 'separator':
        cmds.separator(parent=SHELF_NAME, style="shelf",  highlightColor=[0.321569, 0.521569, 0.65098], height=20)
        return

    #  -----------------------  Data verification
    json_file = os.path.join(tool_folder_path, DATA_FILE_NAME)
    if not os.path.exists(json_file):
        return

    #  -----------------------  Loading button settings from json file
    with open(json_file, 'r') as file:
        json_data = json.load(file)

    #  -----------------------  Copy the script files to the appropriate folder
    scripts_list = json_data.pop('scripts_list') if json_data.get('scripts_list') else []
    for script in scripts_list:
        source_script_file = os.path.join(tool_folder_path, script)
        if os.path.exists(source_script_file):
            dest_script_path = os.path.join(scripts_path, script)
            shutil.copy2(source_script_file, dest_script_path)

    #   -----------------------  Create general settings for the button
    data = {'parent': SHELF_NAME, 'overlayLabelColor': [1, 1, 1], 'overlayLabelBackColor': [0.268, 0.268, 0.268, 1]}

    for k, v in json_data.items():
        val = v.encode('utf-8') if isinstance(v, str) else v
        data[k.encode('utf-8')] = val

    #  -----------------------  add command
    for ext in ('.py', '.mel'):
        command_file = os.path.join(tool_folder_path, COMMAND_FILE_NAME + ext)
        if os.path.exists(command_file):
            with open(command_file, 'r') as file:
                data['command'] = file.read()
                continue

    #  -----------------------  add menu items
    items_folder = os.path.join(tool_folder_path, ITEMS_FOLDER_NAME)
    if os.path.exists(items_folder):
        data['menuItem'] = list()
        data['menuItemPython'] = list()
        for i, item in enumerate(os.listdir(items_folder)):
            item_file = os.path.join(tool_folder_path,  ITEMS_FOLDER_NAME, item)
            name, ext = item.split('.')
            with open(item_file, 'r') as f:
                cod = f.read()
            data['menuItem'].append([name, cod])
            if ext == 'py':
                data['menuItemPython'].append(i)

    #  -----------------------  add icon
    source_icon_file = os.path.join(tool_folder_path, ICON_FILE_NAME)
    if os.path.exists(source_icon_file):
        dest_icon_name = os.path.basename(tool_folder_path)+".png"
        dest_icon_path = os.path.join(icon_path, dest_icon_name)
        shutil.copy2(source_icon_file, dest_icon_path)
        data["image"] = dest_icon_path

    #  -----------------------  add button
    cmds.shelfButton(**data)



if __name__ == '__main__':
    # scripts_path = 'C:\\Users\\avbeliaev\\Documents\\maya\\2019\\scripts'
    # icon_path = "C:\\Users\\avbeliaev\\Documents\\maya\\2019\\prefs\\icons"
    # tool_folder_path = 'D:\\Projects\\Python\\char_dpt_tools\\tools\\099_separator'
    # add_buttons(tool_folder_path, scripts_path, icon_path)
    install_Char_DPT_tools()