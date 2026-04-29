import re
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import maya.cmds as cmds
import maya.mel as mm
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya

ABOUT_SCRIPT = "\n" \
               "Latest updates:                          \n" \
               "                                         \n" \
               "12.10.2021   -add serch and replace      \n" \
               "08.02.2021   -add setting sever          \n" \
               "07.02.2021   -start refactoring          \n" \
               "                                         \n" \
               "Created by Andrey Belyaev                \n" \
               "andreikin@mail.ru"

HELP_TEXT = "\n" \
            "                Rename object script                                  .\n" \
            "- To rename object, enter the required name and click 'Rename'\n" \
            "- Selecting 'Rename hierarchy' button will rename all child objects.\n" \
            "- The button 'Select nonunique' will allow you to find objects in the \n" \
            "      scene that need to be renamed to prevent problems in the future."

PREFFIX_LIST = ['none', 'L_', 'R_', 'UP_', 'DW_', 'FV_', 'l_', 'r_']
SUFFIX_LIST = ['none', '_ctrl', '_jnt', '_grp', '_loc', '_geo', '_bind']
DEFAULT_DIGITS = "##"
DEFAULT_SETTINGS = [0, "", DEFAULT_DIGITS, 1]


class MyWindow(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setWindowTitle("Rename object")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        #self.setFixedSize(465, 300)

        # help and About script windows menu_bar
        menuBar = QMenuBar()
        self.setMenuBar(menuBar)
        menu = QMenu("Settings")
        menuBar.addMenu(menu)

        self.un_name_check_box = QAction("Use only unique names", self, checkable=True)
        self.un_name_check_box.setChecked(True)
        menu.addAction(self.un_name_check_box)
        def_settings = QAction("Reset settings", self)
        menu.addAction(def_settings)
        def_settings.triggered.connect(lambda: self.set_settings(*DEFAULT_SETTINGS))

        menu = QMenu("Help")
        menuBar.addMenu(menu)

        about_script_action = QAction("About script", self)
        menu.addAction(about_script_action)
        about_script_action.triggered.connect(lambda: self.text_dialog("About program"))
        help_action = QAction("Help", self)
        menu.addAction(help_action)
        help_action.triggered.connect(lambda: self.text_dialog("Help"))

        self.option_box = QGroupBox("Rename object:")
        self.raname_box_layout = QVBoxLayout(self.option_box)
        self.layout.addWidget(self.option_box)

        # Labels
        self.gridLayout = QGridLayout()
        self.label_pfx = QLabel(" Prefix:")
        self.gridLayout.addWidget(self.label_pfx, 0, 0, 1, 1)
        self.label_name = QLabel(" Name:")
        self.gridLayout.addWidget(self.label_name, 0, 1, 1, 1)
        self.label_digits = QLabel(" Digits:")
        self.gridLayout.addWidget(self.label_digits, 0, 2, 1, 1)
        self.label_sfx = QLabel(" Suffix:")
        self.gridLayout.addWidget(self.label_sfx, 0, 3, 1, 1)

        # comboBox_pfx, sfx, lineEdits
        self.comboBox_pfx = QComboBox()
        for pfx in PREFFIX_LIST:
            self.comboBox_pfx.addItem(pfx)
        self.gridLayout.addWidget(self.comboBox_pfx, 1, 0, 1, 1)
        self.lineEdit_name = QLineEdit()
        #self.lineEdit_name.setFixedWidth(207)
        self.lineEdit_name.setClearButtonEnabled(True)
        self.lineEdit_name.setPlaceholderText("Type name")
        self.gridLayout.addWidget(self.lineEdit_name, 1, 1, 1, 1)
        self.lineEdit_digit = QLineEdit()
        self.gridLayout.addWidget(self.lineEdit_digit, 1, 2, 1, 1)
        self.lineEdit_digit.setText(DEFAULT_DIGITS)
        self.comboBox_sfx = QComboBox()
        for sfx in SUFFIX_LIST:
            self.comboBox_sfx.addItem(sfx)
        self.gridLayout.addWidget(self.comboBox_sfx, 1, 3, 1, 1)
        self.raname_box_layout.addLayout(self.gridLayout)

        self.line1 = QFrame()  # line
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setFrameShadow(QFrame.Sunken)
        self.raname_box_layout.addWidget(self.line1)

        self.button_horizontalLayout = QHBoxLayout()  # buttons
        self.button_horizontalLayout.setSpacing(3)
        self.raname_box_layout.addLayout(self.button_horizontalLayout)
        self.button_nonunik = QPushButton('Select nonunique')
        self.button_horizontalLayout.addWidget(self.button_nonunik)
        self.button_nonunik.clicked.connect(self.select_nonunique)

        self.btn_fix_nonuniq = QPushButton('Fix nonunique')
        self.button_horizontalLayout.addWidget(self.btn_fix_nonuniq)
        self.btn_fix_nonuniq.clicked.connect(self.rename_nonunique)

        self.button__hierarhy = QPushButton("Rename hierarchy")
        self.button_horizontalLayout.addWidget(self.button__hierarhy)
        self.button__hierarhy.clicked.connect(lambda: self.rename(True))
        self.button_rename = QPushButton("Rename")
        self.button_horizontalLayout.addWidget(self.button_rename)
        self.button_rename.clicked.connect(lambda: self.rename(False))

        self.option_box2 = QGroupBox("Serch and replace:")
        self.raplace_box_layout = QVBoxLayout(self.option_box2)
        self.serchGridLayout = QGridLayout()

        self.comboBox_pfx_serch = QComboBox()
        for pfx in PREFFIX_LIST:
            self.comboBox_pfx_serch.addItem(pfx)
        self.serchGridLayout.addWidget(self.comboBox_pfx_serch, 1, 0, 1, 1)
        self.lineEdit_serch = QLineEdit()
        self.lineEdit_serch.setClearButtonEnabled(True)
        self.lineEdit_serch.setPlaceholderText("Type your own prefix")
        #self.lineEdit_serch.setFixedWidth(207)
        self.serchGridLayout.addWidget(self.lineEdit_serch, 1, 1, 1, 1)

        self.btn_add_pfx = QPushButton("Add pfx to selected")
        self.serchGridLayout.addWidget(self.btn_add_pfx, 1, 2, 1, 1)
        self.btn_add_pfx.clicked.connect(lambda: self.add_pfx("serch"))

        self.comboBox_pfx_replace = QComboBox()
        for pfx in PREFFIX_LIST:
            self.comboBox_pfx_replace.addItem(pfx)
        self.serchGridLayout.addWidget(self.comboBox_pfx_replace, 2, 0, 1, 1)
        self.lineEdit_replace = QLineEdit()
        self.lineEdit_replace.setClearButtonEnabled(True)
        self.lineEdit_replace.setPlaceholderText("Type your own prefix")
        #self.lineEdit_replace.setFixedWidth(207)
        self.serchGridLayout.addWidget(self.lineEdit_replace, 2, 1, 1, 1)

        self.btn_add_pfx2 = QPushButton("Add pfx to selected")
        #self.btn_add_pfx2.setFixedWidth(137)
        self.serchGridLayout.addWidget(self.btn_add_pfx2, 2, 2, 1, 1)
        self.btn_add_pfx2.clicked.connect(lambda: self.add_pfx(""))
        self.raplace_box_layout.addLayout(self.serchGridLayout)
        self.layout.addWidget(self.option_box2)

        self.line1 = QFrame()  # line 2
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setFrameShadow(QFrame.Sunken)
        self.raplace_box_layout.addWidget(self.line1)

        self.serch_button_HLayout = QHBoxLayout()  # buttons 2
        self.serch_button_HLayout.setSpacing(3)
        self.raplace_box_layout.addLayout(self.serch_button_HLayout)
        self.button_close = QPushButton('Close')
        self.serch_button_HLayout.addWidget(self.button_close)
        self.button_close.clicked.connect(self.close)
        self.btn_replace_hierarchy = QPushButton("Replace hierarchy")
        self.serch_button_HLayout.addWidget(self.btn_replace_hierarchy)
        self.btn_replace_hierarchy.clicked.connect(lambda: self.serch_and_replace(True))
        self.btn_replace = QPushButton("Replace")
        self.serch_button_HLayout.addWidget(self.btn_replace)
        self.btn_replace.clicked.connect(lambda: self.serch_and_replace(False))

        # load settings
        self.settings = QSettings("anRename", "Settings")
        self.load_settings()

        style_sheet = """ 
            QLineEdit { border-radius: 3 ; 
                /*height: 20px;*/
                background-color: rgb(40, 40, 40); 
                border:1px solid rgb(40, 40, 40);
                }
            
            QLineEdit:hover  { 
                border:1px solid rgb(118, 118, 118);
                }


            QGridLayout { margin: 0; }     
            QPushButton { 
                border-radius: 3px;
                border: 1px solid rgb(60, 60, 60);
                /*height: 20px;*/
                background-color: rgb(100, 100, 100); 
                border-style: outset;} 
            
            QPushButton:pressed { background-color: rgb(0, 0, 0); }

            QPushButton:hover { background-color: rgb(130, 130, 130);}
            
            QGroupBox { border-radius: 3 ;
                padding-top: 15 px;
                background-color: rgb(80, 80, 80); }
            QGroupBox::title {
                subcontrol-origin: margin;
                font-weight: bold;
                subcontrol-position: top left;  
                padding: 5 10px;
                }
            QComboBox {
                border-radius: 3px;
                width: 50px;
                /*height: 20px;*/
                background-color: rgb(40, 40, 40); }
                }
            """
        #self.setStyleSheet(style_sheet)

    def load_settings(self):
        """
        If settings not exist - load default settings
        """
        if self.settings.contains("renamer settings"):
            prefix, name, digs, suffix = self.settings.value("renamer settings")
        else:
            prefix, name, digs, suffix = DEFAULT_SETTINGS
        self.set_settings(prefix, name, digs, suffix)

    def set_settings(self, prefix, name, digs, suffix):
        self.comboBox_pfx.setCurrentIndex(int(prefix))
        self.lineEdit_name.setText(name)
        self.lineEdit_digit.setText(digs)
        self.comboBox_sfx.setCurrentIndex(int(suffix))
        self.comboBox_pfx_serch.setCurrentIndex(1)
        self.comboBox_pfx_replace.setCurrentIndex(2)

    def serch_and_replace(self, hierarhy):
        pfx_srch, pfx_rpls = self.__get_serch_and_replace_data()
        if hierarhy:
            mm.eval('searchReplaceNames "' + pfx_srch + '" "' + pfx_rpls + '" "hierarchy";')
        else:
            mm.eval('searchReplaceNames "' + pfx_srch + '" "' + pfx_rpls + '" "selected";')

    def add_pfx(self, pfx_part):  # pfx_part - serch or replace button (serch/replace)
        pfx_srch, pfx_rpls = self.__get_serch_and_replace_data()
        pfx = pfx_srch if pfx_part == "serch" else pfx_rpls

        sel = cmds.ls(sl=True)
        for obj in sel:
            cmds.rename(obj, pfx + obj)

    def closeEvent(self, evt):
        """
        When window closed it save fields settings
        """
        prefix = self.comboBox_pfx.currentIndex()
        name = self.lineEdit_name.text()
        digs = self.lineEdit_digit.text()
        suffix = self.comboBox_sfx.currentIndex()
        self.settings.setValue("renamer settings", [prefix, name, digs, suffix])

    def text_dialog(self, text_type):
        """
        Dialog window for help and about program
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        if text_type == "Help":
            help_dialog.setWindowTitle("Help window")
            help_dialog.setText(HELP_TEXT)
        else:
            help_dialog.setWindowTitle("About program")
            help_dialog.setText(ABOUT_SCRIPT)
        help_dialog.setStandardButtons(QMessageBox.Cancel)
        help_dialog.exec_()

    def rename(self, rename_hierarchy):
        prefix = self.__get_pfx_from_ui()
        new_name = self.__get_name_from_ui()
        digs = self.__get_digits_from_ui()
        suffix = self.__get_sfx_from_ui()
        sel = cmds.ls(selection=True)
        if not sel:
            raise ValueError('Must be selected at least one object.')
        else:
            node = cmds.createNode('unknown')
            cmds.addAttr(node, longName='selObjects', attributeType='message', multi=True, indexMatters=False)
            for each in sel:
                cmds.connectAttr('%s.message' % each, '%s.selObjects' % node, nextAvailable=True)
                if rename_hierarchy:
                    self.findChildren(each, node)
            con = cmds.listConnections('%s.selObjects' % node, source=True, destination=False)
            for i, obj in enumerate(con):
                num = i + 1
                objCurr = cmds.listConnections('%s.selObjects[%s]' % (node, i))[0]
                newDigs = (digs % num)

                if self.un_name_check_box.isChecked():
                    for j in range(1000):
                        result = prefix + new_name + newDigs + suffix
                        if cmds.objExists(result):
                            num += 1
                            newDigs = (digs % num)
                        else:
                            break
                else:
                    result = prefix + new_name + newDigs + suffix
                cmds.select(objCurr, replace=True)
                result = cmds.rename(result)
            cmds.delete(node)
            cmds.select(clear=True)

    def select_nonunique(self):
        def isNameUnique(name):
            shortName = name.split("|")
            try:
                longNames = cmds.ls(shortName[-1], l=True)
            except:
                longNames = cmds.ls(("*" + shortName[-1]), l=True)
            if len(longNames) > 1:
                return 0
            else:
                return 1

        rez = []
        for obj in cmds.ls():
            if not isNameUnique(obj):
                rez.append(obj)
        cmds.select(rez)

    def __get_pfx_from_ui(self):
        prefix = self.comboBox_pfx.currentText()
        if prefix == 'none':
            prefix = ''
        return prefix

    def __get_name_from_ui(self):
        return self.lineEdit_name.text()

    def __get_digits_from_ui(self):
        digits = self.lineEdit_digit.text()
        numDigits = digits.count('#')
        if numDigits == 0:
            raise ValueError("Count of # must be more then 0.")
        substr = '#' * numDigits
        zeroSubstr = '0' * numDigits
        newDig = digits.replace(substr, zeroSubstr)
        if newDig == digits:
            raise ValueError('Digits must contain only # symbols.')
        digs = digits.replace(substr, '%0' + str(numDigits) + 'd')
        return digs

    def __get_sfx_from_ui(self):
        suffix = self.comboBox_sfx.currentText()
        if suffix == 'none':
            suffix = ''
        return suffix

    def __get_serch_and_replace_data(self):
        pfx_srch = self.comboBox_pfx_serch.currentText()
        pfx_rpls = self.comboBox_pfx_replace.currentText()

        pfx_srch = "" if pfx_srch == 'none' else pfx_srch
        pfx_rpls = "" if pfx_rpls == 'none' else pfx_rpls

        pfx_srch += self.lineEdit_serch.text()
        pfx_rpls += self.lineEdit_replace.text()
        return pfx_srch, pfx_rpls

    def findChildren(self, parent, node):
        children = cmds.listRelatives(parent, children=True, fullPath=True)
        if children:
            for child in children:
                cmds.connectAttr('%s.message' % child, '%s.selObjects' % node, na=True)
                self.findChildren(child, node)

    def rename_nonunique(self, hashes='###'):
        sel = cmds.ls(sl=True)
        sel.sort(key=lambda x: len(x.split("|")), reverse=True)
        for obj in sel:
            new_name = self.unique_names_generator(obj, hashes)
            if not obj == new_name:
                cmds.rename(obj, new_name)

    @staticmethod
    def unique_names_generator(obj, hashes='###'):

        shot_name = obj.split("|")[-1]

        if len(cmds.ls(shot_name)) == 1:
            return shot_name
        else:
            if not len(cmds.ls(shot_name)) == 1:
                try:
                    num = re.findall('(\d+)', shot_name)[-1]  # get seurs namber string
                    txt = shot_name.split(num)[0]
                    txt = txt.replace(num, '')
                    sfx = shot_name.split(txt + num)[-1]
                except IndexError:
                    num = ""
                    if "_" in shot_name:
                        txt = shot_name.split("_")[0]
                        sfx = "_" + shot_name.split("_")[-1]
                    else:
                        txt = shot_name
                        sfx = ""
                for i in range(1000):
                    num_str = '{0:0' + str(len(hashes)) + 'd}'
                    str_new_num = num_str.format(i)
                    new_name = txt + str_new_num + sfx
                    if len(cmds.ls(new_name)) == 0:
                        return new_name
                        break


def rename_object():
    global win
    try:
        win.deleteLater()
    except:
        pass
    win = MyWindow()
    print ("----------------------------")
    win.show()


rename_object()
