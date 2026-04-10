#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main Procedure:
    onMayaDroppedPythonFile()

Creation Date:
    10.04.2026

Authors:
    Belyaev Andrey
    andreikin@mail.ru

Description:
        This file is a universal installer and launcher for the Char_DPT_tools
    toolset inside Autodesk Maya.

    It provides a framework that allows artists and TDs to organize tools
    in simple folder structures and automatically expose them as:

        • Maya main menu items
        • Maya shelf buttons
        • Optional shelf popup menus
        • Automatic startup menu loading

Installation:
        There is no manual setup required.

    To install, rename file to menu_installer.py, shelf_installer.py or button_installer.py and
    simply drag and drop one of the installer files into Maya:

        1. menu_installer.py
           → Installs the "Char_DPT_tools" menu in Maya.

        2. shelf_installer.py
           → Creates the "Char_DPT_shelf" shelf with tool buttons.

        3. button_installer.py
           → Creates a single shelf button for this tool only.

    During installation the script will:
        • Copy launcher.py into Maya user scripts directory
        • Add menu creation command into userSetup.py
        • Ask for the root folder where tools are stored
        • Build the menu/shelf automatically

    After installation, Maya will recreate the menu automatically
    on every startup.
"""

import sys
sys.dont_write_bytecode = True

from contextlib import contextmanager
import os
import re
import shutil
import json
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QSettings

INSTALLER_VERSION = '1.0.0'
MENU = 'script_manager_menu'
MENU_LABEL = 'Char_DPT_tools'
SHELF_NAME = "Char_DPT_shelf"


class ScriptLauncher:
    """
      Responsible for launching Maya tools located in a tool folder.
      This class:
          1. Adds the module path temporarily to sys.path (if exists)
          2. Executes Python or MEL script
          3. Tracks tool usage statistics in a JSON file
          4. Can copy itself into Maya scripts directory for global access
      """
    SCRIPT_PY_NAME = 'script.py'
    SCRIPT_MEL_NAME = 'script.mel'
    MODULES_FOLDER = 'module'

    def __init__(self, stats_json_path="U:\CharDptRepository\char_dpt_tools\scripts_stats.json"):
        self.stats_json_path = stats_json_path

    @contextmanager
    def temp_sys_path(self, path):
        """
        Context manager that temporarily inserts a path into sys.path.
        """
        if path not in sys.path:
            sys.path.insert(0, path)
            added = True
        else:
            added = False
        try:
            yield
        finally:
            if added:
                sys.path.remove(path)

    def run_python(self, py_path, module_path=None):
        """
        Executes a Python script in an isolated global context.
        """
        if os.path.exists(py_path):
            globals_dict = {"__file__": py_path, "__name__": "__main__"}
            if module_path:
                with self.temp_sys_path(module_path):
                    exec (compile(open(py_path, "rb").read(), py_path, 'exec'), globals_dict)
            else:
                exec (compile(open(py_path, "rb").read(), py_path, 'exec'), globals_dict)

    def run_mel(self, script_path):
        """
        Executes a MEL script inside Maya.
        """
        if os.path.exists(script_path):
            with open(script_path, 'r') as f:
                mel_code = f.read()
            mel.eval(mel_code)

    def launch(self, tool_folder_path):
        """
        Main entry point for launching a tool. Also increments execution statistics.
        """
        try:
            module_folder = os.path.join(tool_folder_path, 'module')
            module_path = None

            if os.path.exists(module_folder) and os.listdir(module_folder):
                module_path = os.path.join(module_folder, os.listdir(module_folder)[0])

            py_path = os.path.join(tool_folder_path, 'script.py')
            mel_path = os.path.join(tool_folder_path, 'script.mel')

            self.increment_script_counter(os.path.basename(tool_folder_path))

            if os.path.exists(py_path):
                self.run_python(py_path, module_path)
                return
            elif os.path.exists(mel_path):
                self.run_mel(mel_path)

        except Exception as message:
            om.MGlobal.displayError(message)

    def increment_script_counter(self, script_name):
        """
        Increments launch counter for a tool in the statistics JSON file.
        """
        try:
            if not os.path.exists(self.stats_json_path):
                data = {}
            else:
                with open(self.stats_json_path, "r") as f:

                    try:
                        data = json.load(f)
                    except:
                        data = {}

            if script_name in data:
                data[script_name] += 1
            else:
                data[script_name] = 1

            with open(self.stats_json_path, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            om.MGlobal.displayInfo('The ' + script_name + ' script was successfully executed.')

        except Exception as message:
            om.MGlobal.displayError(message)

    @staticmethod
    def copy_launcher():
        """
        Copies this launcher file into Maya's user scripts directory
        """
        srs = __file__
        dst = os.path.join(maya_paths()['scripts_path'], 'launcher.py')
        shutil.copy(srs, dst)


class ToolDataAssembler:
    """
    This class reads the folder content and converts it into
    dictionaries suitable for cmds.menuItem and cmds.shelfButton.
    """
    ICON_FILE_NAME = 'icon.png'
    SCRIPT_FILE_NAME = 'script.py'
    DATA_FILE_NAME = 'data.json'
    ITEMS_FOLDER_NAME = 'menu_items'

    def __init__(self, tool_folder_path):
        self.tool_folder_path = tool_folder_path
        self.label = os.path.basename(tool_folder_path)
        self.image = self.get_icon()
        self.json_path = os.path.join(self.tool_folder_path, self.DATA_FILE_NAME)

        json_data = self.load_json()
        self.annotation = json_data.get('annotation', self.label)
        self.shelf_label = json_data.get('shelf_label', self.label)
        self.hotkey = json_data.get('hotkey')

    @staticmethod
    def hotkey_command(tool_folder_path):
        """Builds a MEL command string that executes with hotkey."""
        python_code = 'from launcher import * ; ScriptLauncher().launch("' + tool_folder_path + '")'
        python_code_escaped = python_code.replace('\\', '\\\\').replace('"', '\\"')
        mel_command = 'python("' + python_code_escaped + '")'
        return mel_command

    def add_hotkey(self):
        """
        Creates a Maya hotkey for the tool based on data from data.json.
        """
        if not self.hotkey or not self.hotkey.get("key"):
            return

        name = self.label + 'hotkey'
        command_string = self.hotkey_command(self.tool_folder_path)
        cmds.nameCommand(name, annotation=self.annotation, command=command_string)

        # --- Hotkey ---
        cmds.hotkey(
            keyShortcut=self.hotkey.get('key'),
            ctrlModifier=self.hotkey.get('ctl'),
            shiftModifier=self.hotkey.get('shif'),
            altModifier=self.hotkey.get('alt'),
            name=name
        )
        om.MGlobal.displayInfo('The ' + self.label + ' hotkey added successful.')

    @property
    def item_data(self):
        self.add_hotkey()
        """
        Generates a dictionary used to create a Maya menu item.
        """
        data = {'label': self.label,
                'command': ToolDataAssembler.__menu_command(ScriptLauncher().launch, self.tool_folder_path),
                'sourceType': 'python',
                'annotation': self.annotation,
                'image': self.image
                }
        data = self.__convert_bytes_to_str(data) if sys.version[0] == '3' else data
        return data

    @property
    def button_data(self):
        """
        Generates a dictionary used to create a Maya shelf button.
        """
        self.add_hotkey()

        data = {'parent': self.__get_current_shelf(),
                'overlayLabelColor': [1, 1, 1],
                'overlayLabelBackColor': [0.268, 0.268, 0.268, 0.8],
                'imageOverlayLabel': self.shelf_label,
                'command': self.command(self.tool_folder_path),
                'sourceType': 'python',
                'annotation': self.annotation,
                'image': self.image
                }

        menu_item, menu_item_python = self.btn_menu()
        if menu_item:
            data['menuItem'] = menu_item
            data['menuItemPython'] = menu_item_python

        data = self.__convert_bytes_to_str(data) if sys.version[0] == '3' else data
        return data

    def btn_menu(self):
        """
        Builds submenu data for a shelf button from 'menu_items' folder.
        """
        menu_item = list()
        menu_item_python = list()

        items_folder = os.path.join(self.tool_folder_path, self.ITEMS_FOLDER_NAME)

        if os.path.exists(items_folder):
            for i, item in enumerate(os.listdir(items_folder)):
                item_file = os.path.join(self.tool_folder_path, self.ITEMS_FOLDER_NAME, item)
                menu_item.append([item, self.command(item_file)])
                menu_item_python.append(i)
        return menu_item, menu_item_python

    @staticmethod
    def command(tool_folder_path):
        """
        Builds a Python command string executed by Maya UI elements.
        """
        command = 'from launcher import *\n'
        command += ('tool_folder_path = r"' + tool_folder_path + '"\n')
        command += 'ScriptLauncher().launch(tool_folder_path)'
        return command

    def get_icon(self):
        """
        Returns path to tool icon if exists, otherwise default Maya icon.
        """
        icon_file = os.path.join(self.tool_folder_path, self.ICON_FILE_NAME)
        if os.path.exists(icon_file):
            return icon_file
        else:
            return 'commandButton.png'

    def load_json(self):
        """
        Decoding Russian text in a json file
        """
        if not os.path.exists(self.json_path):
            return dict()

        if sys.version[0] == '3':
            try:
                with open(self.json_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except UnicodeDecodeError:
                with open(self.json_path, 'r', encoding='cp1251') as f:
                    return json.load(f)
        else:
            with open(self.json_path, 'r') as f:
                json_data = json.load(f)
                out = dict()
                for k, v in json_data.items():
                    val = v.encode('utf-8') if isinstance(v, str) else v
                    out[k.encode('utf-8')] = val
                return out

    @staticmethod
    def __convert_bytes_to_str(data):
        result = {}
        for key, value in data.items():
            key = key.decode('utf-8', errors='ignore') if isinstance(key, bytes) else key
            result[key] = value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else value
        return result

    @staticmethod
    def __menu_command(func, *args, **kwargs):
        """
        Creates unique callback functions for menu items created in loops.
        """

        def _callback(*_):
            return func(*args, **kwargs)

        return _callback

    @staticmethod
    def __get_current_shelf():
        """
        Detects the currently active Maya shelf.
        """
        shelf_top_level = mel.eval('$tmp = $gShelfTopLevel')
        current_shelf = cmds.shelfTabLayout(shelf_top_level, q=True, selectTab=True)
        return current_shelf


class ToolsStructure:
    """
    Scans the tools root directory and builds hierarchical structure
    for menu and shelf creation.
    """
    def __init__(self, tools_folder):
        self.tools_folder = tools_folder

    @staticmethod
    def is_tool(folder_path):
        """
        Determines whether a folder represents a valid tool.
        """
        if any([os.path.isfile(os.path.join(folder_path, "script.py")),
                os.path.isfile(os.path.join(folder_path, "script.mel")),
                os.path.isdir(os.path.join(folder_path, "menu_items"))]):
            return True
        else:
            return False

    def build_structure(self):
        """
        Builds dictionary describing tools grouped by subfolders.
        """
        tools_structure = dict()
        other_scripts = list()

        for submenu_folder in sorted(os.listdir(self.tools_folder)):
            submenu_path = os.path.join(self.tools_folder, submenu_folder)
            if os.path.isdir(submenu_path) and not self.is_tool(submenu_path):

                # we go through each folder
                tools_structure[submenu_folder] = []
                for script_folder in sorted(os.listdir(submenu_path)):
                    script_path = os.path.join(submenu_path, script_folder)
                    if os.path.isdir(script_path) and self.is_tool(script_path):
                        tools_structure[submenu_folder].append(os.path.normpath(script_path))

            if os.path.isdir(submenu_path) and self.is_tool(submenu_path):
                other_scripts.append(os.path.normpath(submenu_path))
        tools_structure['other_scripts'] = other_scripts

        return tools_structure


class CharDepTools:
    """
    High-level class responsible for creating Maya UI:
        - Main menu
        - Shelf
        - Shelf button
        - Managing user settings

    This is the class used during installation.
    """
    def __init__(self):
        pass

    @staticmethod
    def menu():
        """
        Creates or rebuilds the main Maya menu for all tools.
        """
        try:
            if cmds.menu(MENU, exists=True):
                cmds.deleteUI(MENU)

            menu = cmds.menu(
                MENU,
                label=MENU_LABEL,
                parent="MayaWindow",
                tearOff=True)

            path = QSettings("Char_DTP_tools", "Settings").value("path")

            structure = ToolsStructure(path).build_structure()
            other_scripts = structure.pop('other_scripts')

            for group, item_list in structure.items():

                group_name = re.sub(r'^_{1,2}', '', group)
                cmds.menuItem('fld' + group, label=group_name, tearOff=True, sm=True, p=menu)
                for item_path in item_list:
                    item_data = ToolDataAssembler(item_path).item_data
                    item_data['parent'] = 'fld' + group
                    cmds.menuItem(**item_data)
            for item_path in other_scripts:
                item_data = ToolDataAssembler(item_path).item_data
                item_data['parent'] = menu
                cmds.menuItem(**item_data)

            cmds.menuItem(divider=True, p=menu)
            cmds.menuItem("set path", l="Set path to scripts folder", p=menu, c=CharDepTools.set_path)

        except Exception as massage:
            om.MGlobal.displayError (massage)

    @staticmethod
    def shelf():
        """
        Creates a dedicated Maya shelf and fills it with tool buttons.
        """
        # ----------------------- remove old version if exists and create new one
        if cmds.shelfLayout(SHELF_NAME, exists=True):
            CharDepTools.delete_shelf(SHELF_NAME)

        cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")
        cmds.shelfTabLayout("ShelfLayout", edit=True, selectTab=SHELF_NAME)

        structure = ToolsStructure(os.path.dirname(__file__)).build_structure()
        other_scripts = structure.pop('other_scripts')

        for group, btn_list in structure.items():
            for btn_path in btn_list:
                cmds.shelfButton(**ToolDataAssembler(btn_path).button_data)
            cmds.separator(parent=SHELF_NAME, style="shelf", highlightColor=[0.321569, 0.521569, 0.65098], height=30)
        for btn_path in other_scripts:
            cmds.shelfButton(**ToolDataAssembler(btn_path).button_data)

    @staticmethod
    def script():
        """
        Adds a single shelf button for the current script directory.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_obj = ToolDataAssembler(script_dir)
        cmds.shelfButton(**data_obj.button_data)

    @staticmethod
    def delete_shelf(shelf_name):
        """
        Completely removes a Maya shelf and its configuration.
        """

        gShelfTopLevel = mel.eval('$tmp = $gShelfTopLevel')

        if not cmds.control(gShelfTopLevel, exists=True):
            return False

        shelves = cmds.tabLayout(gShelfTopLevel, q=True, ca=True) or []

        nShelves = cmds.shelfTabLayout(gShelfTopLevel, q=True, numberOfChildren=True)

        if shelf_name not in shelves:
            return False
        shelf_num = shelves.index(shelf_name)
        for i in range(shelf_num, nShelves):
            next_i = i + 1
            shelfLoad = cmds.optionVar(q="shelfLoad%d" % next_i) if cmds.optionVar(exists="shelfLoad%d" % next_i) else 0
            shelfName = cmds.optionVar(q="shelfName%d" % next_i)
            shelfFile = cmds.optionVar(q="shelfFile%d" % next_i)
            shelfAlign = cmds.optionVar(q="shelfAlign%d" % next_i) if cmds.optionVar(
                exists="shelfAlign%d" % next_i) else "left"
            cmds.optionVar(iv=("shelfLoad%d" % i, shelfLoad))
            cmds.optionVar(sv=("shelfName%d" % i, shelfName))
            cmds.optionVar(sv=("shelfFile%d" % i, shelfFile))
            cmds.optionVar(sv=("shelfAlign%d" % i, shelfAlign))
        cmds.optionVar(remove="shelfLoad%d" % nShelves)
        cmds.optionVar(remove="shelfName%d" % nShelves)
        cmds.optionVar(remove="shelfFile%d" % nShelves)
        cmds.optionVar(remove="shelfAlign%d" % nShelves)

        shelf_path = gShelfTopLevel + "|" + shelf_name
        if cmds.layout(shelf_path, exists=True):
            cmds.deleteUI(shelf_path, layout=True)

        shelf_dirs = mel.eval('internalVar -userShelfDir')
        path_separator = ";" if cmds.about(win=True) else ":"
        shelf_array = shelf_dirs.split(path_separator)

        for path in shelf_array:
            file_name = os.path.join(path, "shelf_%s.mel" % shelf_name)
            deleted_file = file_name + ".deleted"

            if os.path.exists(deleted_file):
                os.remove(deleted_file)

            if os.path.exists(file_name):
                os.rename(file_name, deleted_file)
                break

        mel.eval("shelfTabChange();")
        return True

    @staticmethod
    def set_path(*args):
        """
        Opens dialog to select tools root folder and stores it in QSettings.
        """
        path_in_settings = QSettings("Char_DTP_tools", "Settings").value("path")
        default_dir = str(path_in_settings) if os.path.isdir(path_in_settings) else QtCore.QDir.currentPath()

        lib_path = QtWidgets.QFileDialog.getExistingDirectory(None, "Select folder", default_dir)
        try:
            if lib_path and os.path.exists(lib_path) and os.path.isdir(lib_path):
                QSettings("Char_DTP_tools", "Settings").setValue("path", lib_path)
                CharDepTools.menu()
        except Exception as e:
            om.MGlobal.displayError(e)

    @staticmethod
    def add_command_to_user_setup():
        """
        Adds menu creation command into Maya userSetup.py
        so the menu loads automatically on Maya startup.
        """
        filename = os.path.join(maya_paths()['scripts_path'], "userSetup.py")

        command_lines = ["import maya.cmds as cmds",
                         "from launcher import CharDepTools",
                         "CharDepTools.menu()"]
        try:
            with open(filename, 'r') as f:
                lines = [l.rstrip('\n') for l in f.readlines()]
        except IOError:
            lines = []
        for command in command_lines:
            if command not in lines:
                with open(filename, 'a') as f:
                    f.write(command + '\n')

