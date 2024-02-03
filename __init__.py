# gui
from PySide2 import QtWidgets

# pose manager
from .ui import PoseManagerUI

# bulit-ins
import sys

# maya
from maya import cmds as mc

self = sys.modules[__name__]
self._window = None


def show():
    app = QtWidgets.QApplication.instance()
    maya_window = next(w for w in app.topLevelWidgets() if w.objectName() == "MayaWindow")
    try:
        for c in maya_window.children():
            if isinstance(c, PoseManagerUI):
                c.deleteLater()
    except Exception:
        pass

    self._window = PoseManagerUI()
    control = PoseManagerUI.tool_name + "WorkspaceControl"
    if mc.workspaceControl(control, query=True, exists=True):
        mc.workspaceControl(control, edit=True, close=True)
        mc.deleteUI(control, control=True)
    self._window.show(dockable=True)
    return self._window
