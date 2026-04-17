import re
import maya.cmds as cmds
import maya.OpenMaya as om

PFX = {'L_': 'R_', 'l_': 'r_', 'left_': 'right_', 'Left_': 'Right_'}
PFX_PATTERN = '^(L_|R_|l_|r_|left_|right_|Left_|Right_)'
DIGIT_PATTERN = r'\d{1,}$'

def is_name_uique(name):
    return len(cmds.ls(name, l=True)) == 1

def unique_names_generator(in_name, name_index_padding=3):
    """
    Generates a unique name that is not in the scene
    """
    new_name = in_name
    num_str = '{0:0' + str(name_index_padding) + 'd}'
    pref, name, num, sfx = divide_name(in_name)
    num = int(num) if num else 0
    while not len(cmds.ls(new_name)) == 0:
        num += 1
        str_new_num = num_str.format(num)
        new_name = pref + name + str_new_num + sfx
    return new_name

def rename_shape(obj):
    """
    Renames all shapes controllers to unique names.
    """
    if not len(cmds.ls(obj)) == 1:
        om.MGlobal.displayError("There is either no object named {} in the scene or there is more than "
                                "one of them".format(obj))
        return
    pref, name, num, sfx = divide_name(obj)
    i=1
    for shape in cmds.listRelatives(obj, s=True, fullPath=True):
        shape_new_name = pref + name + num + 'Shape'
        while cmds.objExists(shape_new_name + '{0:03d}'.format(i)):
            i += 1
        cmds.rename(shape, shape_new_name + '{0:03d}'.format(i))


def fix_non_unique_name(function):
    """A decorator that accepts a `function` and enforces unique names in the passed list of objects.
    Arguments:
        function (function): The function to be executed with unique object names.
    """
    def wrapper(obj_list):

        obj_list = cmds.ls(obj_list, long=True)
        obj_list = sorted(obj_list, key=len, reverse=True)
        tmp_names = obj_list[:]

        for i in range(len(obj_list)):
            tmp_names[i] = unique_names_generator("jnt")
            cmds.rename(obj_list[i], tmp_names[i])

        return_value = function(tmp_names)

        for i in range(len(obj_list)):
            cmds.rename(tmp_names[i], obj_list[i].split('|')[-1])
        return return_value
    return wrapper


def suffix_minus(in_name):
    return "".join(divide_name(in_name)[:-1])

def divide_name(in_name):
    """
    Divides the object name into its component parts: prefix, name, number and suffix
    """
    pref, sfx, num, namespace = '', '', '', ''

    # get namespace
    if ':' in in_name:
        namespace = in_name.split(':')[:-1]
        namespace = ':'.join(namespace) + ':'
        in_name = in_name.split(':')[-1]

    # get prefix
    match = re.match(PFX_PATTERN, in_name)
    if match:
        pref = match.group()
        in_name = in_name.replace(pref, '')

    # get name and sfix
    in_name = in_name.split('_')
    if len(in_name) >= 2:
        name, sfx = '_'.join(in_name[:-1]), '_' + in_name[-1]
    else:
        name = in_name[0]

    # get digit
    digit_search = re.findall(DIGIT_PATTERN, name)
    if digit_search:
        num = digit_search[0]
        name = re.sub(DIGIT_PATTERN, '', name)

    if namespace:
        pref = namespace + pref

    return pref, name, num, sfx


def is_string_prefix(inp_string):
    return inp_string in list(PFX.keys()) + [PFX[x] for x in PFX]


def namespace_off(func):
    """
    decorator that disables namespaces for the function being decorated
    """
    def wrapper(*args, **kwargs):
        current = cmds.namespaceInfo(currentNamespace=True)
        if not current == u':':
            cmds.namespace(setNamespace=u':')
        return_value = func(*args, **kwargs)
        cmds.namespace(setNamespace=current)
        return return_value
    return wrapper

def get_namespaces_list():
    current_namespace = cmds.namespaceInfo(currentNamespace=True)
    cmds.namespace(setNamespace=':')
    namespaces_list = [''] + [x for x in cmds.namespaceInfo(lon=True) if x not in ['UI', 'shared']]
    cmds.namespace(setNamespace=current_namespace)
    return namespaces_list

if __name__ == '__main__':
    name1 = "NewNamespace1:testCT_CT"
    print (unique_names_generator(name1))
