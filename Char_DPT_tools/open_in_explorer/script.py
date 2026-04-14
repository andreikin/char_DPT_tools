import maya, subprocess, os
import maya.OpenMaya as om


def open_scene_in_explorer():
    path = os.path.dirname(maya.cmds.file(q=True, sn=True))
    if path:
        subprocess.Popen('explorer \"%s\"' % os.path.abspath(path))
    else:
        om.MGlobal.displayError('Scene has not been saved and therefore cannot be opened in Explorer!')

open_scene_in_explorer()

