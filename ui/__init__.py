# gui
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# pose manager
from .. import api as pm_api
from .. import io as pm_io

# maya
from maya import cmds as mc


class DriverWidget(QtWidgets.QWidget):
    """
┌──────────────────────────────┐
│  ┌─list widget────────────┐  │
│  │                        │  │
│  │                        │  │
│  │ * driver1 | controller │  │
│  │ driver2 | controller   │  │
│  │                        │  │
│  │                        │  │
│  │                        │  │
│  │                        │  │
│  │                        │  │
│  │                        │  │
│  │                        │  │
│  └────────────────────────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐  │
│  │add   │ │mirror│ │delete│  │
│  │driver│ │driver│ │driver│  │
│  └──────┘ └──────┘ └──────┘  │
└──────────────────────────────┘

    driver list widget - item double click - current driver change

    add driver btn - add driver
    mirror driver btn - mirror driver
    delete driver btn - delete driver
    """

    changedCurrentDriver = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.initialize_ui()
        self.refresh_ui()

    def initialize_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)
        self.list_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.list_widget.itemDoubleClicked.connect(self.change_driver)
        layout.addWidget(self.list_widget)

        btn_layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(btn_layout)

        self.add_driver_btn = QtWidgets.QPushButton("Add Driver")
        self.add_driver_btn.clicked.connect(self.add_driver)
        self.mirror_driver_btn = QtWidgets.QPushButton("Mirror Driver")
        self.mirror_driver_btn.clicked.connect(self.mirror_driver)
        self.delete_driver_btn = QtWidgets.QPushButton("Delete Driver")
        self.delete_driver_btn.clicked.connect(self.delete_driver)

        btn_layout.addWidget(self.add_driver_btn)
        btn_layout.addWidget(self.mirror_driver_btn)
        btn_layout.addWidget(self.delete_driver_btn)

    def refresh_ui(self):
        self.list_widget.clear()

        if not mc.objExists("pose_manager"):
            return

        data = pm_api.get_data()

        for k in data.keys():
            driver = k.replace("_pmInterpolator", "")
            controller = data[k]["controller"]
            item = QtWidgets.QListWidgetItem()
            item.setText(driver + " | " + controller)

            self.list_widget.addItem(item)

    def add_driver(self):
        selected = mc.ls(selection=True)
        if len(selected) != 2:
            mc.warning("you need select driver and controller")
            return
        pm_api.add_driver(selected[0], selected[1])
        self.refresh_ui()

    def mirror_driver(self):
        items = self.list_widget.selectedItems()
        for item in items:
            pm_api.mirror_driver(item.text().split(" | ")[0])
        if items:
            self.refresh_ui()

    def delete_driver(self):
        items = self.list_widget.selectedItems()
        for item in items:
            pm_api.delete_driver(item.text().split(" | ")[0])
        if items:
            self.refresh_ui()
            self.changedCurrentDriver.emit("")

    def change_driver(self, item):
        self.changedCurrentDriver.emit(item.text().split(" | ")[0])


