
@staticmethod
def hotkey_command(tool_folder_path):

    python_code = 'from launcher import *;'

    python_code += 'ScriptLauncher().launch("' + tool_folder_path + '")'
    python_code_escaped = python_code.replace('\\', '\\\\').replace('"', '\\"')
    mel_command = 'python("' + python_code_escaped + '")'
    return mel_command

def hotkey_data(self):

    # if not self.hotkey or self.hotkey == {u'ctl': True, u'k': u'key_name', u'alt': True}:
    #     return None

    data = self.hotkey
    #data['name'] = self.labe l +'_hotkey'
    data['annotation'] = self.annotation
    data['command'] = "python('" + self.command(self.tool_folder_path) + ")'"
    # pprint (data)
    # --- Name Command ---

    # command_string = ToolDataAssembler.command(self.tool_folder_path)
    command_string = 'python("from launcher import *; ScriptLauncher().launch(r\'D:\\Projects\\Python\\char_dpt_tools\\Utilities\\script_template\')")'
    cmds.nameCommand(
        data['name'],
        annotation=data['annotation'],
        command=command_string
    )

    # --- Hotkey ---
    cmds.hotkey(
        keyShortcut=data['key'],
        ctrlModifier=data['ctl'],
        shiftModifier=data['shif'],
        altModifier=data['alt'],
        name=data['name']
    )

    return data