def maya_paths():
    """
    Detects Maya user directories for:
        - scripts
        - icons
    """
    paths = dict()
    maya_version = cmds.about(version=True)

    pattern_scripts = r'.+' + maya_version + '/prefs/scripts'
    paths['scripts_path'] = [x for x in os.environ['MAYA_SCRIPT_PATH'].split(';') if re.match(pattern_scripts, x)][0]

    pattern_icons = r'.+' + maya_version + '/prefs/icons'
    paths['icon_path'] = [x for x in os.environ['XBMLANGPATH'].split(';') if re.match(pattern_icons, x)][0]
    return paths


def onMayaDroppedPythonFile(obj):
    """
    Entry point triggered when this file is dragged into Maya viewport.

    Behavior depends on file name:
        - menu_installer.py   → installs menu
        - shelf_installer.py  → installs shelf
        - button_installer.py → installs single shelf button

    Also:
        - Copies launcher to Maya scripts folder
        - Adds startup command to userSetup.py
    """

    ScriptLauncher.copy_launcher()
    CharDepTools.add_command_to_user_setup()

    if os.path.basename(__file__) == 'menu_installer.py':
        # save tools path
        path = os.path.dirname(__file__)
        QSettings("Char_DTP_tools", "Settings").setValue("path", path)
        # add menu
        CharDepTools.menu()
        om.MGlobal.displayInfo('The ' + MENU_LABEL + ' menu installation was successful.')

    elif os.path.basename(__file__) == 'shelf_installer.py':
        CharDepTools.shelf()
        om.MGlobal.displayInfo('The ' + SHELF_NAME + ' shelf installation was successful.')

    elif os.path.basename(__file__) == 'button_installer.py':
        CharDepTools.script()
        dir_name = os.path.dirname(__file__)

        om.MGlobal.displayInfo('The ' + os.path.basename(dir_name) + ' installation was successful.')