class PoseDrivenWidget(QtWidgets.QWidget):
    """
  ┌────┐
┌─┤pose│| driven1 | driven2 | ... | ◄ ► ─┐
│ └────┘                                 │
│                  ┌───────────────────┐ │
│  Current Driver :│                   │ │
│                  └───────────────────┘ │
│                                        │
│ ┌──────┬────┬────┬────┬────┬────┬────┐ │
│ │ pose │ tx │ ty │ tz │ rx │ ry │ rz │ │
│ │ name │    │    │    │    │    │    │ │
│ ├──────┼────┼────┼────┼────┼────┼────┤ │
│ │ pose │ 0  │ 0  │ 0  │ 0  │ 0  │ 0  │ │
│ │  #1  │    │    │    │    │    │    │ │
│ ├──────┼────┼────┼────┼────┼────┼────┤ │
│ │ pose │ 0  │ 0  │ 0  │ 90 │ 0  │ 0  │ │
│ │  #2  │    │    │    │    │    │    │ │
│ ├──────┼────┼────┼────┼────┼────┼────┤ │
│ │ pose │ 0  │ 0  │ 0  │ 0  │ 90 │ 0  │ │
│ │  #3  │    │    │    │    │    │    │ │
│ └──────┴────┴────┴────┴────┴────┴────┘ │
│                                        │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │add       │ │update    │ │delete    │ │
│ │pose      │ │pose      │ │pose      │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│                                        │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │add       │ │update    │ │delete    │ │
│ │driven    │ │driven    │ │driven    │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│                                        │
└────────────────────────────────────────┘
    """

    current_driver = None

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.initialize_ui()
        self.refresh_ui()

    def initialize_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        label_layout = QtWidgets.QHBoxLayout(self)
        label = QtWidgets.QLabel("Current Driver")
        self.driver_line_edit = QtWidgets.QLineEdit()
        self.driver_line_edit.setReadOnly(True)
        self.driver_line_edit.setAlignment(QtCore.Qt.AlignRight)
        self.controller_line_edit = QtWidgets.QLineEdit()
        self.controller_line_edit.setReadOnly(True)
        self.controller_line_edit.setAlignment(QtCore.Qt.AlignRight)
        label_layout.addWidget(label)
        label_layout.addWidget(self.driver_line_edit)
        label_layout.addWidget(self.controller_line_edit)
        layout.addLayout(label_layout)
        self.driver_line_edit.mousePressEvent = self.select_driver
        self.controller_line_edit.mousePressEvent = self.select_controller

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.tabBarDoubleClicked.connect(self.select_driven)
        layout.addWidget(self.tab_widget)

        btn_layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(btn_layout)

        self.add_pose_btn = QtWidgets.QPushButton("Add Pose")
        self.add_pose_btn.clicked.connect(self.add_pose)
        self.update_pose_btn = QtWidgets.QPushButton("Update Pose")
        self.update_pose_btn.clicked.connect(self.update_pose)
        self.delete_pose_btn = QtWidgets.QPushButton("Delete Pose")
        self.delete_pose_btn.clicked.connect(self.delete_pose)
        btn_layout.addWidget(self.add_pose_btn)
        btn_layout.addWidget(self.update_pose_btn)
        btn_layout.addWidget(self.delete_pose_btn)

        btn_layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(btn_layout)

        self.add_driven_btn = QtWidgets.QPushButton("Add Driven")
        self.add_driven_btn.clicked.connect(self.add_driven)
        self.update_driven_btn = QtWidgets.QPushButton("Update Driven")
        self.update_driven_btn.clicked.connect(self.update_driven)
        self.delete_driven_btn = QtWidgets.QPushButton("Delete Driven")
        self.delete_driven_btn.clicked.connect(self.delete_driven)
        btn_layout.addWidget(self.add_driven_btn)
        btn_layout.addWidget(self.update_driven_btn)
        btn_layout.addWidget(self.delete_driven_btn)

    def refresh_ui(self, current_driver=""):
        # DriverWidget 의 current_driver 변수를 저장합니다.
        self.current_driver = current_driver
        if self.current_driver == "":
            self.tab_widget.clear()
            return

        current_index = self.tab_widget.currentIndex()
        current_tab_name = ""
        if current_index >= 0:
            current_tab_name = self.tab_widget.tabText(current_index)

        self.tab_widget.clear()

        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.table_widget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["tx", "ty", "tz", "rx", "ry", "rz"])
        self.table_widget.itemDoubleClicked.connect(self.go_to_pose)
        self.tab_widget.addTab(self.table_widget, "pose")

        if not mc.objExists("pose_manager"):
            return

        data = pm_api.get_data()

        interpolator_name = self.current_driver + "_pmInterpolator"
        row_labels = data[interpolator_name]["pose"].keys()

        for i, pose in enumerate(row_labels):
            tr = data[interpolator_name]["pose"][pose]["t"] + data[interpolator_name]["pose"][pose]["r"]
            self.table_widget.insertRow(i)
            for _i, v in enumerate(tr):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.DisplayRole, v)
                self.table_widget.setItem(i, _i, item)
        self.table_widget.setVerticalHeaderLabels(row_labels)

        self.driven_table_widgets = []
        for blend_m in data[interpolator_name]["driven"]:
            driven = blend_m.replace("_bm", "")

            table_widget = QtWidgets.QTableWidget(self)
            table_widget.itemDoubleClicked.connect(self.go_to_pose)
            table_widget.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
            table_widget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            table_widget.setColumnCount(6)
            table_widget.setHorizontalHeaderLabels(["tx", "ty", "tz", "rx", "ry", "rz"])

            for i, pose in enumerate(data[interpolator_name]["pose"].keys()):
                t = data[interpolator_name]["pose"][pose]["driven"][driven]["t"]
                r = data[interpolator_name]["pose"][pose]["driven"][driven]["r"]
                table_widget.insertRow(i)
                for _i, v in enumerate(t + r):
                    item = QtWidgets.QTableWidgetItem()
                    item.setData(QtCore.Qt.DisplayRole, v)
                    table_widget.setItem(i, _i, item)

            table_widget.setVerticalHeaderLabels(row_labels)
            self.tab_widget.addTab(table_widget, driven)
            self.driven_table_widgets.append(table_widget)

        self.driver_line_edit.setText(self.current_driver)
        self.controller_line_edit.setText(data[interpolator_name]["controller"])

        if current_tab_name:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == current_tab_name:
                    self.tab_widget.setCurrentIndex(i)

    def add_pose(self):
        if self.current_driver is None:
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Pose Name Dialog")
        input_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Pose Name 을 입력하세요.")
        line_edit = QtWidgets.QLineEdit()
        input_layout.addWidget(label)
        input_layout.addWidget(line_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("Ok", dialog)
        ok_btn.setDefault(True)
        cancel_btn = QtWidgets.QPushButton("Cancel", dialog)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout = QtWidgets.QVBoxLayout(dialog)
        dialog.setLayout(layout)
        layout.addLayout(input_layout)
        layout.addLayout(btn_layout)

        if not dialog.exec_():
            return
        pose_name = line_edit.text()
        if pose_name:
            pm_api.add_pose(self.current_driver, pose_name)
            self.refresh_ui(self.current_driver)

    def update_pose(self):
        if self.current_driver is None:
            return
        widget = self.tab_widget.currentWidget()
        row = widget.currentRow()
        pose = widget.verticalHeaderItem(row).text()
        pm_api.update_pose(self.current_driver, pose)
        self.refresh_ui(self.current_driver)

    def delete_pose(self):
        if self.current_driver is None:
            return
        widget = self.tab_widget.currentWidget()
        row = widget.currentRow()
        pose = widget.verticalHeaderItem(row).text()
        pm_api.delete_pose(self.current_driver, pose)
        self.refresh_ui(self.current_driver)

    def add_driven(self):
        if self.current_driver is None:
            return
        selected = mc.ls(selection=True)
        if selected:
            for sel in selected:
                pm_api.add_driven(self.current_driver, sel)
            self.refresh_ui(self.current_driver)

    def update_driven(self):
        if self.current_driver is None:
            return
        current_index = self.tab_widget.currentIndex()
        current_tab_name = ""
        if current_index >= 0:
            current_tab_name = self.tab_widget.tabText(current_index)

        if not current_tab_name:
            mc.warning("Driven tab 을 선택해 주세요.")
            return

        widget = self.tab_widget.currentWidget()
        row = widget.currentRow()
        if row == -1:
            mc.warning("Pose 를 선택해 주세요.")
            return
        pose = widget.verticalHeaderItem(row).text()

        pm_api.update_driven(self.current_driver, pose, current_tab_name)
        self.refresh_ui(self.current_driver)

    def delete_driven(self):
        current_index = self.tab_widget.currentIndex()
        current_tab_name = ""
        if current_index >= 0:
            current_tab_name = self.tab_widget.tabText(current_index)
        if current_tab_name:
            pm_api.delete_driven(self.current_driver, current_tab_name)
            self.refresh_ui(self.current_driver)

    def go_to_pose(self, index):
        widget = self.tab_widget.currentWidget()
        pm_api.go_to_pose(self.current_driver, widget.verticalHeaderItem(index.row()).text())

    def select_driver(self, e):
        driver = self.driver_line_edit.text()
        if mc.objExists(driver):
            mc.select(driver)

    def select_controller(self, e):
        controller = self.controller_line_edit.text()
        if mc.objExists(controller):
            mc.select(controller)

    def select_driven(self, i):
        if i != 0:
            driven = self.tab_widget.tabText(i)
            if mc.objExists(driven):
                mc.select(driven)


class PoseManagerUI(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    """
┌──────────────────────┐ ┌──file──┐
│ File |               │ │  save  │
├──────────────────────┤ ├────────┤
│                      │ │  load  │
│ ┌──DriverWidget────┐ │ └────────┘
│ │                  │ │
│ │                  │ │
│ └──────────────────┘ │
│                      │
│ ┌─PoseDrivenWidget─┐ │
│ │                  │ │
│ │                  │ │
│ └──────────────────┘ │
│                      │
└──────────────────────┘
    """

    # use dockable in __init.py
    tool_name = "PoseManagerUI"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Pose Manager")
        self.setObjectName(self.tool_name)

        self.setCentralWidget(self.initialize_ui())

    def initialize_ui(self):
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)
        widget.setLayout(layout)

        self.driver_widget = DriverWidget(widget)
        layout.addWidget(self.driver_widget)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        self.pose_driven_widget = PoseDrivenWidget(widget)
        layout.addWidget(self.pose_driven_widget)

        self.driver_widget.changedCurrentDriver.connect(self.pose_driven_widget.refresh_ui)

        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        save_action = QtWidgets.QAction(QtGui.QIcon(":save.png"), "Save", self)
        load_action = QtWidgets.QAction(QtGui.QIcon(":openLoadGeneric.png"), "Load", self)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        save_action.triggered.connect(self.save)
        load_action.triggered.connect(self.load)

        return widget

    def save(self):
        root_dir = mc.workspace(query=True, rootDirectory=True)
        file_path = mc.fileDialog2(caption="Save Pose",
                                   startingDirectory=root_dir,
                                   fileFilter="Pose (*.pose)",
                                   fileMode=0)
        if file_path:
            file_path = file_path[0]
        else:
            return None
        data = pm_api.get_data()
        if data:
            print("Save Pose : {0}".format(file_path))
            pm_io.dump(file_path=file_path, data=data)
        else:
            print("Empty data")

    def load(self):
        root_dir = mc.workspace(query=True, rootDirectory=True)
        file_path = mc.fileDialog2(caption="Load Pose",
                                   startingDirectory=root_dir,
                                   fileFilter="Pose (*.pose)",
                                   fileMode=1)
        if file_path:
            file_path = file_path[0]
        else:
            return None
        pm_io.load(file_path=file_path)
        self.driver_widget.refresh_ui()
        self.pose_driven_widget.refresh_ui()

