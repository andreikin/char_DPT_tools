import json
import sys
sys.dont_write_bytecode = True

from contextlib import contextmanager
import os

import maya.cmds as cmds
import maya.mel as mel



INSTALLER_VERSION = '1.0.0'
MENU = 'script_manager_menu'
MENU_LABEL = 'Char_DPT_tools'
SHELF_NAME = "Char_DPT_shelf"


class ScriptLauncher2:

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
                module_path = module_folder

            py_path = os.path.join(tool_folder_path, 'script.py')
            mel_path = os.path.join(tool_folder_path, 'script.mel')

            self.increment_script_counter(os.path.basename(tool_folder_path))

            if os.path.exists(py_path):
                self.run_python(py_path, module_path)
                return
            elif os.path.exists(mel_path):
                self.run_mel(mel_path)

        except Exception as message:
            cmds.error(message)

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
            cmds.error(message)

if __name__ == '__main__':
    print ('========================================')

    path = r"D:\Projects\Python\char_dpt_tools\Char_DPT_tools\__skinning\skin_manager"

    from launcher import *
    ScriptLauncher().launch(path)