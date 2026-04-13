#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import re
import shutil
import sys

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.mel as mel


DATA_FILE_NAME = 'data.json'
ICON_FILE_NAME = 'icon.png'
SCRIPT_FILE_NAME = 'script'
ITEMS_FOLDER_NAME = 'submenu items'
MODULES_FOLDER = 'module'


def onMayaDroppedPythonFile(obj):
    """
    Function launched when a file is dropped into the Maya program
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    add_button(tool_folder_path=script_dir,
               scripts_path=maya_paths()['scripts_path'],
               icon_path=maya_paths()['icon_path'])


def add_button(tool_folder_path=None, scripts_path=None, icon_path=None):
    """
        Description of the json file with button creation settings:
            "label": label button text
            "script": command that runs the code (if there is a file 'script.py', it is loaded)
            "annotation": "pop-up text with annotation",
    """
    #  -----------------------  Loading button settings from json file
    json_file = os.path.join(tool_folder_path, DATA_FILE_NAME)
    json_data = load_json_safe(json_file)

    #  -----------------------  Get modul name and script files to the appropriate folder
    module_folder = os.path.join(tool_folder_path, MODULES_FOLDER)
    if os.path.exists(module_folder) and os.listdir(module_folder):
        module_name = os.listdir(module_folder)[0]
        module_path = os.path.join(module_folder,  os.listdir(module_folder)[0])

        copy_folder(module_path, os.path.join(scripts_path, module_name))

    #   -----------------------  Create general settings for the button
    data = {'parent': get_current_shelf(),
            'overlayLabelColor': [1, 1, 1],
            'overlayLabelBackColor': [0.268, 0.268, 0.268, 1],
            "imageOverlayLabel": json_data.get("shelf_settings", {}).get("label", "")}
    data.update(json_data)

    #  -----------------------  add command
    for ext in ('.py', '.mel'):
        command_file = os.path.join(tool_folder_path, SCRIPT_FILE_NAME + ext)
        if os.path.exists(command_file):
            with open(command_file, 'r') as file:
                data['command'] = file.read()
                data["sourceType"] = "python" if ext == '.py' else "mel"
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
    else:
        data["image"] ='commandButton.png'

    # remove axillary keys
    for key in ("shelf_settings", "menu_settings"):
        if key in data:
            data.pop(key)

    #  -----------------------  add button
    data = convert_bytes_to_str(data) if sys.version[0] == '3' else data
    cmds.shelfButton(**data)
    script_name = os.path.basename(tool_folder_path).capitalize()
    om.MGlobal.displayInfo(script_name + " successfully installed to shelf!")


def convert_bytes_to_str(data):
    result = {}
    for key, value in data.items():
        key = key.decode('utf-8', errors='ignore') if isinstance(key, bytes) else key
        result[key] = value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else value
    return result


def copy_folder(src, dst):

    if not os.path.exists(dst):
        os.makedirs(dst)

    for root, dirs, files in os.walk(src):

        rel_path = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel_path)

        if not os.path.exists(target_root):
            os.makedirs(target_root)

        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(target_root, f)

            shutil.copy2(src_file, dst_file)


def load_json_safe(path):
    """
    Decoding Russian text in a json file
    """
    if sys.version[0] == '3':
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except UnicodeDecodeError:
            with open(path, 'r', encoding='cp1251') as f:
                return json.load(f)
    else:
        with open(path, 'r') as f:
            json_data = json.load(f)
            out = dict()
            for k, v in json_data.items():
                val = v.encode('utf-8') if isinstance(v, str) else v
                out[k.encode('utf-8')] = val
            return out


def get_current_shelf():
    """
    Returns the name of the currently active shelf in Maya.
    """
    shelf_top_level = mel.eval('$tmp = $gShelfTopLevel')
    current_shelf = cmds.shelfTabLayout(shelf_top_level, q=True, selectTab=True)
    return current_shelf


def maya_paths():
    paths = dict()
    maya_version = cmds.about(version=True)

    pattern_scripts = r'.+' + maya_version + '/prefs/scripts'
    paths['scripts_path'] = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_scripts, x)][0]

    pattern_icons = r'.+' + maya_version + '/prefs/icons'
    paths['icon_path'] = [x for x in os.environ['XBMLANGPATH'].split(';') if re.match(pattern_icons, x)][0]
    return paths


