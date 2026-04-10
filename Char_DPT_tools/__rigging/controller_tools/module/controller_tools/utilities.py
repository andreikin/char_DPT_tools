
import re
import maya.cmds as cmds
import maya.OpenMaya as om

PFX = {'L_': 'R_', 'l_': 'r_', 'left_': 'right_', 'Left_': 'Right_'}
PFX_PATTERN = '^(L_|R_|l_|r_|left_|right_|Left_|Right_)'
DIGIT_PATTERN = r'\d{1,}$'

def rename_shape(obj):
    """
    Renames all shapes controllers to unique names.
    """
    if not len(cmds.ls(obj)) == 1:
        om.MGlobal.displayError("There is either no object named" + obj + "in the scene or there is more than  one of "
                                                                          "them")
        return
    pref, name, num, sfx = divide_name(obj)
    i=1
    for shape in cmds.listRelatives(obj, s=True, fullPath=True):
        shape_new_name = pref + name + num + 'Shape'
        while cmds.objExists(shape_new_name + '{0:03d}'.format(i)):
            i += 1
        cmds.rename(shape, shape_new_name + '{0:03d}'.format(i))


def divide_name(in_name):
    """
    Divides the object name into its component parts: prefix, name, number and suffix
    """
    pref, sfx, num, namespace = '', '', '', ''
    # _______________ get namespace
    if ':' in in_name:
        namespace = in_name.split(':')[:-1]
        namespace = ':'.join(namespace) + ':'
        in_name = in_name.split(':')[-1]
    # _______________ get prefix
    match = re.match(PFX_PATTERN, in_name)
    if match:
        pref = match.group()
        in_name = in_name.replace(pref, '')
    # _______________ get name and sfix
    in_name = in_name.split('_')
    if len(in_name) >= 2:
        name, sfx = '_'.join(in_name[:-1]), '_' + in_name[-1]
    else:
        name = in_name[0]
    # _______________ get digit
    digit_search = re.findall(DIGIT_PATTERN, name)
    if digit_search:
        num = digit_search[0]
        name = re.sub(DIGIT_PATTERN, '', name)
    if namespace:
        pref = namespace + pref

    return pref, name, num, sfx


def suffix_minus(in_name):
    return "".join(divide_name(in_name)[:-1])


def namespace_off(func):
    """
    decorator that disables namespaces for the function being decorated
    """
    def wrapper(*args, **kwargs):
        current = cmds.namespaceInfo( currentNamespace=True )
        if not current == u':':
            cmds.namespace(setNamespace=u':')
        return_value = func(*args, **kwargs)
        cmds.namespace(setNamespace=current)
        return return_value
    return wrapper


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